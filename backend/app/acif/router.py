from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.acif.schemas import AcifSkillStateResponse
from backend.app.acif.service import get_current_skill_states
from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User
from backend.app.core.database import get_db


router = APIRouter(
    prefix="/api/v1/acif",
    tags=["ACIF"],
)


@router.get(
    "/skill-state",
    response_model=AcifSkillStateResponse,
)
def get_skill_state(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_current_skill_states(
        db=db,
        user_id=current_user.id,
    )