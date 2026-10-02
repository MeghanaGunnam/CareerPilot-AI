from __future__ import annotations

import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.acif.engine import calculate_all_skill_states
from backend.app.assessments.models import Assessment
from backend.app.career_twin.service import (
    get_career_twin,
    get_latest_snapshot,
)
from backend.app.careers.models import (
    Career,
    CareerSkillRequirement,
)
from backend.app.skills.models import (
    Skill,
    SkillCompetencyMapping,
)


def get_career_or_404(
    db: Session,
    career_id: uuid.UUID,
) -> Career:
    career = db.get(Career, career_id)

    if career is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Career not found.",
        )

    return career


def get_career_competencies(
    db: Session,
    career_id: uuid.UUID,
) -> dict[str, dict[str, Any]]:
    rows = list(
        db.scalars(
            select(CareerSkillRequirement).where(
                CareerSkillRequirement.career_id
                == career_id,
                CareerSkillRequirement.not_relevant
                .is_not(True),
                CareerSkillRequirement.recommend_suppress
                .is_not(True),
            )
        ).all()
    )

    competencies: dict[str, dict[str, Any]] = {}

    for row in rows:
        key = row.element_id

        if key not in competencies:
            competencies[key] = {
                "element_id": row.element_id,
                "element_name": row.element_name,
                "skill_type": row.skill_type,
                "importance": None,
                "level": None,
            }

        if row.scale_id == "IM":
            competencies[key]["importance"] = (
                row.data_value
            )

        elif row.scale_id == "LV":
            competencies[key]["level"] = (
                row.data_value
            )

    return competencies


def get_measured_competency_ids(
    db: Session,
    user_id: uuid.UUID,
) -> set[str]:
    career_twin = get_career_twin(
        db=db,
        user_id=user_id,
    )

    if career_twin is None:
        return set()

    snapshot = get_latest_snapshot(
        db=db,
        career_twin_id=career_twin.id,
    )

    if snapshot is None:
        return set()

    skill_states = calculate_all_skill_states(
        snapshot.state_data
    )

    measured_skill_ids = {
        str(state["skill_id"])
        for state in skill_states
        if state.get("estimated_proficiency")
        is not None
    }

    if not measured_skill_ids:
        return set()

    mappings = list(
        db.scalars(
            select(SkillCompetencyMapping).where(
                SkillCompetencyMapping.is_active.is_(
                    True
                )
            )
        ).all()
    )

    return {
        mapping.onet_element_id
        for mapping in mappings
        if str(mapping.skill_id)
        in measured_skill_ids
    }

def get_career_assessment_recommendations(
    db: Session,
    user_id: uuid.UUID,
    career_id: uuid.UUID,
) -> dict[str, Any]:
    career = get_career_or_404(
        db=db,
        career_id=career_id,
    )

    competencies = get_career_competencies(
        db=db,
        career_id=career.id,
    )

    measured_competency_ids = (
        get_measured_competency_ids(
            db=db,
            user_id=user_id,
        )
    )

    rows = db.execute(
        select(
            Assessment,
            Skill,
            SkillCompetencyMapping,
        )
        .join(
            Skill,
            Skill.id == Assessment.skill_id,
        )
        .join(
            SkillCompetencyMapping,
            SkillCompetencyMapping.skill_id
            == Skill.id,
        )
        .where(
            Assessment.is_active.is_(True),
            SkillCompetencyMapping.is_active
            .is_(True),
        )
    ).all()

    recommendations: list[dict[str, Any]] = []

    for assessment, skill, mapping in rows:
        competency = competencies.get(
            mapping.onet_element_id
        )

        if competency is None:
            continue

        if (
            mapping.onet_element_id
            in measured_competency_ids
        ):
            continue

        recommendations.append(
            {
                "assessment_id": assessment.id,
                "skill_id": skill.id,
                "skill_name": skill.canonical_name,
                "title": assessment.title,
                "description": (
                    assessment.description
                ),
                "difficulty": assessment.difficulty,
                "version": assessment.version,
                "career_id": career.id,
                "career_title": career.title,
                "onet_soc_code": (
                    career.onet_soc_code
                ),
                "competency": {
                    "element_id": (
                        competency["element_id"]
                    ),
                    "element_name": (
                        competency["element_name"]
                    ),
                    "skill_type": (
                        competency["skill_type"]
                    ),
                    "importance": (
                        competency["importance"]
                    ),
                    "level": competency["level"],
                    "mapping_type": (
                        mapping.mapping_type
                    ),
                    "mapping_version": (
                        mapping.mapping_version
                    ),
                    "mapping_rationale": (
                        mapping.rationale
                    ),
                },
                "recommendation_status": (
                    "RECOMMENDED"
                ),
                "reason": (
                    "This assessment measures a "
                    "CareerPilot skill mapped to an "
                    "O*NET competency relevant to the "
                    "selected occupation. CareerPilot "
                    "does not currently have "
                    "assessment-derived measurement "
                    "evidence for that competency."
                ),
            }
        )

    recommendations.sort(
        key=lambda item: (
            item["competency"]["importance"]
            if item["competency"]["importance"]
            is not None
            else -1
        ),
        reverse=True,
    )

    return {
        "career_id": career.id,
        "career_title": career.title,
        "onet_soc_code": career.onet_soc_code,
        "recommended_count": len(
            recommendations
        ),
        "recommendations": recommendations,
        "interpretation": (
            "Recommendations are based on active "
            "CareerPilot assessments whose skills are "
            "explicitly mapped to O*NET competencies "
            "for the selected occupation and for which "
            "the current Career Twin does not already "
            "contain assessment-derived measurement "
            "evidence. O*NET importance and level are "
            "kept as separate scales."
        ),
    }