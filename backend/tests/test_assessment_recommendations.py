"""Focused recommendation boundaries; no database connection or personal data."""
import os
import unittest
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://test:test@localhost/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("SECRET_KEY", "assessment-unit-tests")

from fastapi import HTTPException
from backend.app.assessments import recommendations as rec, router
from backend.app.auth.dependencies import get_current_user


class RecommendationTests(unittest.TestCase):
    def setUp(self):
        self.db = Mock()
        self.user_id = uuid.uuid4()
        self.career = NS(id=uuid.uuid4(), title="Synthetic occupation", onet_soc_code="00-0000.01")
        self.python = NS(id=uuid.uuid4(), canonical_name="Python")
        self.sql = NS(id=uuid.uuid4(), canonical_name="SQL")
        self.rows = [(NS(id=uuid.uuid4(), title=f"{s.canonical_name} sample", description=None,
                         difficulty="BEGINNER", version=1), s) for s in (self.python, self.sql)]
        self.db.execute.return_value.all.return_value = self.rows

    def requirement(self, name):
        return NS(id=uuid.uuid4(), workplace_example=name, in_demand=True,
                  hot_technology=False, onet_version="31.0")

    def recommend(self, names):
        self.db.scalars.return_value.all.return_value = [self.requirement(n) for n in names]
        with patch.object(rec, "get_measured_skill_ids", return_value=set()):
            return rec.get_technology_recommendations(self.db, self.user_id, self.career)

    def test_exact_aliases_change_recommendations_with_occupation_input(self):
        self.assertEqual([r["skill_name"] for r in self.recommend([" Python "])], ["Python"])
        self.assertEqual([r["skill_name"] for r in self.recommend(["Structured query language SQL"])], ["SQL"])
        self.assertEqual(self.recommend(["NoSQL", "Microsoft SQL Server", "Python tools", "MySQL"]), [])

    def test_software_signal_is_not_a_competency_and_is_deduplicated(self):
        rows = self.recommend(["SQL", "Structured query language SQL"])
        self.assertEqual(len(rows), 1)
        self.assertIsNone(rows[0]["competency"])
        self.assertEqual(rows[0]["recommendation_type"], "SOFTWARE_SIGNAL")
        statement = str(self.db.scalars.call_args.args[0])
        self.assertIn("career_software_requirements.in_demand IS true", statement)
        self.assertIn("career_software_requirements.career_id =", statement)
        self.assertIn("assessments.is_active IS true", str(self.db.execute.call_args.args[0]))

    def test_measured_python_suppresses_only_python_even_at_zero_score(self):
        snapshot = NS(state_data={"skills": [
            {"skill_id": str(self.python.id), "name": "Python", "evidence": [
                {"source_type": "ASSESSMENT", "evidence_status": "ASSESSED", "evidence_strength": 0,
                 "observed_at": datetime.now(timezone.utc).isoformat()}]},
            {"skill_id": str(self.sql.id), "name": "SQL", "evidence": [
                {"source_type": "RESUME", "evidence_status": "DETECTED", "evidence_strength": 1}]},
        ]})
        self.db.scalars.return_value.all.return_value = [self.requirement("Python"), self.requirement("SQL")]
        with patch.object(rec, "get_career_twin", return_value=NS(id=uuid.uuid4())), \
             patch.object(rec, "get_latest_snapshot", return_value=snapshot):
            result = rec.get_technology_recommendations(self.db, self.user_id, self.career)
        self.assertEqual([row["skill_name"] for row in result], ["SQL"])

    def test_me_uses_authenticated_owner_and_mapped_primary_goal(self):
        goal = NS(id=uuid.uuid4(), onet_soc_code=self.career.onet_soc_code)
        self.db.scalar.return_value = self.career
        with patch.object(rec, "get_user_primary_career_goal", return_value=goal) as lookup, \
             patch.object(rec, "get_career_assessment_recommendations", return_value={}) as recommend:
            result = router.get_my_recommended_assessments(self.db, NS(id=self.user_id))
        lookup.assert_called_once_with(db=self.db, user_id=self.user_id)
        recommend.assert_called_once_with(self.db, self.user_id, self.career.id)
        self.assertEqual(result["career_goal_id"], goal.id)
        route = next(r for r in router.router.routes if r.path.endswith("/recommendations/me"))
        self.assertIn(get_current_user, [d.call for d in route.dependant.dependencies])

    def test_missing_unmapped_and_unknown_goals_have_explicit_empty_state(self):
        for goal in (None, NS(onet_soc_code=None), NS(onet_soc_code="00-0000.00")):
            self.db.scalar.return_value = None
            with patch.object(rec, "get_user_primary_career_goal", return_value=goal):
                with self.assertRaises(HTTPException) as error:
                    rec.get_my_assessment_recommendations(self.db, self.user_id)
                self.assertEqual(error.exception.status_code, 404)

    def test_broad_competency_mapping_cannot_recommend_python_or_sql(self):
        mapping = NS(onet_element_id="programming")
        self.db.execute.return_value.all.return_value = [(a, s, mapping) for a, s in self.rows]
        with patch.object(rec, "get_career_or_404", return_value=self.career), \
             patch.object(rec, "get_career_competencies", return_value={"programming": {"importance": 5}}), \
             patch.object(rec, "get_measured_competency_ids", return_value=set()), \
             patch.object(rec, "get_technology_recommendations", return_value=[]):
            result = rec.get_career_assessment_recommendations(self.db, self.user_id, self.career.id)
        self.assertEqual(result["recommended_count"], 0)


if __name__ == "__main__":
    unittest.main()
