from typing import Any


def build_evidence_actions(
    technology_analysis: dict[str, Any],
) -> list[dict[str, Any]]:
    actions = []

    weak_items = technology_analysis.get(
        "evidence_needs_strengthening",
        [],
    )

    for item in weak_items:
        technology = item["technology"]

        actions.append(
            {
                "action_type": "STRENGTHEN_EVIDENCE",
                "technology": technology,
                "priority": "HIGH",
                "reason": (
                    f"CareerPilot found evidence for "
                    f"{technology}, but the current evidence "
                    f"confidence is relatively weak."
                ),
                "recommended_action": (
                    f"Add stronger evidence for {technology} "
                    f"through a relevant assessment, completed "
                    f"project, certification, or experience."
                ),
                "current_evidence_confidence": item.get(
                    "evidence_confidence"
                ),
            }
        )

    return actions


def build_exploration_actions(
    technology_analysis: dict[str, Any],
) -> list[dict[str, Any]]:
    actions = []

    missing_items = technology_analysis.get(
        "missing_evidence",
        [],
    )

    for item in missing_items:
        technology = item["technology"]

        actions.append(
            {
                "action_type": "EXPLORE_MARKET_SIGNAL",
                "technology": technology,
                "priority": "MEDIUM",
                "reason": (
                    f"{technology} appears as an in-demand "
                    f"technology signal for the selected "
                    f"occupation, but no matching evidence "
                    f"exists in the current Career Twin."
                ),
                "recommended_action": (
                    f"Review whether {technology} is relevant "
                    f"to your intended specialization before "
                    f"deciding to learn or demonstrate it."
                ),
            }
        )

    return actions


def build_competency_actions(
    competency_requirements: list[dict[str, Any]],
    limit: int = 5,
) -> list[dict[str, Any]]:
    candidates = [
        item
        for item in competency_requirements
        if item.get("student_measurement_status")
        == "NOT_ASSESSED"
        and item.get("importance") is not None
    ]

    candidates.sort(
        key=lambda item: item["importance"],
        reverse=True,
    )

    actions = []

    for item in candidates[:limit]:
        competency = item["element_name"]

        actions.append(
            {
                "action_type": "ASSESS_COMPETENCY",
                "competency": competency,
                "priority": "HIGH",
                "career_importance": item.get(
                    "importance"
                ),
                "career_level": item.get("level"),
                "reason": (
                    f"{competency} is an important occupational "
                    f"competency for the selected career, but "
                    f"CareerPilot does not currently have a "
                    f"student measurement for it."
                ),
                "recommended_action": (
                    f"Complete an appropriate CareerPilot "
                    f"assessment or provide valid evidence "
                    f"for {competency}."
                ),
            }
        )

    return actions


def build_career_gps(
    gap_analysis: dict[str, Any],
) -> dict[str, Any]:
    technology_analysis = gap_analysis[
        "technology_analysis"
    ]

    competency_requirements = gap_analysis[
        "competency_requirements"
    ]

    evidence_actions = build_evidence_actions(
        technology_analysis
    )

    exploration_actions = build_exploration_actions(
        technology_analysis
    )

    competency_actions = build_competency_actions(
        competency_requirements
    )

    ordered_actions = (
        evidence_actions
        + competency_actions
        + exploration_actions
    )

    for index, action in enumerate(
        ordered_actions,
        start=1,
    ):
        action["sequence"] = index

    return {
        "actions": ordered_actions,
        "summary": {
            "total_actions": len(ordered_actions),
            "strengthen_evidence_actions": len(
                evidence_actions
            ),
            "competency_assessment_actions": len(
                competency_actions
            ),
            "market_signal_exploration_actions": len(
                exploration_actions
            ),
        },
        "methodology_status": "HEURISTIC_V1",
        "interpretation": (
            "Career GPS converts current evidence gaps and "
            "career requirement signals into transparent "
            "next-step suggestions. The sequence is a "
            "heuristic V1 plan and is not yet an optimized "
            "minimum-action path."
        ),
    }