from copy import deepcopy
from typing import Any


SUPPORTED_SIMULATION_TYPES = {
    "ADD_SKILL_EVIDENCE",
}


def _get_skill_name(state: dict[str, Any]) -> str:
    return str(
        state.get("name")
        or state.get("skill_name")
        or ""
    ).strip()


def simulate_add_skill_evidence(
    skill_states: list[dict[str, Any]],
    skill_name: str,
    simulated_confidence: float,
) -> list[dict[str, Any]]:
    simulated_states = deepcopy(skill_states)

    normalized_target = skill_name.strip().lower()

    for state in simulated_states:
        current_name = _get_skill_name(state).lower()

        if current_name == normalized_target:
            current_confidence = state.get(
                "evidence_confidence"
            )

            if current_confidence is None:
                current_confidence = 0.0

            state["evidence_confidence"] = max(
                float(current_confidence),
                float(simulated_confidence),
            )

            state["simulation_status"] = "MODIFIED"

            return simulated_states

    simulated_states.append(
        {
            "name": skill_name,
            "category": None,
            "evidence_confidence": simulated_confidence,
            "estimated_proficiency": None,
            "verified_skill_state": None,
            "evidence_families": ["SIMULATED"],
            "simulation_status": "ADDED",
        }
    )

    return simulated_states


def build_simulation_summary(
    simulation_type: str,
    skill_name: str,
    before_confidence: float | None,
    after_confidence: float,
) -> dict[str, Any]:
    return {
        "simulation_type": simulation_type,
        "skill_name": skill_name,
        "before_evidence_confidence": before_confidence,
        "after_evidence_confidence": after_confidence,
        "database_mutated": False,
        "interpretation": (
            "This is a hypothetical ACIF model-state simulation. "
            "It does not modify the student's real Career Twin and "
            "does not represent a predicted hiring or placement outcome."
        ),
    }
def build_career_simulation_delta(
    before_gap_analysis: dict[str, Any],
    after_gap_analysis: dict[str, Any],
    before_readiness: dict[str, Any],
    after_readiness: dict[str, Any],
) -> dict[str, Any]:
    before_technology = before_gap_analysis[
        "technology_analysis"
    ]
    after_technology = after_gap_analysis[
        "technology_analysis"
    ]

    before_summary = before_technology["summary"]
    after_summary = after_technology["summary"]

    before_coverage = before_readiness[
        "technology_evidence_coverage"
    ].get("score")

    after_coverage = after_readiness[
        "technology_evidence_coverage"
    ].get("score")

    before_strength = before_readiness[
        "technology_evidence_strength"
    ].get("score")

    after_strength = after_readiness[
        "technology_evidence_strength"
    ].get("score")

    return {
        "technology_gap_changes": {
            "strong_evidence_count": {
                "before": before_summary.get(
                    "strong_evidence_count",
                    0,
                ),
                "after": after_summary.get(
                    "strong_evidence_count",
                    0,
                ),
            },
            "evidence_needs_strengthening_count": {
                "before": before_summary.get(
                    "evidence_needs_strengthening_count",
                    0,
                ),
                "after": after_summary.get(
                    "evidence_needs_strengthening_count",
                    0,
                ),
            },
            "missing_evidence_count": {
                "before": before_summary.get(
                    "missing_evidence_count",
                    0,
                ),
                "after": after_summary.get(
                    "missing_evidence_count",
                    0,
                ),
            },
        },
        "readiness_changes": {
            "technology_evidence_coverage": {
                "before": before_coverage,
                "after": after_coverage,
                "delta": (
                    round(
                        after_coverage - before_coverage,
                        4,
                    )
                    if before_coverage is not None
                    and after_coverage is not None
                    else None
                ),
            },
            "technology_evidence_strength": {
                "before": before_strength,
                "after": after_strength,
                "delta": (
                    round(
                        after_strength - before_strength,
                        4,
                    )
                    if before_strength is not None
                    and after_strength is not None
                    else None
                ),
            },
        },
        "interpretation": (
            "These changes describe differences between "
            "the current ACIF model state and a hypothetical "
            "model state. They are not causal estimates of "
            "employment, hiring, or placement outcomes."
        ),
    }