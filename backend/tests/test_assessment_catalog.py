"""Catalog contracts and real SQLAlchemy persistence in isolated in-memory SQLite."""

import os
import unittest
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://test:test@localhost/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("SECRET_KEY", "catalog-unit-test-only")

from sqlalchemy import create_engine, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session

from backend.app.assessments.catalog import CATALOG, get_controlled_catalog_metadata, validate_catalog
from backend.app.assessments.models import Assessment, AssessmentQuestion
from backend.app.assessments.question_bank import TECHNICAL_ASSESSMENTS
from backend.app.assessments.seed import CatalogDriftError, seed_technical_assessments
from backend.app.skills.models import Skill


@compiles(JSONB, "sqlite")
def _sqlite_jsonb(element, compiler, **kwargs):
    return "JSON"


class CatalogValidationTests(unittest.TestCase):
    def test_membership_and_counts(self):
        bank = validate_catalog()
        self.assertEqual({a["skill"]: len(a["questions"]) for a in bank},
                         {"Java": 5, "Critical Thinking": 5, "Python": 10, "SQL": 10})
        self.assertEqual(len({e.catalog_id for e in CATALOG}), 4)

    def test_invalid_keys_positions_answers_and_duplicates_rejected(self):
        for mutation in (
            lambda q: q.update(position=2),
            lambda q: q.update(correct_option="E"),
            lambda q: q["options"][1].update(key="A"),
            lambda q: q["options"][1].update(text=q["options"][0]["text"]),
            lambda q: q.update(explanation=" "),
        ):
            bank = deepcopy(TECHNICAL_ASSESSMENTS)
            mutation(bank[0]["questions"][0])
            with self.assertRaises(ValueError):
                validate_catalog(bank)

    def test_metadata_uses_exact_registration_and_db_active_state(self):
        assessment = SimpleNamespace(title="Python Fundamentals Assessment", version=1, is_active=False)
        result = get_controlled_catalog_metadata(assessment, "Python")
        self.assertEqual(result["catalog_id"], "python-fundamentals")
        self.assertEqual(result["domain"], "PROGRAMMING")
        self.assertFalse(result["is_active"])
        self.assertNotIn("questions", result)
        self.assertIsNone(get_controlled_catalog_metadata(assessment, "Java"))
        assessment.version = 2
        self.assertIsNone(get_controlled_catalog_metadata(assessment, "Python"))


class CatalogPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        for table in (Skill.__table__, Assessment.__table__, AssessmentQuestion.__table__):
            table.create(self.engine)
        self.db = Session(self.engine)
        self.db.add_all([Skill(canonical_name="Java"), Skill(canonical_name="Critical Thinking")])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def count(self, model):
        return self.db.scalar(select(func.count()).select_from(model))

    def test_seed_readback_and_idempotence(self):
        self.assertEqual(seed_technical_assessments(self.db), dict(
            assessments_created=4, questions_created=30, assessments_skipped=0, skills_created=2))
        before = self.db.scalars(select(Assessment).order_by(Assessment.title)).all()
        identities = [a.id for a in before]
        self.assertEqual(sum(len(a.questions) for a in before), 30)
        before[0].is_active = False
        self.db.commit()
        counts = seed_technical_assessments(self.db)
        self.assertEqual(counts, dict(assessments_created=0, questions_created=0, assessments_skipped=4, skills_created=0))
        self.db.expire_all()
        after = self.db.scalars(select(Assessment).order_by(Assessment.title)).all()
        self.assertEqual([a.id for a in after], identities)
        self.assertFalse(after[0].is_active)
        self.assertEqual(self.count(Skill), 4)

    def test_question_drift_refused_without_mutating_persisted_content(self):
        seed_technical_assessments(self.db)
        question = self.db.scalar(select(AssessmentQuestion))
        question.question_text = "Historical custom content"
        self.db.commit()
        with self.assertRaises(CatalogDriftError):
            seed_technical_assessments(self.db)
        self.db.refresh(question)
        self.assertEqual(question.question_text, "Historical custom content")
        self.assertEqual(self.count(AssessmentQuestion), 30)

    def test_title_drift_is_not_a_new_assessment(self):
        seed_technical_assessments(self.db)
        assessment = self.db.scalar(select(Assessment))
        assessment.title = "Locally changed title"
        self.db.commit()
        with self.assertRaises(CatalogDriftError):
            seed_technical_assessments(self.db)
        self.assertEqual(self.count(Assessment), 4)

    def test_case_variant_skill_refused_before_any_assessment_write(self):
        self.db.add(Skill(canonical_name="python"))
        self.db.commit()
        with self.assertRaisesRegex(ValueError, "noncanonical"):
            seed_technical_assessments(self.db)
        self.assertEqual(self.count(Assessment), 0)
        self.assertEqual(self.count(Skill), 3)

    def test_missing_legacy_skill_can_be_created_without_mapping_tables(self):
        critical = self.db.scalar(select(Skill).where(Skill.canonical_name == "Critical Thinking"))
        self.db.delete(critical)
        self.db.commit()
        counts = seed_technical_assessments(self.db)
        self.assertEqual(counts["skills_created"], 3)
        self.assertEqual(self.count(Assessment), 4)

    def test_duplicate_existing_version_refused(self):
        seed_technical_assessments(self.db)
        original = self.db.scalar(select(Assessment))
        self.db.add(Assessment(skill_id=original.skill_id, title=original.title,
                               version=original.version, difficulty=original.difficulty))
        self.db.commit()
        with self.assertRaisesRegex(CatalogDriftError, "multiple assessment rows"):
            seed_technical_assessments(self.db)
        self.assertEqual(self.count(AssessmentQuestion), 30)

    def test_insert_failure_rolls_back_skills_questions_and_assessments(self):
        real_flush = self.db.flush
        calls = 0

        def fail_late(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 6:
                raise RuntimeError("Simulated write failure")
            return real_flush(*args, **kwargs)

        with patch.object(self.db, "flush", side_effect=fail_late):
            with self.assertRaises(RuntimeError):
                seed_technical_assessments(self.db)
        self.assertEqual(self.count(Assessment), 0)
        self.assertEqual(self.count(AssessmentQuestion), 0)
        self.assertEqual(self.count(Skill), 2)

    def test_dirty_session_is_not_committed(self):
        self.db.add(Skill(canonical_name="User work"))
        with self.assertRaisesRegex(ValueError, "clean dedicated"):
            seed_technical_assessments(self.db)
        self.assertEqual(len(self.db.new), 1)


if __name__ == "__main__":
    unittest.main()
