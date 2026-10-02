from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.skills.models import (
    Skill,
    SkillCompetencyMapping,
)


def normalize_name(value: str | None) -> str:
    if not value:
        return ""

    return " ".join(
        value.strip().lower().split()
    )


def get_active_competency_mappings(
    db: Session,
    competency_element_ids: list[str],
) -> list[dict[str, Any]]:
    if not competency_element_ids:
        return []

    rows = db.execute(
        select(
            SkillCompetencyMapping,
            Skill,
        )
        .join(
            Skill,
            Skill.id
            == SkillCompetencyMapping.skill_id,
        )
        .where(
            SkillCompetencyMapping.is_active.is_(True),
            SkillCompetencyMapping.onet_element_id.in_(
                competency_element_ids
            ),
        )
    ).all()

    mappings: list[dict[str, Any]] = []

    for mapping, skill in rows:
        mappings.append(
            {
                "skill_id": str(skill.id),
                "skill_name": skill.canonical_name,
                "onet_element_id": (
                    mapping.onet_element_id
                ),
                "onet_element_name": (
                    mapping.onet_element_name
                ),
                "mapping_type": mapping.mapping_type,
                "mapping_version": (
                    mapping.mapping_version
                ),
                "rationale": mapping.rationale,
            }
        )

    return mappings


def find_competency_measurement(
    competency_element_id: str,
    competency_name: str,
    skill_states: list[dict[str, Any]],
    mappings: list[dict[str, Any]],
) -> dict[str, Any] | None:
    relevant_mappings = [
        mapping
        for mapping in mappings
        if mapping["onet_element_id"]
        == competency_element_id
    ]

    if not relevant_mappings:
        return None

    mapped_skills = {
        normalize_name(mapping["skill_name"]): mapping
        for mapping in relevant_mappings
    }

    candidates: list[dict[str, Any]] = []

    for state in skill_states:
        skill_name = normalize_name(
            state.get("name")
        )

        mapping = mapped_skills.get(skill_name)

        if mapping is None:
            continue

        estimated_proficiency = state.get(
            "estimated_proficiency"
        )

        # Resume/project/certification evidence alone must
        # not mark an occupational competency as measured.
        # A measurement requires assessment-derived
        # proficiency from the mapped concrete skill.
        if estimated_proficiency is None:
            continue

        candidates.append(
            {
                "skill_name": state.get("name"),
                "estimated_proficiency": (
                    estimated_proficiency
                ),
                "evidence_confidence": state.get(
                    "evidence_confidence"
                ),
                "verified_skill_state": state.get(
                    "verified_skill_state"
                ),
                "evidence_families": (
                    state.get("evidence_families")
                    or []
                ),
                "mapping_type": mapping[
                    "mapping_type"
                ],
                "mapping_version": mapping[
                    "mapping_version"
                ],
                "mapping_rationale": mapping[
                    "rationale"
                ],
            }
        )

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: (
            item["estimated_proficiency"]
            if item["estimated_proficiency"]
            is not None
            else -1
        ),
        reverse=True,
    )

    strongest = candidates[0]

    return {
        "status": "MEASURED",
        "measurement_type": (
            "MAPPED_SKILL_ASSESSMENT"
        ),
        "competency_element_id": (
            competency_element_id
        ),
        "competency": competency_name,
        "supporting_skill": strongest[
            "skill_name"
        ],
        "estimated_proficiency": strongest[
            "estimated_proficiency"
        ],
        "evidence_confidence": strongest[
            "evidence_confidence"
        ],
        "verified_skill_state": strongest[
            "verified_skill_state"
        ],
        "evidence_families": strongest[
            "evidence_families"
        ],
        "mapping_type": strongest[
            "mapping_type"
        ],
        "mapping_version": strongest[
            "mapping_version"
        ],
        "mapping_rationale": strongest[
            "mapping_rationale"
        ],
        "interpretation": (
            "CareerPilot found assessment-derived "
            "measurement evidence from a mapped technical "
            "skill. The mapping indicates that this skill "
            "contributes evidence toward the broader O*NET "
            "occupational competency. It must not be "
            "interpreted as complete measurement of that "
            "competency."
        ),
    }


def build_competency_measurements(
    db: Session,
    competencies: list[dict[str, str]],
    skill_states: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    element_ids = list(
        {
            competency["element_id"]
            for competency in competencies
            if competency.get("element_id")
        }
    )

    mappings = get_active_competency_mappings(
        db=db,
        competency_element_ids=element_ids,
    )

    measurements: dict[
        str,
        dict[str, Any],
    ] = {}

    for competency in competencies:
        element_id = competency.get("element_id")
        element_name = competency.get("element_name")

        if not element_id or not element_name:
            continue

        measurement = find_competency_measurement(
            competency_element_id=element_id,
            competency_name=element_name,
            skill_states=skill_states,
            mappings=mappings,
        )

        if measurement is not None:
            measurements[element_id] = measurement

    return measurements