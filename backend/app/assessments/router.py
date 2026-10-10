import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.assessments.models import (
    AssessmentQuestion,
)
from backend.app.assessments.schemas import (
    AssessmentAttemptSummaryResponse,
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
    get_catalog_metadata,
    get_skill_or_404,
    get_user_attempt_or_404,
    get_user_attempts,
    serialize_attempt_result,
    serialize_attempt_summary,
    submit_assessment,
)
from backend.app.assessments.recommendations import (
    get_career_assessment_recommendations,
    get_my_assessment_recommendations,
)
from backend.app.assessments.catalog import get_controlled_catalog_metadata
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
    question_counts, latest_attempts = get_catalog_metadata(
        db, current_user.id, [assessment.id for assessment in assessments]
    )

    response: list[AssessmentListItemResponse] = []

    for assessment in assessments:
        skill = assessment.skill

        response.append(
            AssessmentListItemResponse(
                catalog_metadata=get_controlled_catalog_metadata(assessment, skill.canonical_name),
                id=assessment.id,
                skill_id=skill.id,
                skill_name=skill.canonical_name,
                title=assessment.title,
                description=assessment.description,
                difficulty=assessment.difficulty,
                version=assessment.version,
                question_count=question_counts.get(assessment.id, 0),
                latest_attempt=(
                    serialize_attempt_summary(latest_attempts[assessment.id])
                    if assessment.id in latest_attempts else None
                ),
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

@router.get("/recommendations/me", response_model=CareerAssessmentRecommendationsResponse)
def get_my_recommended_assessments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_my_assessment_recommendations(db=db, user_id=current_user.id)


@router.get(
    "/attempts",
    response_model=list[AssessmentAttemptSummaryResponse],
)
def list_assessment_attempts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    return [
        serialize_attempt_summary(attempt)
        for attempt in get_user_attempts(db, current_user.id, limit, offset)
    ]


@router.get(
    "/attempts/{attempt_id}",
    response_model=AssessmentAttemptResultResponse,
)
def get_assessment_attempt(
    attempt_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = get_user_attempt_or_404(db, current_user.id, attempt_id)
    return serialize_attempt_result(db, attempt)


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
        catalog_metadata=get_controlled_catalog_metadata(assessment, skill.canonical_name),
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

    return serialize_attempt_result(db, attempt)
