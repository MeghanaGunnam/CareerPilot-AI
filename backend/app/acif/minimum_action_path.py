from typing import Any


MAX_PATH_ACTIONS = 5


def _evidence_priority(
    action: dict[str, Any],
) -> float:
    confidence = action.get(
        "current_evidence_confidence"
    )

    if confidence is None:
        return 0.0

    # Lower confidence means a larger evidence gap.
    return 1.0 - confidence


def _competency_priority(
    action: dict[str, Any],
) -> float:
    importance = action.get("career_importance")

    if importance is None:
        return 0.0

    # O*NET Importance uses a 1–5 scale.
    return max(
        0.0,
        min(
            1.0,
            (importance - 1.0) / 4.0,
        ),
    )


def build_minimum_action_path(
    career_gps: dict[str, Any],
    max_actions: int = MAX_PATH_ACTIONS,
) -> dict[str, Any]:
    actions = career_gps.get("actions", [])

    evidence_actions = [
        action
        for action in actions
        if action.get("action_type")
        == "STRENGTHEN_EVIDENCE"
    ]

    competency_actions = [
        action
        for action in actions
        if action.get("action_type")
        == "ASSESS_COMPETENCY"
    ]

    evidence_actions.sort(
        key=_evidence_priority,
        reverse=True,
    )

    competency_actions.sort(
        key=_competency_priority,
        reverse=True,
    )

    selected: list[dict[str, Any]] = []

    # First prioritize evidence already associated
    # with the student's current Career Twin.
    for action in evidence_actions:
        if len(selected) >= max_actions:
            break

        selected.append(
            {
                **action,
                "selection_reason": (
                    "Existing career-relevant evidence "
                    "was found, but its confidence can "
                    "be strengthened."
                ),
            }
        )

    # Fill remaining slots with high-importance
    # occupational competency assessments.
    for action in competency_actions:
        if len(selected) >= max_actions:
            break

        selected.append(
            {
                **action,
                "selection_reason": (
                    "This is a high-importance occupational "
                    "competency that has not yet been "
                    "measured for the student."
                ),
            }
        )

    for index, action in enumerate(
        selected,
        start=1,
    ):
        action["path_step"] = index

    return {
        "path": selected,
        "summary": {
            "selected_action_count": len(selected),
            "available_gps_action_count": len(actions),
        },
        "methodology_status": "HEURISTIC_V1",
        "optimization_status": "NOT_OPTIMIZED",
        "interpretation": (
            "This path is a deterministic shortlist of "
            "high-priority actions from Career GPS. It is "
            "not yet a mathematically optimized minimum "
            "action path because action costs, prerequisite "
            "relationships, specialization relevance, and "
            "validated outcome gains are not yet modeled."
        ),
    }