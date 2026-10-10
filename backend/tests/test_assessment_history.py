"""Run from the repository root with python -m unittest discover -s backend/tests."""

import os
import unittest
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock, patch

# No database connection is made by these tests.
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://test:test@localhost/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("SECRET_KEY", "assessment-history-unit-test-only")

from fastapi import HTTPException
from sqlalchemy import and_
from sqlalchemy.dialects import postgresql

from backend.app.assessments import router, service
from backend.app.assessments.models import AssessmentAttempt
from backend.app.auth.dependencies import get_current_user


class AssessmentHistoryTests(unittest.TestCase):
    def setUp(self):
        self.user_id = uuid.uuid4()
        self.now = datetime(2026, 10, 10, 12, tzinfo=timezone.utc)
        self.skill = SimpleNamespace(id=uuid.uuid4(), canonical_name="Python")
        self.assessment = SimpleNamespace(
            id=uuid.uuid4(), skill_id=self.skill.id, skill=self.skill,
            title="Python fundamentals", version=3, is_active=False,
            description="Core knowledge", difficulty="BEGINNER",
        )
        self.attempt = SimpleNamespace(
            id=uuid.uuid4(), user_id=self.user_id,
            assessment_id=self.assessment.id, assessment=self.assessment,
            status="COMPLETED", raw_score=2, total_questions=3,
            percentage=66.67, started_at=self.now, completed_at=self.now,
        )
        self.db = Mock()

    def test_detail_query_requires_both_owner_and_attempt(self):
        self.db.scalar.return_value = self.attempt
        actual = service.get_user_attempt_or_404(
            self.db, self.user_id, self.attempt.id
        )
        self.assertIs(actual, self.attempt)
        statement = self.db.scalar.call_args.args[0]
        self.assertTrue(statement.whereclause.compare(and_(
            AssessmentAttempt.id == self.attempt.id,
            AssessmentAttempt.user_id == self.user_id,
        )))

    def test_foreign_and_missing_attempts_have_same_404(self):
        self.db.scalar.return_value = None
        for attempt_id in (self.attempt.id, uuid.uuid4()):
            with self.subTest(attempt_id=attempt_id):
                with self.assertRaises(HTTPException) as caught:
                    router.get_assessment_attempt(
                        attempt_id, self.db, SimpleNamespace(id=uuid.uuid4())
                    )
                self.assertEqual(caught.exception.status_code, 404)
                self.assertEqual(caught.exception.detail, "Assessment attempt not found.")
        self.db.scalars.assert_not_called()

    def test_history_is_owner_scoped_bounded_and_newest_first(self):
        self.db.scalars.return_value.all.return_value = [self.attempt]
        actual = service.get_user_attempts(self.db, self.user_id, 10, 20)
        self.assertEqual(actual, [self.attempt])
        statement = self.db.scalars.call_args.args[0]
        self.assertTrue(statement.whereclause.compare(
            AssessmentAttempt.user_id == self.user_id
        ))
        compiled = statement.compile(dialect=postgresql.dialect())
        self.assertIn("assessment_attempts.started_at DESC", str(compiled))
        self.assertIn(10, compiled.params.values())
        self.assertIn(20, compiled.params.values())

    def test_result_uses_persisted_scores_and_inactive_version_provenance(self):
        question = SimpleNamespace(
            id=uuid.uuid4(), correct_option="B", explanation="Because B."
        )
        self.db.scalars.return_value.all.return_value = [SimpleNamespace(
            question=question, selected_option="A", is_correct=False,
        )]
        result = service.serialize_attempt_result(self.db, self.attempt)
        self.assertEqual(result.raw_score, 2)  # Do not re-score from loaded answers.
        self.assertEqual(result.percentage, 66.67)
        self.assertEqual(result.assessment_title, self.assessment.title)
        self.assertEqual(result.assessment_version, 3)
        self.assertEqual(result.skill_id, self.skill.id)
        self.assertEqual(result.skill_name, "Python")
        self.assertEqual(result.started_at, self.now)
        self.assertEqual(result.completed_at, self.now)
        self.assertEqual(result.answers[0].correct_option, "B")
        self.assertFalse(result.answers[0].is_correct)
        self.assertEqual(result.answers[0].explanation, "Because B.")
        self.assertEqual(result.model_dump(mode="json")["attempt_id"], str(self.attempt.id))
        self.db.commit.assert_not_called()

    def test_in_progress_attempt_preserves_nulls_without_answer_key(self):
        self.attempt.status = "IN_PROGRESS"
        self.attempt.raw_score = self.attempt.percentage = None
        self.attempt.completed_at = None
        result = service.serialize_attempt_result(self.db, self.attempt)
        self.assertIsNone(result.raw_score)
        self.assertIsNone(result.completed_at)
        self.assertEqual(result.answers, [])
        self.db.scalars.assert_not_called()

    def test_submit_and_detail_share_result_serialization(self):
        self.db.scalars.return_value.all.return_value = []
        self.db.scalar.return_value = self.attempt
        user = SimpleNamespace(id=self.user_id)
        with patch.object(router, "submit_assessment", return_value=self.attempt):
            submitted = router.submit_technical_assessment(
                self.assessment.id, Mock(), self.db, user
            )
        fetched = router.get_assessment_attempt(self.attempt.id, self.db, user)
        self.assertEqual(submitted.model_dump(), fetched.model_dump())

    def test_catalog_metadata_scopes_owner_before_ranking(self):
        self.db.execute.return_value.all.return_value = [(self.assessment.id, 3)]
        self.db.scalars.return_value.all.return_value = [self.attempt]
        counts, latest = service.get_catalog_metadata(
            self.db, self.user_id, [self.assessment.id]
        )
        self.assertEqual(counts, {self.assessment.id: 3})
        self.assertEqual(latest, {self.assessment.id: self.attempt})
        compiled = self.db.scalars.call_args.args[0].compile(dialect=postgresql.dialect())
        sql = str(compiled)
        self.assertIn("PARTITION BY assessment_attempts.assessment_id", sql)
        self.assertIn("WHERE assessment_attempts.user_id =", sql)
        self.assertIn(self.user_id, compiled.params.values())
        self.assertIn("anon_1.rank =", sql)

    def test_catalog_exposes_counts_latest_attempt_and_empty_states(self):
        user = SimpleNamespace(id=self.user_id)
        with patch.object(router, "get_active_assessments", return_value=[self.assessment]), patch.object(
            router, "get_catalog_metadata", return_value=(
                {self.assessment.id: 3}, {self.assessment.id: self.attempt}
            )
        ) as metadata:
            catalog = router.list_assessments(self.db, user)
            metadata.assert_called_once_with(self.db, self.user_id, [self.assessment.id])
        self.assertEqual(catalog[0].question_count, 3)
        self.assertEqual(catalog[0].latest_attempt.attempt_id, self.attempt.id)
        with patch.object(router, "get_active_assessments", return_value=[self.assessment]), patch.object(
            router, "get_catalog_metadata", return_value=({}, {})
        ):
            catalog = router.list_assessments(self.db, user)
        self.assertEqual(catalog[0].question_count, 0)
        self.assertIsNone(catalog[0].latest_attempt)
        self.assertEqual(service.get_catalog_metadata(self.db, self.user_id, []), ({}, {}))

    def test_history_routes_are_authenticated_and_precede_uuid_route(self):
        routes = {route.path: route for route in router.router.routes}
        paths = list(routes)
        for path in ("/api/v1/assessments/attempts", "/api/v1/assessments/attempts/{attempt_id}"):
            self.assertLess(paths.index(path), paths.index("/api/v1/assessments/{assessment_id}"))
            dependencies = [item.call for item in routes[path].dependant.dependencies]
            self.assertIn(get_current_user, dependencies)


if __name__ == "__main__":
    unittest.main()
