from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from backend.app.assessments.catalog import CATALOG, catalog_assessment_id, validate_catalog
from backend.app.assessments.models import Assessment, AssessmentQuestion
from backend.app.skills.models import Skill


class CatalogDriftError(ValueError):
    """An existing assessment version differs from its controlled definition."""


QUESTION_FIELDS = ("position", "question_text", "options", "correct_option", "explanation")
ASSESSMENT_FIELDS = ("title", "description", "difficulty", "version")
NEW_SKILLS = {
    "Java": ("Programming Language", "Java programming language; canonical skill required by the preserved local assessment."),
    "Critical Thinking": ("Reasoning", "Critical thinking; canonical skill required by the preserved local assessment, without an asserted O*NET equivalence."),
    "Python": ("Programming Language", "Python programming language; local assessment skill, not an O*NET competency equivalence."),
    "SQL": ("Query Language", "Structured Query Language; local assessment skill, not an O*NET competency equivalence."),
}


def _verify_existing(assessment, item):
    for field in ASSESSMENT_FIELDS:
        if getattr(assessment, field) != item[field]:
            raise CatalogDriftError(f"{item['skill']} v{item['version']}: {field} drift; append a new version instead")
    actual = [{field: getattr(q, field) for field in QUESTION_FIELDS} for q in assessment.questions]
    expected = [{field: q[field] for field in QUESTION_FIELDS} for q in item["questions"]]
    if actual != expected:
        raise CatalogDriftError(f"{item['skill']} v{item['version']}: question drift; append a new version instead")


def seed_technical_assessments(db: Session) -> dict[str, int]:
    """Append missing versions atomically. Never edit existing content or active flags.

    Owns commit/rollback; use a clean dedicated Session. PostgreSQL seed runs are
    serialized because the legacy schema has no skill/version unique constraint.
    """
    bank = validate_catalog()
    if db.new or db.dirty or db.deleted:
        raise ValueError("Catalog seed requires a clean dedicated session")
    counts = dict(assessments_created=0, questions_created=0, assessments_skipped=0, skills_created=0)
    try:
        if db.get_bind().dialect.name == "postgresql":
            db.execute(text("SELECT pg_advisory_xact_lock(728194602)"))
        plan = []
        # Validate every existing version before inserting any catalog content.
        for item in bank:
            entry = next(e for e in CATALOG if (e.skill_name, e.title, e.version) == (item["skill"], item["title"], item["version"]))
            matches = db.scalars(select(Skill).where(func.lower(func.trim(Skill.canonical_name)) == item["skill"].lower())).all()
            if len(matches) > 1 or (matches and matches[0].canonical_name != item["skill"]):
                raise ValueError(f"Ambiguous/noncanonical skill '{item['skill']}'; resolve explicitly before seeding")
            skill = matches[0] if matches else None
            if skill is None and item["skill"] not in NEW_SKILLS:
                raise ValueError(f"Skill '{item['skill']}' does not exist; import it before seeding")
            existing = [] if skill is None else db.scalars(select(Assessment).where(Assessment.skill_id == skill.id, Assessment.version == item["version"])).all()
            if len(existing) > 1:
                raise CatalogDriftError(f"Ambiguous {item['skill']} v{item['version']}; multiple assessment rows")
            if existing:
                _verify_existing(existing[0], item)
                counts["assessments_skipped"] += 1
            else:
                plan.append((item, entry, skill))
        created_skills = {}
        for item, entry, skill in plan:
            if skill is None:
                skill = created_skills.get(item["skill"])
                if skill is None:
                    category, description = NEW_SKILLS[item["skill"]]
                    skill = Skill(canonical_name=item["skill"], category=category, description=description)
                    db.add(skill)
                    db.flush()
                    created_skills[item["skill"]] = skill
                    counts["skills_created"] += 1
            assessment = Assessment(id=catalog_assessment_id(entry), skill_id=skill.id, is_active=entry.is_active, **{field: item[field] for field in ASSESSMENT_FIELDS})
            db.add(assessment)
            db.flush()
            for question in item["questions"]:
                db.add(AssessmentQuestion(assessment_id=assessment.id, **{field: question[field] for field in QUESTION_FIELDS}))
                counts["questions_created"] += 1
            counts["assessments_created"] += 1
        db.commit()
    except Exception:
        db.rollback()
        raise
    return counts
