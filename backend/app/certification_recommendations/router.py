from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User
from backend.app.certification_recommendations.schemas import CertificationRecommendationsResponse
from backend.app.certification_recommendations.service import get_certification_recommendations
from backend.app.core.database import get_db


router = APIRouter(prefix="/api/v1/certification-recommendations", tags=["Certification Recommendations"])


@router.get("", response_model=CertificationRecommendationsResponse)
def get_certification_recommendations_endpoint(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
):
    return get_certification_recommendations(db=db, user_id=current_user.id)
