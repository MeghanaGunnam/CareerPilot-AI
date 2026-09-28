from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User
from backend.app.core.database import get_db
from backend.app.psychometrics.questions import (
    RESPONSE_OPTIONS,
    RIASEC_QUESTIONS,
)
from backend.app.psychometrics.schemas import (
    CareerInterestMatchResponse,
    RiasecAssessmentRequest,
    RiasecAssessmentResultResponse,
    RiasecQuestionnaireResponse,
)
from backend.app.psychometrics.service import (
    ASSESSMENT_VERSION,
    create_assessment,
    get_interest_matches,
    get_latest_assessment,
)


router = APIRouter(
    prefix="/api/v1/psychometrics",
    tags=["Psychometrics"],
)


@router.get(
    "/riasec/questions",
    response_model=RiasecQuestionnaireResponse,
)
def get_riasec_questions(
    current_user: User = Depends(get_current_user),
):
    return RiasecQuestionnaireResponse(
        assessment_version=ASSESSMENT_VERSION,
        instructions=(
            "Rate how much you would enjoy each activity. "
            "Answer based on your genuine interests rather than "
            "what you think you should choose as a career."
        ),
        questions=RIASEC_QUESTIONS,
        response_options=RESPONSE_OPTIONS,
    )


@router.post(
    "/riasec/assessments",
    response_model=RiasecAssessmentResultResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_riasec_assessment(
    payload: RiasecAssessmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_assessment(
        db=db,
        user_id=current_user.id,
        answers=payload.answers,
    )


@router.get(
    "/riasec/latest",
    response_model=RiasecAssessmentResultResponse,
)
def get_latest_riasec_assessment(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = get_latest_assessment(
        db=db,
        user_id=current_user.id,
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No completed RIASEC assessment found.",
        )

    return result


@router.get(
    "/riasec/matches",
    response_model=list[CareerInterestMatchResponse],
)
def get_riasec_career_matches(
    limit: int = Query(
        default=10,
        ge=1,
        le=50,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_interest_matches(
        db=db,
        user_id=current_user.id,
        limit=limit,
    )