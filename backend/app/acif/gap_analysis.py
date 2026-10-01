from typing import Any


STRONG_EVIDENCE_THRESHOLD = 0.70


def classify_technology_match(
    evidence_confidence: float | None,
) -> str:
    if evidence_confidence is None:
        return "MISSING_EVIDENCE"

    if evidence_confidence >= STRONG_EVIDENCE_THRESHOLD:
        return "STRONG_EVIDENCE"

    return "EVIDENCE_NEEDS_STRENGTHENING"


def build_technology_gap_analysis(
    software_alignment: dict[str, Any],
) -> dict[str, Any]:
    strong_evidence = []
    weak_evidence = []
    missing_evidence = []

    for item in software_alignment.get("matched", []):
        confidence = item.get("evidence_confidence")

        gap_status = classify_technology_match(
            confidence
        )

        result = {
            **item,
            "gap_status": gap_status,
        }

        if gap_status == "STRONG_EVIDENCE":
            strong_evidence.append(result)
        else:
            weak_evidence.append(result)

    for item in software_alignment.get("missing", []):
        missing_evidence.append(
            {
                **item,
                "gap_status": "MISSING_EVIDENCE",
                "interpretation": (
                    "No matching evidence was found in the "
                    "current Career Twin. This does not prove "
                    "that the student lacks this technology."
                ),
            }
        )

    return {
        "strong_evidence": strong_evidence,
        "evidence_needs_strengthening": weak_evidence,
        "missing_evidence": missing_evidence,
        "summary": {
            "strong_evidence_count": len(
                strong_evidence
            ),
            "evidence_needs_strengthening_count": len(
                weak_evidence
            ),
            "missing_evidence_count": len(
                missing_evidence
            ),
        },
    }


def build_competency_requirement_profile(
    competency_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[
        tuple[str, str],
        dict[str, Any],
    ] = {}

    for row in competency_rows:
        if row.get("not_relevant") is True:
            continue

        if row.get("recommend_suppress") is True:
            continue

        skill_type = row["skill_type"]
        element_name = row["element_name"]

        key = (
            skill_type,
            element_name,
        )

        if key not in grouped:
            grouped[key] = {
                "skill_type": skill_type,
                "element_id": row["element_id"],
                "element_name": element_name,
                "importance": None,
                "level": None,
                "student_measurement_status": "NOT_ASSESSED",
                "gap_status": "UNKNOWN",
            }

        scale_id = row["scale_id"]
        value = row["data_value"]

        if scale_id == "IM":
            grouped[key]["importance"] = value

        elif scale_id == "LV":
            grouped[key]["level"] = value

    requirements = list(grouped.values())

    requirements.sort(
        key=lambda item: (
            item["importance"]
            if item["importance"] is not None
            else -1
        ),
        reverse=True,
    )

    return requirements


def build_gap_analysis(
    software_alignment: dict[str, Any],
    competency_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    technology_analysis = (
        build_technology_gap_analysis(
            software_alignment
        )
    )

    competency_profile = (
        build_competency_requirement_profile(
            competency_rows
        )
    )

    return {
        "technology_analysis": technology_analysis,
        "competency_requirements": competency_profile,
        "interpretation": {
            "strong_evidence": (
                "CareerPilot found relatively strong "
                "supporting evidence for this technology "
                "under the current ACIF evidence model. "
                "This does not by itself prove proficiency."
            ),
            "missing_evidence": (
                "No evidence was found in the current "
                "Career Twin. It must not be interpreted "
                "as proof that the student lacks the skill."
            ),
            "not_assessed": (
                "The career requires or values this "
                "competency, but CareerPilot has not yet "
                "measured the student's competency level."
            ),
        },
    }