from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User
from backend.app.core.database import get_db
from backend.app.roadmap.schemas import RoadmapItemResponse, RoadmapItemStatusUpdate, RoadmapResponse
from backend.app.roadmap.service import get_roadmap, update_roadmap_item_status

router = APIRouter(prefix="/api/v1/roadmap", tags=["Roadmap"])


@router.get("", response_model=RoadmapResponse)
def get_roadmap_endpoint(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_roadmap(db=db, user_id=current_user.id)


@router.patch("/{item_id}", response_model=RoadmapItemResponse)
def update_roadmap_item_endpoint(item_id: UUID, payload: RoadmapItemStatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return update_roadmap_item_status(db=db, user_id=current_user.id, item_id=item_id, new_status=payload.status)
