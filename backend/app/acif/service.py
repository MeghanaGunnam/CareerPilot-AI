from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.acif.career_gps import build_career_gps
from backend.app.acif.career_matching import build_career_match_breakdown
from backend.app.acif.engine import (
    ACIF_MODEL_VERSION,
    calculate_all_skill_states,
)
from backend.app.acif.gap_analysis import build_gap_analysis
from backend.app.acif.minimum_action_path import build_minimum_action_path
from backend.app.acif.readiness import build_readiness_dimensions
from backend.app.acif.simulator import (
    build_career_simulation_delta,
    build_simulation_summary,
    simulate_add_skill_evidence,
)
from backend.app.career_twin.service import (
    get_career_twin,
    get_latest_snapshot,
)
from backend.app.careers.models import (
    Career,
    CareerSkillRequirement,
    CareerSoftwareRequirement,
)


def get_current_twin_snapshot(
    db: Session,
    user_id: UUID,
):
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
            detail=(
                "Career Twin does not contain "
                "a snapshot yet."
            ),
        )

    return twin, snapshot


def get_current_skill_states(
    db: Session,
    user_id: UUID,
) -> dict:
    twin, snapshot = get_current_twin_snapshot(
        db=db,
        user_id=user_id,
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


def get_career_match(
    db: Session,
    user_id: UUID,
    career_id: UUID,
) -> dict:
    twin, snapshot = get_current_twin_snapshot(
        db=db,
        user_id=user_id,
    )

    career = db.scalar(
        select(Career).where(
            Career.id == career_id
        )
    )

    if career is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Career not found.",
        )

    student_riasec = snapshot.state_data.get(
        "riasec"
    )

    career_riasec = None

    if career.riasec_profile is not None:
        career_riasec = {
            "realistic": career.riasec_profile.realistic,
            "investigative": career.riasec_profile.investigative,
            "artistic": career.riasec_profile.artistic,
            "social": career.riasec_profile.social,
            "enterprising": career.riasec_profile.enterprising,
            "conventional": career.riasec_profile.conventional,
        }

    skill_states = calculate_all_skill_states(
        snapshot.state_data
    )

    software_rows = db.scalars(
        select(CareerSoftwareRequirement).where(
            CareerSoftwareRequirement.career_id
            == career.id,
            CareerSoftwareRequirement.in_demand.is_(True),
        )
    ).all()

    software_requirements = [
        {
            "workplace_example": row.workplace_example,
            "element_name": row.element_name,
            "hot_technology": row.hot_technology,
            "in_demand": row.in_demand,
        }
        for row in software_rows
    ]

    breakdown = build_career_match_breakdown(
        student_riasec=student_riasec,
        career_riasec=career_riasec,
        skill_states=skill_states,
        software_requirements=software_requirements,
    )

    return {
        "career_twin_id": str(twin.id),
        "snapshot_version": snapshot.version,
        "model_version": ACIF_MODEL_VERSION,
        "career": {
            "id": str(career.id),
            "onet_soc_code": career.onet_soc_code,
            "title": career.title,
            "job_zone": career.job_zone,
            "onet_version": career.onet_version,
        },
        **breakdown,
    }


def get_career_gap_analysis(
    db: Session,
    user_id: UUID,
    career_id: UUID,
) -> dict:
    career_match = get_career_match(
        db=db,
        user_id=user_id,
        career_id=career_id,
    )

    competency_rows = db.scalars(
        select(CareerSkillRequirement).where(
            CareerSkillRequirement.career_id
            == career_id
        )
    ).all()

    competency_data = [
        {
            "skill_type": row.skill_type,
            "element_id": row.element_id,
            "element_name": row.element_name,
            "scale_id": row.scale_id,
            "scale_name": row.scale_name,
            "data_value": row.data_value,
            "not_relevant": row.not_relevant,
            "recommend_suppress": row.recommend_suppress,
        }
        for row in competency_rows
    ]

    gap_analysis = build_gap_analysis(
        software_alignment=career_match[
            "software_alignment"
        ],
        competency_rows=competency_data,
    )

    return {
        "career_twin_id": career_match[
            "career_twin_id"
        ],
        "snapshot_version": career_match[
            "snapshot_version"
        ],
        "model_version": career_match[
            "model_version"
        ],
        "career": career_match["career"],
        "gap_analysis": gap_analysis,
    }


