from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.acif.schemas import AcifSkillStateResponse
from backend.app.acif.service import (
    get_career_gap_analysis,
    get_career_gps,
    get_career_match,
    get_career_readiness,
    get_current_skill_states,
    get_minimum_action_path,
    simulate_skill_evidence,
    simulate_career_skill_evidence,
)
from backend.app.acif.schemas import SkillEvidenceSimulationRequest
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


@router.get(
    "/careers/{career_id}/match",
)
def get_match_for_career(
    career_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_career_match(
        db=db,
        user_id=current_user.id,
        career_id=career_id,
    )


@router.get(
    "/careers/{career_id}/gap-analysis",
)
def get_gap_analysis_for_career(
    career_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_career_gap_analysis(
        db=db,
        user_id=current_user.id,
        career_id=career_id,
    )


@router.get(
    "/careers/{career_id}/readiness",
)
def get_readiness_for_career(
    career_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_career_readiness(
        db=db,
        user_id=current_user.id,
        career_id=career_id,
    )
@router.get(
    "/careers/{career_id}/career-gps",
)
def get_gps_for_career(
    career_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_career_gps(
        db=db,
        user_id=current_user.id,
        career_id=career_id,
    )
@router.get(
    "/careers/{career_id}/minimum-action-path",
)
def get_minimum_path_for_career(
    career_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_minimum_action_path(
        db=db,
        user_id=current_user.id,
        career_id=career_id,
    )
@router.post("/simulations/skill-evidence")
def simulate_skill_evidence_api(
    request: SkillEvidenceSimulationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return simulate_skill_evidence(
        db=db,
        user_id=current_user.id,
        skill_name=request.skill_name,
        simulated_confidence=request.simulated_confidence,
    )
@router.post(
    "/careers/{career_id}/simulations/skill-evidence"
)
def simulate_career_skill_evidence_endpoint(
    career_id: UUID,
    payload: SkillEvidenceSimulationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return simulate_career_skill_evidence(
        db=db,
        user_id=current_user.id,
        career_id=career_id,
        skill_name=payload.skill_name,
        simulated_confidence=payload.simulated_confidence,
    )