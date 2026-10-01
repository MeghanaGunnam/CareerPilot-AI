from __future__ import annotations

import math
from typing import Any

from backend.app.acif.technology_matching import (
    build_student_skill_index,
    normalize_technology_name,
)


RIASEC_KEYS = (
    "realistic",
    "investigative",
    "artistic",
    "social",
    "enterprising",
    "conventional",
)


def cosine_similarity(
    first: list[float],
    second: list[float],
) -> float | None:
    if len(first) != len(second) or not first:
        return None

    first_norm = math.sqrt(
        sum(value * value for value in first)
    )

    second_norm = math.sqrt(
        sum(value * value for value in second)
    )

    if first_norm == 0.0 or second_norm == 0.0:
        return None

    dot_product = sum(
        a * b
        for a, b in zip(first, second)
    )

    similarity = dot_product / (
        first_norm * second_norm
    )

    return max(
        0.0,
        min(1.0, similarity),
    )


def calculate_riasec_alignment(
    student_profile: dict[str, Any] | None,
    career_profile: dict[str, Any] | None,
) -> float | None:
    if not student_profile or not career_profile:
        return None

    student_vector: list[float] = []
    career_vector: list[float] = []

    for key in RIASEC_KEYS:
        student_value = student_profile.get(key)
        career_value = career_profile.get(key)

        if student_value is None or career_value is None:
            return None

        student_vector.append(float(student_value))
        career_vector.append(float(career_value))

    return cosine_similarity(
        student_vector,
        career_vector,
    )


def calculate_software_alignment(
    skill_states: list[dict[str, Any]],
    software_requirements: list[dict[str, Any]],
) -> dict[str, Any]:
    student_index = build_student_skill_index(
        skill_states
    )

    unique_requirements: dict[
        str,
        dict[str, Any],
    ] = {}

    for requirement in software_requirements:
        normalized = normalize_technology_name(
            requirement.get("workplace_example")
        )

        if not normalized:
            continue

        existing = unique_requirements.get(normalized)

        # Prefer an in-demand record if duplicate normalized
        # technologies occur.
        if existing is None:
            unique_requirements[normalized] = requirement
        elif (
            requirement.get("in_demand")
            and not existing.get("in_demand")
        ):
            unique_requirements[normalized] = requirement

    matched: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []

    confidence_sum = 0.0
    matched_count = 0

    for normalized, requirement in sorted(
        unique_requirements.items()
    ):
        student_skill = student_index.get(
            normalized
        )

        requirement_info = {
            "technology": requirement.get(
                "workplace_example"
            ),
            "normalized_technology": normalized,
            "element_name": requirement.get(
                "element_name"
            ),
            "hot_technology": bool(
                requirement.get("hot_technology")
            ),
            "in_demand": bool(
                requirement.get("in_demand")
            ),
        }

        if student_skill is None:
            missing.append(requirement_info)
            continue

        confidence = float(
            student_skill.get(
                "evidence_confidence"
            )
            or 0.0
        )

        matched_count += 1
        confidence_sum += confidence

        matched.append(
            {
                **requirement_info,
                "student_skill": student_skill.get(
                    "name"
                ),
                "evidence_confidence": round(
                    confidence,
                    4,
                ),
                "estimated_proficiency": (
                    student_skill.get(
                        "estimated_proficiency"
                    )
                ),
                "verified_skill_state": (
                    student_skill.get(
                        "verified_skill_state"
                    )
                ),
                "evidence_families": (
                    student_skill.get(
                        "evidence_families"
                    )
                    or []
                ),
            }
        )

    total_requirements = len(
        unique_requirements
    )

    coverage = (
        matched_count / total_requirements
        if total_requirements
        else None
    )

    evidence_weighted_coverage = (
        confidence_sum / total_requirements
        if total_requirements
        else None
    )

    return {
        "total_software_requirements": (
            total_requirements
        ),
        "matched_requirement_count": (
            matched_count
        ),
        "missing_requirement_count": len(
            missing
        ),
        "coverage": (
            round(coverage, 4)
            if coverage is not None
            else None
        ),
        "evidence_weighted_coverage": (
            round(
                evidence_weighted_coverage,
                4,
            )
            if evidence_weighted_coverage
            is not None
            else None
        ),
        "matched": matched,
        "missing": missing,
    }


def build_career_match_breakdown(
    student_riasec: dict[str, Any] | None,
    career_riasec: dict[str, Any] | None,
    skill_states: list[dict[str, Any]],
    software_requirements: list[
        dict[str, Any]
    ],
) -> dict[str, Any]:
    riasec_alignment = (
        calculate_riasec_alignment(
            student_profile=student_riasec,
            career_profile=career_riasec,
        )
    )

    software_alignment = (
        calculate_software_alignment(
            skill_states=skill_states,
            software_requirements=(
                software_requirements
            ),
        )
    )

    return {
        "riasec_alignment": (
            round(riasec_alignment, 4)
            if riasec_alignment is not None
            else None
        ),
        "software_alignment": (
            software_alignment
        ),
        "final_match_score": None,
        "final_match_score_status": (
            "NOT_CALIBRATED"
        ),
    }