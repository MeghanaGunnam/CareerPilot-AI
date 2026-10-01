import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.assessments.models import (
    Assessment,
    AssessmentAnswer,
    AssessmentAttempt,
    AssessmentQuestion,
)
from backend.app.assessments.schemas import AssessmentSubmitRequest
from backend.app.skills.models import Skill, SkillEvidence, StudentSkill
from backend.app.skills.service import get_or_create_student_skill


def get_active_assessments(db: Session) -> list[Assessment]:
    statement = (
        select(Assessment)
        .where(Assessment.is_active.is_(True))
        .order_by(Assessment.title.asc())
    )
    return list(db.scalars(statement).all())


def get_assessment_or_404(
    db: Session,
    assessment_id: uuid.UUID,
) -> Assessment:
    assessment = db.scalar(
        select(Assessment).where(
            Assessment.id == assessment_id,
            Assessment.is_active.is_(True),
        )
    )

    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found.",
        )

    return assessment


def get_skill_or_404(
    db: Session,
    skill_id: uuid.UUID,
) -> Skill:
    skill = db.get(Skill, skill_id)

    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment skill not found.",
        )

    return skill


def submit_assessment(
    db: Session,
    user_id: uuid.UUID,
    assessment_id: uuid.UUID,
    payload: AssessmentSubmitRequest,
) -> AssessmentAttempt:

    assessment = get_assessment_or_404(db, assessment_id)

    questions = list(
        db.scalars(
            select(AssessmentQuestion)
            .where(
                AssessmentQuestion.assessment_id == assessment.id
            )
            .order_by(AssessmentQuestion.position.asc())
        ).all()
    )

    if not questions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment has no questions.",
        )

    if len(payload.answers) != len(questions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All assessment questions must be answered exactly once.",
        )

    submitted_answers = {
        answer.question_id: answer.selected_option.strip().upper()
        for answer in payload.answers
    }

    if len(submitted_answers) != len(payload.answers):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A question was submitted more than once.",
        )

    question_map = {
        question.id: question
        for question in questions
    }

    if set(submitted_answers.keys()) != set(question_map.keys()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Submitted answers do not match this assessment.",
        )

    correct_count = 0

    attempt = AssessmentAttempt(
        user_id=user_id,
        assessment_id=assessment.id,
        status="IN_PROGRESS",
        total_questions=len(questions),
    )

    db.add(attempt)
    db.flush()

    for question in questions:
        selected_option = submitted_answers[question.id]

        valid_options = {
            str(option["key"]).upper()
            for option in question.options
        }

        if selected_option not in valid_options:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid option for question "
                    f"{question.position}."
                ),
            )

        is_correct = (
            selected_option.upper()
            == question.correct_option.upper()
        )

        if is_correct:
            correct_count += 1

        db.add(
            AssessmentAnswer(
                attempt_id=attempt.id,
                question_id=question.id,
                selected_option=selected_option,
                is_correct=is_correct,
            )
        )

    percentage = round(
        (correct_count / len(questions)) * 100.0,
        2,
    )

    completed_at = datetime.now(timezone.utc)

    attempt.raw_score = correct_count
    attempt.percentage = percentage
    attempt.status = "COMPLETED"
    attempt.completed_at = completed_at

    student_skill = get_or_create_student_skill(
        db=db,
        user_id=user_id,
        skill_id=assessment.skill_id,
    )

    evidence = SkillEvidence(
        student_skill_id=student_skill.id,
        source_type="ASSESSMENT",
        source_reference=str(attempt.id),
        source_section=assessment.title,
        evidence_text=(
            f"{correct_count}/{len(questions)} correct "
            f"({percentage:.2f}%)"
        ),
        evidence_status="ASSESSED",
        evidence_strength=percentage / 100.0,
        observed_at=completed_at,
    )

    db.add(evidence)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(attempt)

    return attempt