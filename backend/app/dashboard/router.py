from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User
from backend.app.core.database import get_db
from backend.app.assistant.provider import get_assistant_provider
from backend.app.dashboard.schemas import DashboardSummary
from backend.app.dashboard.service import get_dashboard_summary

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def summary(db: Session = Depends(get_db), user: User = Depends(get_current_user), provider=Depends(get_assistant_provider)):
    return get_dashboard_summary(db, user.id, provider)
