from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.assessments.models import Assessment, AssessmentQuestion
from backend.app.assessments.question_bank import TECHNICAL_ASSESSMENTS
from backend.app.skills.models import Skill


def seed_technical_assessments(db: Session) -> dict[str, int]:
    assessments_created = 0
    questions_created = 0
    assessments_skipped = 0

    for assessment_data in TECHNICAL_ASSESSMENTS:
        skill_name = assessment_data["skill"]

        skill = db.scalar(
            select(Skill).where(
                Skill.canonical_name == skill_name
            )
        )

        if skill is None:
            raise ValueError(
                f"Skill '{skill_name}' does not exist. "
                "Create/import the skill before seeding its assessment."
            )

        existing_assessment = db.scalar(
            select(Assessment).where(
                Assessment.skill_id == skill.id,
                Assessment.version == assessment_data["version"],
                Assessment.title == assessment_data["title"],
            )
        )

        if existing_assessment is not None:
            assessments_skipped += 1
            continue

        assessment = Assessment(
            skill_id=skill.id,
            title=assessment_data["title"],
            description=assessment_data["description"],
            difficulty=assessment_data["difficulty"],
            version=assessment_data["version"],
            is_active=True,
        )

        db.add(assessment)
        db.flush()

        for question_data in assessment_data["questions"]:
            question = AssessmentQuestion(
                assessment_id=assessment.id,
                position=question_data["position"],
                question_text=question_data["question_text"],
                options=question_data["options"],
                correct_option=question_data["correct_option"],
                explanation=question_data["explanation"],
            )

            db.add(question)
            questions_created += 1

        assessments_created += 1

    db.commit()

    return {
        "assessments_created": assessments_created,
        "questions_created": questions_created,
        "assessments_skipped": assessments_skipped,
    }