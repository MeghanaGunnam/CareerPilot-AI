import json
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from backend.app.assessments.models import (
    Assessment,
    AssessmentAnswer,
    AssessmentAttempt,
    AssessmentQuestion,
)
from backend.app.assessments.schemas import (
    AssessmentAnswerResult,
    AssessmentAttemptResultResponse,
    AssessmentAttemptSummaryResponse,
    AssessmentSubmitRequest,
)
from backend.app.skills.models import Skill, SkillEvidence, StudentSkill
from backend.app.skills.service import get_or_create_student_skill
from backend.app.career_twin.service import (
    create_career_twin_snapshot,
)

def get_active_assessments(db: Session) -> list[Assessment]:
    statement = (
        select(Assessment)
        .options(joinedload(Assessment.skill))
        .where(Assessment.is_active.is_(True))
        .order_by(Assessment.title.asc())
    )
    return list(db.scalars(statement).all())


def get_user_attempts(
    db: Session,
    user_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
) -> list[AssessmentAttempt]:
    statement = (
        select(AssessmentAttempt)
        .options(joinedload(AssessmentAttempt.assessment).joinedload(Assessment.skill))
        .where(AssessmentAttempt.user_id == user_id)
        .order_by(AssessmentAttempt.started_at.desc(), AssessmentAttempt.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(statement).all())


def get_user_attempt_or_404(
    db: Session,
    user_id: uuid.UUID,
    attempt_id: uuid.UUID,
) -> AssessmentAttempt:
    attempt = db.scalar(
        select(AssessmentAttempt)
        .options(joinedload(AssessmentAttempt.assessment).joinedload(Assessment.skill))
        .where(
            AssessmentAttempt.id == attempt_id,
            AssessmentAttempt.user_id == user_id,
        )
    )
    if attempt is None:
        raise HTTPException(status_code=404, detail="Assessment attempt not found.")
    return attempt


def get_catalog_metadata(
    db: Session,
    user_id: uuid.UUID,
    assessment_ids: list[uuid.UUID],
) -> tuple[dict[uuid.UUID, int], dict[uuid.UUID, AssessmentAttempt]]:
    if not assessment_ids:
        return {}, {}
    counts = dict(db.execute(
        select(AssessmentQuestion.assessment_id, func.count(AssessmentQuestion.id))
        .where(AssessmentQuestion.assessment_id.in_(assessment_ids))
        .group_by(AssessmentQuestion.assessment_id)
    ).all())
    ranked = (
        select(
            AssessmentAttempt.id,
            func.row_number().over(
                partition_by=AssessmentAttempt.assessment_id,
                order_by=(AssessmentAttempt.started_at.desc(), AssessmentAttempt.id.desc()),
            ).label("rank"),
        )
        .where(
            AssessmentAttempt.user_id == user_id,
            AssessmentAttempt.assessment_id.in_(assessment_ids),
        )
        .subquery()
    )
    latest = db.scalars(
        select(AssessmentAttempt)
        .join(ranked, ranked.c.id == AssessmentAttempt.id)
        .where(ranked.c.rank == 1)
        .options(joinedload(AssessmentAttempt.assessment).joinedload(Assessment.skill))
    ).all()
    return counts, {attempt.assessment_id: attempt for attempt in latest}


def serialize_attempt_summary(
    attempt: AssessmentAttempt,
) -> AssessmentAttemptSummaryResponse:
    # Historical reads deliberately include inactive assessment versions.
    assessment = attempt.assessment
    return AssessmentAttemptSummaryResponse(
        attempt_id=attempt.id,
        assessment_id=assessment.id,
        assessment_title=assessment.title,
        assessment_version=assessment.version,
        skill_id=assessment.skill_id,
        skill_name=assessment.skill.canonical_name,
        status=attempt.status,
        raw_score=attempt.raw_score,
        total_questions=attempt.total_questions,
        percentage=attempt.percentage,
        started_at=attempt.started_at,
        completed_at=attempt.completed_at,
    )


def serialize_attempt_result(
    db: Session,
    attempt: AssessmentAttempt,
) -> AssessmentAttemptResultResponse:
    answer_results = []
    if attempt.status == "COMPLETED":
        answers = db.scalars(
            select(AssessmentAnswer)
            .options(joinedload(AssessmentAnswer.question))
            .where(AssessmentAnswer.attempt_id == attempt.id)
            .order_by(AssessmentAnswer.answered_at.asc(), AssessmentAnswer.id.asc())
        ).all()
        for answer in answers:
            question = answer.question
            if question is None:
                continue
            answer_results.append(AssessmentAnswerResult(
                question_id=question.id,
                selected_option=answer.selected_option,
                correct_option=question.correct_option,
                is_correct=answer.is_correct,
                explanation=question.explanation,
            ))
    return AssessmentAttemptResultResponse(
        **serialize_attempt_summary(attempt).model_dump(),
        answers=answer_results,
    )


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

    # Validate the entire payload before creating any attempt or answer rows.
    for question in questions:
        valid_options = {str(option["key"]).upper() for option in question.options}
        if submitted_answers[question.id] not in valid_options:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid option for question {question.position}.",
            )

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
        evidence_text=json.dumps({
            "schema_version": "assessment-evidence-v1",
            "assessment_id": str(assessment.id),
            "assessment_version": assessment.version,
            "assessment_title": assessment.title,
            "attempt_id": str(attempt.id),
            "skill_id": str(assessment.skill_id),
            "raw_score": correct_count,
            "total_questions": len(questions),
            "percentage": percentage,
            "completed_at": completed_at.isoformat(),
            "interpretation": "Observed score on this version's question sample; not universal skill proficiency.",
        }, sort_keys=True),
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

    create_career_twin_snapshot(
        db=db,
        user_id=user_id,
        trigger_type="ASSESSMENT_COMPLETED",
        source_type="ASSESSMENT",
        source_reference=str(attempt.id),
    )
    return attempt