def get_career_readiness(
    db: Session,
    user_id: UUID,
    career_id: UUID,
) -> dict:
    career_match = get_career_match(
        db=db,
        user_id=user_id,
        career_id=career_id,
    )

    gap_result = get_career_gap_analysis(
        db=db,
        user_id=user_id,
        career_id=career_id,
    )

    readiness = build_readiness_dimensions(
        gap_analysis=gap_result["gap_analysis"],
        riasec_alignment=career_match.get(
            "riasec_alignment"
        ),
    )

    return {
        "career_twin_id": career_match[
            "career_twin_id"
        ],
        "snapshot_version": career_match[
            "snapshot_version"
        ],
        "model_version": career_match[
            "model_version"
        ],
        "career": career_match["career"],
        "readiness": readiness,
    }


def get_career_gps(
    db: Session,
    user_id: UUID,
    career_id: UUID,
) -> dict:
    gap_result = get_career_gap_analysis(
        db=db,
        user_id=user_id,
        career_id=career_id,
    )

    gps = build_career_gps(
        gap_analysis=gap_result["gap_analysis"],
    )

    return {
        "career_twin_id": gap_result[
            "career_twin_id"
        ],
        "snapshot_version": gap_result[
            "snapshot_version"
        ],
        "model_version": gap_result[
            "model_version"
        ],
        "career": gap_result["career"],
        "career_gps": gps,
    }


def get_minimum_action_path(
    db: Session,
    user_id: UUID,
    career_id: UUID,
) -> dict:
    gps_result = get_career_gps(
        db=db,
        user_id=user_id,
        career_id=career_id,
    )

    minimum_path = build_minimum_action_path(
        career_gps=gps_result["career_gps"],
    )

    return {
        "career_twin_id": gps_result[
            "career_twin_id"
        ],
        "snapshot_version": gps_result[
            "snapshot_version"
        ],
        "model_version": gps_result[
            "model_version"
        ],
        "career": gps_result["career"],
        "minimum_action_path": minimum_path,
    }


def simulate_skill_evidence(
    db: Session,
    user_id: UUID,
    skill_name: str,
    simulated_confidence: float,
) -> dict:
    if not 0.0 <= simulated_confidence <= 1.0:
        raise ValueError(
            "simulated_confidence must be between 0.0 and 1.0"
        )

    current_states = get_current_skill_states(
        db=db,
        user_id=user_id,
    )

    skill_states = current_states["skills"]

    normalized_target = skill_name.strip().lower()

    before_confidence = None

    for state in skill_states:
        current_name = str(
            state.get("name")
            or state.get("skill_name")
            or ""
        ).strip().lower()

        if current_name == normalized_target:
            before_confidence = state.get(
                "evidence_confidence"
            )
            break

    simulated_states = simulate_add_skill_evidence(
        skill_states=skill_states,
        skill_name=skill_name,
        simulated_confidence=simulated_confidence,
    )

    simulated_skill = next(
        (
            state
            for state in simulated_states
            if str(
                state.get("name")
                or state.get("skill_name")
                or ""
            ).strip().lower()
            == normalized_target
        ),
        None,
    )

    actual_after_confidence = (
        simulated_skill.get("evidence_confidence")
        if simulated_skill is not None
        else simulated_confidence
    )

    summary = build_simulation_summary(
        simulation_type="ADD_SKILL_EVIDENCE",
        skill_name=skill_name,
        before_confidence=before_confidence,
        after_confidence=actual_after_confidence,
    )

    return {
        "model_version": current_states[
            "model_version"
        ],
        "simulation": summary,
        "before": {
            "skill_name": skill_name,
            "evidence_confidence": before_confidence,
        },
        "after": simulated_skill,
    }
