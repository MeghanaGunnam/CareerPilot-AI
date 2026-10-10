"""Deterministic scoring and evidence contract, without a live database."""
import json
import os
import unittest
import uuid
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://test:test@localhost/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("SECRET_KEY", "assessment-unit-tests")

from fastapi import HTTPException
from backend.app.assessments import service
from backend.app.assessments.schemas import AssessmentSubmitRequest
from backend.app.skills.models import SkillEvidence
from backend.app.acif.engine import calculate_all_skill_states


class AssessmentPipelineTests(unittest.TestCase):
    def setUp(self):
        self.db = Mock()
        self.user_id = uuid.uuid4()
        self.assessment = NS(id=uuid.uuid4(), skill_id=uuid.uuid4(), title="Python sample", version=7)
        self.questions = [NS(id=uuid.uuid4(), position=i, correct_option="A",
                             options=[{"key": "A"}, {"key": "B"}]) for i in range(1, 4)]
        self.db.scalar.return_value = self.assessment
        self.db.scalars.return_value.all.return_value = self.questions
        self.added = []
        def add(row):
            row.id = uuid.uuid4()
            self.added.append(row)
        self.db.add.side_effect = add

    def payload(self, options):
        return AssessmentSubmitRequest(answers=[
            {"question_id": q.id, "selected_option": option}
            for q, option in zip(self.questions, options)
        ])

    def test_partial_and_zero_scores_keep_provenance_and_snapshot_trigger(self):
        for options, raw, percent in (([" a ", "A", "B"], 2, 66.67), (["B"] * 3, 0, 0.0)):
            with self.subTest(raw=raw), \
                 patch.object(service, "get_or_create_student_skill", return_value=NS(id=uuid.uuid4())), \
                 patch.object(service, "create_career_twin_snapshot") as snapshot:
                attempt = service.submit_assessment(self.db, self.user_id, self.assessment.id, self.payload(options))
                self.assertEqual((attempt.raw_score, attempt.percentage, attempt.status), (raw, percent, "COMPLETED"))
                evidence = [r for r in self.added if isinstance(r, SkillEvidence)][-1]
                provenance = json.loads(evidence.evidence_text)
                self.assertEqual(provenance["assessment_version"], 7)
                self.assertEqual(provenance["assessment_id"], str(self.assessment.id))
                self.assertEqual(provenance["attempt_id"], str(attempt.id))
                self.assertEqual(provenance["skill_id"], str(self.assessment.skill_id))
                self.assertEqual(provenance["percentage"], percent)
                self.assertEqual(provenance["completed_at"], attempt.completed_at.isoformat())
                self.assertEqual(evidence.source_reference, str(attempt.id))
                self.assertIn("not universal", provenance["interpretation"])
                snapshot.assert_called_once_with(db=self.db, user_id=self.user_id,
                    trigger_type="ASSESSMENT_COMPLETED", source_type="ASSESSMENT", source_reference=str(attempt.id))
                states = calculate_all_skill_states({"skills": [{"skill_id": str(self.assessment.skill_id),
                    "name": "Python", "evidence": [{"source_type": evidence.source_type,
                    "evidence_status": evidence.evidence_status, "evidence_strength": evidence.evidence_strength,
                    "observed_at": evidence.observed_at}]}]}, now=attempt.completed_at)
                self.assertEqual(states[0]["estimated_proficiency"], round(percent / 100, 4))

    def test_invalid_payload_never_persists_attempt_or_answers(self):
        payloads = [self.payload(["A"]), self.payload(["A", "A", "invalid"])]
        duplicate = self.payload(["A"] * 3)
        duplicate.answers[2].question_id = duplicate.answers[0].question_id
        payloads.append(duplicate)
        foreign = self.payload(["A"] * 3)
        foreign.answers[2].question_id = uuid.uuid4()
        payloads.append(foreign)
        for payload in payloads:
            with self.assertRaises(HTTPException):
                service.submit_assessment(self.db, self.user_id, self.assessment.id, payload)
        self.db.add.assert_not_called()
        self.db.commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
