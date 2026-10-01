from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.app.acif.engine import (
    ACIF_MODEL_VERSION,
    calculate_all_skill_states,
)
from backend.app.career_twin.service import (
    get_career_twin,
    get_latest_snapshot,
)


def get_current_skill_states(
    db: Session,
    user_id: UUID,
) -> dict:
    twin = get_career_twin(
        db=db,
        user_id=user_id,
    )

    if twin is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Career Twin has not been created yet. "
                "Create a Career Twin snapshot first."
            ),
        )

    snapshot = get_latest_snapshot(
        db=db,
        career_twin_id=twin.id,
    )

    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Career Twin does not contain a snapshot yet.",
        )

    skill_states = calculate_all_skill_states(
        snapshot.state_data
    )

    return {
        "career_twin_id": str(twin.id),
        "snapshot_version": snapshot.version,
        "model_version": ACIF_MODEL_VERSION,
        "skills": skill_states,
    }