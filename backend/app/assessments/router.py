import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.assessments.models import (
    AssessmentAnswer,
    AssessmentQuestion,
)
from backend.app.assessments.schemas import (
    AssessmentAnswerResult,
    AssessmentDetailResponse,
    AssessmentListItemResponse,
    AssessmentQuestionResponse,
    AssessmentAttemptResultResponse,
    AssessmentSubmitRequest,
    CareerAssessmentRecommendationsResponse,
)
from backend.app.assessments.service import (
    get_active_assessments,
    get_assessment_or_404,
    get_skill_or_404,
    submit_assessment,
)
from backend.app.assessments.recommendations import (
    get_career_assessment_recommendations,
)
from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User
from backend.app.core.database import get_db


router = APIRouter(
    prefix="/api/v1/assessments",
    tags=["Technical Assessments"],
)


@router.get(
    "",
    response_model=list[AssessmentListItemResponse],
)
def list_assessments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    assessments = get_active_assessments(db)

    response: list[AssessmentListItemResponse] = []

    for assessment in assessments:
        skill = get_skill_or_404(
            db=db,
            skill_id=assessment.skill_id,
        )

        response.append(
            AssessmentListItemResponse(
                id=assessment.id,
                skill_id=skill.id,
                skill_name=skill.canonical_name,
                title=assessment.title,
                description=assessment.description,
                difficulty=assessment.difficulty,
                version=assessment.version,
            )
        )

    return response
@router.get(
    "/recommendations/careers/{career_id}",
    response_model=CareerAssessmentRecommendationsResponse,
)
def get_recommended_assessments(
    career_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_career_assessment_recommendations(
        db=db,
        user_id=current_user.id,
        career_id=career_id,
    )

@router.get(
    "/{assessment_id}",
    response_model=AssessmentDetailResponse,
)
def get_assessment(
    assessment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    assessment = get_assessment_or_404(
        db=db,
        assessment_id=assessment_id,
    )

    skill = get_skill_or_404(
        db=db,
        skill_id=assessment.skill_id,
    )

    questions = list(
        db.scalars(
            select(AssessmentQuestion)
            .where(
                AssessmentQuestion.assessment_id
                == assessment.id
            )
            .order_by(
                AssessmentQuestion.position.asc()
            )
        ).all()
    )

    return AssessmentDetailResponse(
        id=assessment.id,
        skill_id=skill.id,
        skill_name=skill.canonical_name,
        title=assessment.title,
        description=assessment.description,
        difficulty=assessment.difficulty,
        version=assessment.version,
        questions=[
            AssessmentQuestionResponse(
                id=question.id,
                position=question.position,
                question_text=question.question_text,
                options=question.options,
            )
            for question in questions
        ],
    )


@router.post(
    "/{assessment_id}/submit",
    response_model=AssessmentAttemptResultResponse,
)
def submit_technical_assessment(
    assessment_id: uuid.UUID,
    payload: AssessmentSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = submit_assessment(
        db=db,
        user_id=current_user.id,
        assessment_id=assessment_id,
        payload=payload,
    )

    assessment = get_assessment_or_404(
        db=db,
        assessment_id=attempt.assessment_id,
    )

    skill = get_skill_or_404(
        db=db,
        skill_id=assessment.skill_id,
    )

    answers = list(
        db.scalars(
            select(AssessmentAnswer)
            .where(
                AssessmentAnswer.attempt_id
                == attempt.id
            )
            .order_by(
                AssessmentAnswer.answered_at.asc()
            )
        ).all()
    )

    answer_results: list[
        AssessmentAnswerResult
    ] = []

    for answer in answers:
        question = db.get(
            AssessmentQuestion,
            answer.question_id,
        )

        if question is None:
            continue

        answer_results.append(
            AssessmentAnswerResult(
                question_id=question.id,
                selected_option=answer.selected_option,
                correct_option=question.correct_option,
                is_correct=answer.is_correct,
                explanation=question.explanation,
            )
        )

    return AssessmentAttemptResultResponse(
        attempt_id=attempt.id,
        assessment_id=assessment.id,
        skill_id=skill.id,
        skill_name=skill.canonical_name,
        status=attempt.status,
        raw_score=attempt.raw_score,
        total_questions=attempt.total_questions,
        percentage=attempt.percentage,
        completed_at=attempt.completed_at,
        answers=answer_results,
    )