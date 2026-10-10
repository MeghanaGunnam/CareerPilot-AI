"""Opt-in, rollback-only PostgreSQL pipeline, confined to a synthetic schema.

Run this module alone with CAREERPILOT_POSTGRES_TEST=1. Uses configured DATABASE_URL
(or backend/.env). Requires CREATE SCHEMA; never reads application/user tables.
No schema, fixture, service commit, or test data survives the outer rollback.
"""
import json
import os
import unittest
import uuid


@unittest.skipUnless(os.getenv("CAREERPILOT_POSTGRES_TEST") == "1", "opt-in PostgreSQL integration")
class PostgresAssessmentPipelineTests(unittest.TestCase):
    def test_scoring_evidence_snapshot_and_goal_specific_recommendations(self):
        from sqlalchemy import select, text
        from sqlalchemy.orm import Session
        from backend.app.core.database import Base, engine
        from backend.app.auth.models import User
        from backend.app.students.models import CareerGoal
        from backend.app.skills.models import Skill, SkillEvidence
        from backend.app.assessments.models import Assessment, AssessmentQuestion
        from backend.app.assessments.schemas import AssessmentSubmitRequest
        from backend.app.assessments.service import submit_assessment, serialize_attempt_result
        from backend.app.assessments.recommendations import get_my_assessment_recommendations
        from backend.app.careers.models import Career, CareerSoftwareRequirement
        from backend.app.career_twin.service import get_career_twin, get_latest_snapshot
        from backend.app.acif.engine import calculate_all_skill_states

        self.assertEqual(engine.dialect.name, "postgresql")
        schema = "assessment_test_" + uuid.uuid4().hex
        with engine.connect() as connection:
            outer = connection.begin()
            try:
                connection.execute(text(f'CREATE SCHEMA "{schema}"'))
                connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
                Base.metadata.create_all(connection)
                with Session(bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False) as db:
                    users = [User(email=f"synthetic-{i}@example.invalid", password_hash="not-a-real-password") for i in range(2)]
                    skills = [Skill(canonical_name=name) for name in ("Python", "SQL")]
                    careers = [Career(onet_soc_code=f"00-0000.0{i}", title=f"Synthetic career {i}") for i in range(2)]
                    db.add_all(users + skills + careers)
                    db.flush()
                    assessments = []
                    questions = []
                    for index, skill in enumerate(skills):
                        assessment = Assessment(skill_id=skill.id, title=f"Synthetic {skill.canonical_name}",
                                                difficulty="BEGINNER", version=3, is_active=True)
                        db.add(assessment)
                        db.flush()
                        items = [AssessmentQuestion(assessment_id=assessment.id, position=i,
                            question_text=f"Synthetic item {i}", options=[{"key": "A", "text": "one"}, {"key": "B", "text": "two"}],
                            correct_option="A", explanation="Synthetic explanation") for i in range(1, 4)]
                        db.add_all(items)
                        assessments.append(assessment)
                        questions.append(items)
                        db.add(CareerSoftwareRequirement(career_id=careers[index].id, element_id=f"synthetic-{index}",
                            element_name="Synthetic software", workplace_example=skill.canonical_name, in_demand=True))
                        db.add(CareerGoal(user_id=users[index].id, target_role=careers[index].title,
                                          onet_soc_code=careers[index].onet_soc_code, is_primary=True))
                    db.commit()
                    initial = [get_my_assessment_recommendations(db, user.id) for user in users]
                    self.assertEqual([[r["skill_name"] for r in result["recommendations"]] for result in initial], [["Python"], ["SQL"]])
                    python_requirement = db.scalar(select(CareerSoftwareRequirement).where(CareerSoftwareRequirement.career_id == careers[0].id))
                    python_requirement.in_demand = False
                    python_requirement.hot_technology = True
                    db.commit()
                    self.assertEqual(get_my_assessment_recommendations(db, users[0].id)["recommended_count"], 0)
                    python_requirement.in_demand = True
                    db.commit()
                    payload = AssessmentSubmitRequest(answers=[{"question_id": q.id, "selected_option": "A" if i < 2 else "B"}
                        for i, q in enumerate(questions[0])])
                    attempt = submit_assessment(db, users[0].id, assessments[0].id, payload)
                    persisted = serialize_attempt_result(db, attempt)
                    self.assertEqual((persisted.raw_score, persisted.total_questions, persisted.percentage), (2, 3, 66.67))
                    self.assertEqual(len(persisted.answers), 3)
                    evidence = db.scalar(select(SkillEvidence).where(SkillEvidence.source_reference == str(attempt.id)))
                    provenance = json.loads(evidence.evidence_text)
                    self.assertEqual(provenance["assessment_version"], 3)
                    self.assertEqual(provenance["skill_id"], str(skills[0].id))
                    twin = get_career_twin(db, users[0].id)
                    snapshot = get_latest_snapshot(db, twin.id)
                    self.assertEqual(snapshot.trigger_type, "ASSESSMENT_COMPLETED")
                    stored_evidence = snapshot.state_data["skills"][0]["evidence"][0]
                    self.assertEqual(json.loads(stored_evidence["evidence_text"]), provenance)
                    states = calculate_all_skill_states(snapshot.state_data, now=attempt.completed_at)
                    self.assertEqual(states[0]["estimated_proficiency"], 0.6667)
                    self.assertEqual(get_my_assessment_recommendations(db, users[0].id)["recommended_count"], 0)
                    self.assertEqual(get_my_assessment_recommendations(db, users[1].id)["recommended_count"], 1)
                    # A goal change uses the new occupation, not the previous snapshot goal.
                    goal = db.scalar(select(CareerGoal).where(CareerGoal.user_id == users[0].id))
                    goal.onet_soc_code = careers[1].onet_soc_code
                    db.commit()
                    self.assertEqual([r["skill_name"] for r in get_my_assessment_recommendations(db, users[0].id)["recommendations"]], ["SQL"])
            finally:
                outer.rollback()
            self.assertIsNone(connection.scalar(text("SELECT to_regnamespace(:schema)"), {"schema": schema}))


if __name__ == "__main__":
    unittest.main()
