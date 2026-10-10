from __future__ import annotations

import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.acif.engine import calculate_all_skill_states
from backend.app.acif.technology_matching import normalize_technology_name
from backend.app.assessments.models import Assessment
from backend.app.career_twin.service import (
    get_career_twin,
    get_latest_snapshot,
)
from backend.app.careers.models import (
    Career,
    CareerSkillRequirement,
    CareerSoftwareRequirement,
)
from backend.app.skills.models import (
    Skill,
    SkillCompetencyMapping,
)
from backend.app.students.service import get_user_primary_career_goal


def get_my_assessment_recommendations(db: Session, user_id: uuid.UUID) -> dict[str, Any]:
    goal = get_user_primary_career_goal(db=db, user_id=user_id)
    if goal is None or not goal.onet_soc_code:
        raise HTTPException(status_code=404, detail="Mapped primary career goal not found.")
    career = db.scalar(select(Career).where(Career.onet_soc_code == goal.onet_soc_code))
    if career is None:
        raise HTTPException(status_code=404, detail="Primary career goal occupation not found.")
    result = get_career_assessment_recommendations(db, user_id, career.id)
    result["career_goal_id"] = goal.id
    return result


def get_measured_skill_ids(db: Session, user_id: uuid.UUID) -> set[str]:
    twin = get_career_twin(db=db, user_id=user_id)
    snapshot = get_latest_snapshot(db=db, career_twin_id=twin.id) if twin else None
    if snapshot is None:
        return set()
    # ACIF derives this value only from assessment strengths, including zero.
    return {
        str(state["skill_id"])
        for state in calculate_all_skill_states(snapshot.state_data)
        if state.get("estimated_proficiency") is not None
    }


def get_technology_recommendations(db: Session, user_id: uuid.UUID, career: Career) -> list[dict[str, Any]]:
    measured = get_measured_skill_ids(db, user_id)
    requirements = db.scalars(select(CareerSoftwareRequirement).where(
        CareerSoftwareRequirement.career_id == career.id,
        CareerSoftwareRequirement.in_demand.is_(True),
    )).all()
    by_name: dict[str, Any] = {}
    for requirement in sorted(requirements, key=lambda row: (row.workplace_example, str(row.id))):
        by_name.setdefault(normalize_technology_name(requirement.workplace_example), requirement)
    rows = db.execute(select(Assessment, Skill).join(Skill, Skill.id == Assessment.skill_id)
                      .where(Assessment.is_active.is_(True))).all()
    result = []
    for assessment, skill in rows:
        normalized = normalize_technology_name(skill.canonical_name)
        requirement = by_name.get(normalized)
        if normalized not in {"python", "sql"} or requirement is None or str(skill.id) in measured:
            continue
        result.append({
            "assessment_id": assessment.id, "skill_id": skill.id,
            "skill_name": skill.canonical_name, "title": assessment.title,
            "description": assessment.description, "difficulty": assessment.difficulty,
            "version": assessment.version, "career_id": career.id,
            "career_title": career.title, "onet_soc_code": career.onet_soc_code,
            "competency": None, "recommendation_type": "SOFTWARE_SIGNAL",
            "software_signal": {
                "requirement_id": requirement.id, "workplace_example": requirement.workplace_example,
                "canonical_technology": normalized, "in_demand": requirement.in_demand,
                "hot_technology": requirement.hot_technology, "onet_version": requirement.onet_version,
                "mapping_type": "EXACT_NORMALIZED_TECHNOLOGY",
            },
            "recommendation_status": "RECOMMENDED",
            "reason": "This assessment samples knowledge of an exactly mapped in-demand occupational technology. "
                      "No assessment-derived measurement exists for this skill in the current Career Twin. "
                      "The software signal is not an O*NET competency or a proficiency requirement.",
        })
    return sorted(result, key=lambda row: (row["skill_name"], row["title"], str(row["assessment_id"])))


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
        # Python/SQL selection must be supported by an exact in-demand software
        # requirement, never inferred from a broad competency mapping.
        if normalize_technology_name(skill.canonical_name) in {"python", "sql"}:
            continue
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

    recommendations.extend(get_technology_recommendations(db, user_id, career))

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
            "explicitly mapped to O*NET competencies or exact normalized in-demand occupational software "
            "for the selected occupation and for which "
            "the current Career Twin does not already "
            "contain assessment-derived measurement "
            "evidence. O*NET importance and level are "
            "kept as separate scales. Software signals do not establish competency or universal proficiency."
        ),
    }
