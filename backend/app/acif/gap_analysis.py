from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from backend.app.acif.competency_matching import (
    build_competency_measurements,
)


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
    db: Session,
    competency_rows: list[dict[str, Any]],
    skill_states: list[dict[str, Any]],
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
        element_id = row["element_id"]
        element_name = row["element_name"]

        # O*NET element_id is the stable competency identity.
        # skill_type is retained so different O*NET
        # requirement families remain distinct if needed.
        key = (
            skill_type,
            element_id,
        )

        if key not in grouped:
            grouped[key] = {
                "skill_type": skill_type,
                "element_id": element_id,
                "element_name": element_name,
                "importance": None,
                "level": None,
                "student_measurement_status": (
                    "NOT_ASSESSED"
                ),
                "gap_status": "UNKNOWN",
                "measurement": None,
            }

        scale_id = row["scale_id"]
        value = row["data_value"]

        if scale_id == "IM":
            grouped[key]["importance"] = value

        elif scale_id == "LV":
            grouped[key]["level"] = value

    competencies = [
        {
            "element_id": item["element_id"],
            "element_name": item["element_name"],
        }
        for item in grouped.values()
    ]

    measurements = build_competency_measurements(
        db=db,
        competencies=competencies,
        skill_states=skill_states,
    )

    for item in grouped.values():
        measurement = measurements.get(
            item["element_id"]
        )

        if measurement is None:
            continue

        item["student_measurement_status"] = (
            "MEASURED"
        )

        item["gap_status"] = (
            "MEASUREMENT_AVAILABLE"
        )

        item["measurement"] = measurement

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
    db: Session,
    software_alignment: dict[str, Any],
    competency_rows: list[dict[str, Any]],
    skill_states: list[dict[str, Any]],
) -> dict[str, Any]:
    technology_analysis = (
        build_technology_gap_analysis(
            software_alignment
        )
    )

    competency_profile = (
        build_competency_requirement_profile(
            db=db,
            competency_rows=competency_rows,
            skill_states=skill_states,
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
            "measured": (
                "CareerPilot found assessment-derived "
                "measurement evidence relevant to this "
                "occupational competency through an active "
                "CareerPilot skill-to-O*NET mapping. The "
                "mapped skill contributes evidence but does "
                "not represent complete measurement of the "
                "broader competency."
            ),
        },
    }