def simulate_career_skill_evidence(
    db: Session,
    user_id: UUID,
    career_id: UUID,
    skill_name: str,
    simulated_confidence: float,
) -> dict:
    if not 0.0 <= simulated_confidence <= 1.0:
        raise ValueError(
            "simulated_confidence must be between 0.0 and 1.0"
        )

    twin, snapshot = get_current_twin_snapshot(
        db=db,
        user_id=user_id,
    )

    career = db.scalar(
        select(Career).where(
            Career.id == career_id
        )
    )

    if career is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Career not found.",
        )

    current_skill_states = calculate_all_skill_states(
        snapshot.state_data
    )

    normalized_target = skill_name.strip().lower()

    before_confidence = None

    for state in current_skill_states:
        current_name = str(
            state.get("name")
            or state.get("skill_name")
            or ""
        ).strip().lower()

        if current_name == normalized_target:
            before_confidence = state.get(
                "evidence_confidence"
            )
            break

    simulated_skill_states = simulate_add_skill_evidence(
        skill_states=current_skill_states,
        skill_name=skill_name,
        simulated_confidence=simulated_confidence,
    )

    simulated_skill = next(
        (
            state
            for state in simulated_skill_states
            if str(
                state.get("name")
                or state.get("skill_name")
                or ""
            ).strip().lower()
            == normalized_target
        ),
        None,
    )

    actual_after_confidence = (
        simulated_skill.get("evidence_confidence")
        if simulated_skill is not None
        else simulated_confidence
    )

    student_riasec = snapshot.state_data.get(
        "riasec"
    )

    career_riasec = None

    if career.riasec_profile is not None:
        career_riasec = {
            "realistic": career.riasec_profile.realistic,
            "investigative": career.riasec_profile.investigative,
            "artistic": career.riasec_profile.artistic,
            "social": career.riasec_profile.social,
            "enterprising": career.riasec_profile.enterprising,
            "conventional": career.riasec_profile.conventional,
        }

    software_rows = db.scalars(
        select(CareerSoftwareRequirement).where(
            CareerSoftwareRequirement.career_id
            == career.id,
            CareerSoftwareRequirement.in_demand.is_(True),
        )
    ).all()

    software_requirements = [
        {
            "workplace_example": row.workplace_example,
            "element_name": row.element_name,
            "hot_technology": row.hot_technology,
            "in_demand": row.in_demand,
        }
        for row in software_rows
    ]

    before_match = build_career_match_breakdown(
        student_riasec=student_riasec,
        career_riasec=career_riasec,
        skill_states=current_skill_states,
        software_requirements=software_requirements,
    )

    after_match = build_career_match_breakdown(
        student_riasec=student_riasec,
        career_riasec=career_riasec,
        skill_states=simulated_skill_states,
        software_requirements=software_requirements,
    )

    competency_rows = db.scalars(
        select(CareerSkillRequirement).where(
            CareerSkillRequirement.career_id
            == career.id
        )
    ).all()

    competency_data = [
        {
            "skill_type": row.skill_type,
            "element_id": row.element_id,
            "element_name": row.element_name,
            "scale_id": row.scale_id,
            "scale_name": row.scale_name,
            "data_value": row.data_value,
            "not_relevant": row.not_relevant,
            "recommend_suppress": row.recommend_suppress,
        }
        for row in competency_rows
    ]

    before_gap = build_gap_analysis(
        software_alignment=before_match[
            "software_alignment"
        ],
        competency_rows=competency_data,
    )

    after_gap = build_gap_analysis(
        software_alignment=after_match[
            "software_alignment"
        ],
        competency_rows=competency_data,
    )

    before_readiness = build_readiness_dimensions(
        gap_analysis=before_gap,
        riasec_alignment=before_match.get(
            "riasec_alignment"
        ),
    )

    after_readiness = build_readiness_dimensions(
        gap_analysis=after_gap,
        riasec_alignment=after_match.get(
            "riasec_alignment"
        ),
    )

    delta = build_career_simulation_delta(
        before_gap_analysis=before_gap,
        after_gap_analysis=after_gap,
        before_readiness=before_readiness,
        after_readiness=after_readiness,
    )

    simulation_summary = build_simulation_summary(
        simulation_type="ADD_SKILL_EVIDENCE",
        skill_name=skill_name,
        before_confidence=before_confidence,
        after_confidence=actual_after_confidence,
    )

    return {
        "career_twin_id": str(twin.id),
        "snapshot_version": snapshot.version,
        "model_version": ACIF_MODEL_VERSION,
        "career": {
            "id": str(career.id),
            "onet_soc_code": career.onet_soc_code,
            "title": career.title,
            "job_zone": career.job_zone,
            "onet_version": career.onet_version,
        },
        "simulation": simulation_summary,
        "before": {
            "skill_evidence_confidence": before_confidence,
            "gap_analysis": before_gap,
            "readiness": before_readiness,
        },
        "after": {
            "skill_evidence_confidence": (
                actual_after_confidence
            ),
            "gap_analysis": after_gap,
            "readiness": after_readiness,
        },
        "delta": delta,
        "database_mutated": False,
    }