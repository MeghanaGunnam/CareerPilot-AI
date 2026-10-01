from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User
from backend.app.career_twin.schemas import (
    CareerTwinHistoryResponse,
    CareerTwinResponse,
    CareerTwinSnapshotResponse,
)
from backend.app.career_twin.service import (
    create_career_twin_snapshot,
    get_career_twin,
    get_latest_snapshot,
    get_snapshot_history,
)
from backend.app.core.database import get_db


router = APIRouter(
    prefix="/api/v1/career-twin",
    tags=["Career Twin"],
)


@router.post(
    "/snapshots",
    response_model=CareerTwinSnapshotResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_snapshot(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_career_twin_snapshot(
        db=db,
        user_id=current_user.id,
        trigger_type="MANUAL_REFRESH",
        source_type="USER",
    )


@router.get(
    "/me",
    response_model=CareerTwinResponse,
)
def get_my_career_twin(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    twin = get_career_twin(
        db=db,
        user_id=current_user.id,
    )

    if twin is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Career Twin has not been created yet. "
                "Create the first snapshot."
            ),
        )

    latest_snapshot = get_latest_snapshot(
        db=db,
        career_twin_id=twin.id,
    )

    return CareerTwinResponse(
        id=twin.id,
        user_id=twin.user_id,
        current_version=twin.current_version,
        created_at=twin.created_at,
        updated_at=twin.updated_at,
        latest_snapshot=latest_snapshot,
    )


@router.get(
    "/history",
    response_model=CareerTwinHistoryResponse,
)
def get_my_career_twin_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    twin = get_career_twin(
        db=db,
        user_id=current_user.id,
    )

    if twin is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Career Twin has not been created yet.",
        )

    snapshots = get_snapshot_history(
        db=db,
        career_twin_id=twin.id,
    )

    return CareerTwinHistoryResponse(
        career_twin_id=twin.id,
        current_version=twin.current_version,
        snapshots=snapshots,
    )