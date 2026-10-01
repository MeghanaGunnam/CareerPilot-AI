from typing import Any


def calculate_evidence_readiness(
    technology_analysis: dict[str, Any],
) -> dict[str, Any]:
    summary = technology_analysis.get("summary", {})

    strong = summary.get(
        "strong_evidence_count",
        0,
    )

    weak = summary.get(
        "evidence_needs_strengthening_count",
        0,
    )

    missing = summary.get(
        "missing_evidence_count",
        0,
    )

    total = strong + weak + missing

    if total == 0:
        return {
            "score": None,
            "status": "INSUFFICIENT_DATA",
            "strong_evidence_count": strong,
            "weak_evidence_count": weak,
            "missing_evidence_count": missing,
            "total_market_signals": total,
        }

    # This measures evidence coverage, not skill proficiency.
    evidenced = strong + weak

    evidence_coverage = evidenced / total

    return {
        "score": round(evidence_coverage, 4),
        "status": "AVAILABLE",
        "strong_evidence_count": strong,
        "weak_evidence_count": weak,
        "missing_evidence_count": missing,
        "total_market_signals": total,
        "interpretation": (
            "Share of the selected career's in-demand "
            "technology signals for which the current "
            "Career Twin contains some evidence. This is "
            "not a proficiency or employability score."
        ),
    }


def calculate_evidence_strength(
    technology_analysis: dict[str, Any],
) -> dict[str, Any]:
    matched = (
        technology_analysis.get(
            "strong_evidence",
            [],
        )
        + technology_analysis.get(
            "evidence_needs_strengthening",
            [],
        )
    )

    if not matched:
        return {
            "score": None,
            "status": "INSUFFICIENT_DATA",
        }

    confidences = [
        item.get("evidence_confidence")
        for item in matched
        if item.get("evidence_confidence") is not None
    ]

    if not confidences:
        return {
            "score": None,
            "status": "INSUFFICIENT_DATA",
        }

    score = sum(confidences) / len(confidences)

    return {
        "score": round(score, 4),
        "status": "AVAILABLE",
        "evidenced_technology_count": len(
            confidences
        ),
        "interpretation": (
            "Average ACIF evidence confidence across "
            "matched in-demand technologies. It represents "
            "strength of supporting evidence, not technical "
            "proficiency."
        ),
    }


def calculate_competency_measurement_coverage(
    competency_requirements: list[dict[str, Any]],
) -> dict[str, Any]:
    total = len(competency_requirements)

    measured = sum(
        1
        for item in competency_requirements
        if item.get(
            "student_measurement_status"
        ) != "NOT_ASSESSED"
    )

    if total == 0:
        return {
            "score": None,
            "status": "INSUFFICIENT_DATA",
        }

    return {
        "score": round(measured / total, 4),
        "status": "AVAILABLE",
        "measured_competency_count": measured,
        "total_competency_count": total,
        "interpretation": (
            "Coverage of occupational competencies for "
            "which CareerPilot has an actual student "
            "measurement. It is not a competency score."
        ),
    }


def build_readiness_dimensions(
    gap_analysis: dict[str, Any],
    riasec_alignment: float | None,
) -> dict[str, Any]:
    technology_analysis = gap_analysis[
        "technology_analysis"
    ]

    competency_requirements = gap_analysis[
        "competency_requirements"
    ]

    return {
        "interest_alignment": {
            "score": riasec_alignment,
            "status": (
                "AVAILABLE"
                if riasec_alignment is not None
                else "INSUFFICIENT_DATA"
            ),
            "interpretation": (
                "RIASEC interest alignment with the "
                "selected career. It does not predict "
                "employment success."
            ),
        },
        "technology_evidence_coverage": (
            calculate_evidence_readiness(
                technology_analysis
            )
        ),
        "technology_evidence_strength": (
            calculate_evidence_strength(
                technology_analysis
            )
        ),
        "competency_measurement_coverage": (
            calculate_competency_measurement_coverage(
                competency_requirements
            )
        ),
        "overall_readiness_score": None,
        "overall_readiness_status": "NOT_CALIBRATED",
        "interpretation": (
            "CareerPilot reports readiness dimensions "
            "separately. No overall employability or "
            "placement probability is produced because "
            "the required weighting and outcome model "
            "have not been validated."
        ),
    }