"""Read-only comparison of saved JD rows with the latest recorded Career Twin.

No extraction, snapshot creation, roadmap generation, or new evidence writes.
Requirement strength is explicitly a conservative interpretation, never a fact.
"""
import re
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.acif.engine import ACIF_MODEL_VERSION, calculate_all_skill_states
from backend.app.acif.gap_analysis import classify_technology_match
from backend.app.acif.career_gps import build_evidence_actions
from backend.app.acif.service import get_current_twin_snapshot
from backend.app.acif.technology_matching import build_student_skill_index, normalize_technology_name
from backend.app.assessments.models import Assessment
from backend.app.certification_recommendations.service import build_recommendations
from backend.app.jobs.schemas import RequirementResponse
from backend.app.jobs.service import get_analysis
from backend.app.skills.models import Skill
from backend.app.students.service import get_user_certifications

MATCHING_VERSION = "jd-evidence-match-v1"
METHODOLOGY = (
    "Unique mapped technologies explicitly required by reliable v2 source clauses only: "
    "numerator = technologies with ACIF STRONG_EVIDENCE (confidence >= 0.70); "
    "denominator = eligible unique technologies. Value = numerator / denominator. "
    "No partial-credit weights. Optional, negated, uncertain, conflicting and unmapped "
    "criteria are excluded, not failures. Null when no eligible criteria, no snapshot, "
    "or extraction was truncated. This is evidence alignment, not proficiency or hiring probability."
)
_negative = re.compile(r"\b(?:not|no|never|without|unnecessary|optional)\b|n[’']t\b", re.I)
_optional = re.compile(r"\b(?:preferred|desirable|bonus|optional|plus)\b|nice[ -]to[ -]have", re.I)
_required = re.compile(r"\b(?:required|must|mandatory|essential)\b", re.I)
_ambiguous = re.compile(r"\b(?:if|unless|either|or|may|might|could)\b", re.I)


def interpret_strength(analysis, requirement) -> tuple[str, str]:
    if analysis.extractor_version != "jd-literal-v2":
        return "UNCERTAIN", "Legacy/unknown extractor may quote only an alias; mandatory status cannot be inferred."
    quote = requirement.quote
    if _negative.search(quote) and not re.search(r"\boptional\b", quote, re.I):
        return "NEGATED_OR_NON_REQUIRED", "Negative language is present; do not treat this clause as mandatory."
    if _optional.search(quote) or requirement.group == "preferred":
        return "OPTIONAL_OR_PREFERRED", "Optional/preferred language or inferred grouping; excluded from required alignment."
    # Inspect surrounding source context only, not extraction. Wrapped qualifiers
    # and shared negative headings must not turn isolated clauses into mandates.
    before = analysis.source_text[:requirement.source_start]
    after = analysis.source_text[requirement.source_end:]
    context = before.split("\n\n")[-1] + quote + after.split("\n\n")[0]
    if _negative.search(context) or _ambiguous.search(quote):
        return "UNCERTAIN", "Context contains negative/conditional/alternative language; review the original JD."
    if _required.search(quote):
        return "EXPLICIT_REQUIRED", "Explicit required-language heuristic; this is a CareerPilot interpretation, not a new source fact."
    return "UNCERTAIN", "A technology mention alone does not establish mandatory status."


def compare_requirements(analysis, skill_states: list[dict], available: bool) -> tuple[list[dict], dict]:
    index = build_student_skill_index(skill_states)
    rows = []
    for requirement in analysis.requirements:
        strength, strength_reason = interpret_strength(analysis, requirement)
        canonical = normalize_technology_name(requirement.normalized_name) or None
        provenance_valid = (
            0 <= requirement.source_start < requirement.source_end <= len(analysis.source_text)
            and analysis.source_text[requirement.source_start:requirement.source_end] == requirement.quote
            and requirement.interpretation_type == "NORMALIZED_INTERPRETATION"
        )
        if not provenance_valid:
            canonical = None
        skill = index.get(canonical) if canonical else None
        details = (skill or {}).get("evidence_details", [])
        measurement = (skill or {}).get("estimated_proficiency")
        evidence = {
            "skill_id": (skill or {}).get("skill_id"),
            "evidence_count": (skill or {}).get("evidence_count", 0),
            "source_types": sorted({item["source_type"] for item in details}),
            "evidence_families": (skill or {}).get("evidence_families", []),
            "evidence_ids": [str(item["evidence_id"]) for item in details if item.get("evidence_id")],
            "evidence_confidence": skill.get("evidence_confidence") if skill and skill.get("evidence_count") else None,
            "assessment_measurement": measurement,
            "measurement_status": "ASSESSMENT_MEASUREMENT_AVAILABLE" if measurement is not None else "NOT_ASSESSED",
        }
        if not canonical:
            state, explanation = "UNKNOWN_OR_UNMAPPED", "No reliable canonical technology interpretation. Education, experience duration and responsibilities are not inferred from skill evidence."
        elif not available:
            state, explanation = "NOT_ASSESSED", "No recorded Career Twin snapshot is available; this is not a claim of missing skill."
        elif strength == "NEGATED_OR_NON_REQUIRED":
            state, explanation = "NOT_ASSESSED", "Not evaluated as a requirement because the source contains negative/non-required language."
        else:
            state = classify_technology_match(evidence["evidence_confidence"])
            if state == "STRONG_EVIDENCE":
                state = "EVIDENCE_BACKED_ALIGNMENT"
            explanation = {
                "EVIDENCE_BACKED_ALIGNMENT": "ACIF found strong supporting evidence (confidence >= 0.70). Evidence confidence does not prove proficiency or satisfy every aspect of the JD clause.",
                "EVIDENCE_NEEDS_STRENGTHENING": "Relevant evidence is recorded, but ACIF confidence is below 0.70. This does not imply inability.",
                "MISSING_EVIDENCE": "No supporting evidence is recorded for this technology in the latest Career Twin. Missing evidence does not mean missing skill.",
            }[state]
        eligible = bool(canonical and available and strength == "EXPLICIT_REQUIRED")
        rows.append({
            "requirement": RequirementResponse.model_validate(requirement),
            "canonical_technology": canonical, "strength": strength,
            "strength_explanation": strength_reason, "state": state, "evidence": evidence,
            "explanation": explanation, "included_in_alignment": eligible,
            "exclusion_reason": None if eligible else "Only reliably mapped, explicit required criteria with available Twin evidence state are eligible.",
            "actions": [],
        })
    # Any inconsistent strength for a repeated technology excludes it entirely.
    uncertain = {row["canonical_technology"] for row in rows if row["strength"] != "EXPLICIT_REQUIRED"}
    for row in rows:
        if row["included_in_alignment"] and row["canonical_technology"] in uncertain:
            row["included_in_alignment"] = False
            row["exclusion_reason"] = "Conflicting or uncertain occurrences of this technology require review."
        if analysis.truncated:
            row["included_in_alignment"] = False
            row["exclusion_reason"] = "Extraction was truncated; a whole-JD aggregate is unavailable."
    eligible = {row["canonical_technology"] for row in rows if row["included_in_alignment"]}
    strong = {row["canonical_technology"] for row in rows if row["included_in_alignment"] and row["state"] == "EVIDENCE_BACKED_ALIGNMENT"}
    return rows, {"value": len(strong) / len(eligible) if eligible else None,
                  "numerator": len(strong), "denominator": len(eligible),
                  "eligible_technologies": sorted(eligible), "methodology": METHODOLOGY}


def get_job_match(db: Session, user_id: UUID, analysis_id: UUID) -> dict:
    # Enforce JD ownership BEFORE looking at private Career Twin state.
    analysis = get_analysis(db, user_id, analysis_id)
    now = datetime.now(timezone.utc)
    twin = snapshot = None
    unavailable = None
    try:
        twin, snapshot = get_current_twin_snapshot(db, user_id)
    except HTTPException as error:
        if error.status_code != 404:
            raise
        unavailable = error.detail
    skills = calculate_all_skill_states(snapshot.state_data, now=now) if snapshot else []
    rows, alignment = compare_requirements(analysis, skills, snapshot is not None)
    if snapshot:
        gaps = {"evidence_needs_strengthening": [], "missing_evidence": []}
        for row in rows:
            if row["canonical_technology"] and row["strength"] != "NEGATED_OR_NON_REQUIRED":
                bucket = {"EVIDENCE_NEEDS_STRENGTHENING": "evidence_needs_strengthening", "MISSING_EVIDENCE": "missing_evidence"}.get(row["state"])
                if bucket:
                    gaps[bucket].append({"technology": row["canonical_technology"], "evidence_confidence": row["evidence"]["evidence_confidence"]})
        evidence_actions = {a["technology"]: a for a in build_evidence_actions(gaps)}
        certificates = build_recommendations({"technology_analysis": gaps}, get_user_certifications(db, user_id))
        assessments = db.execute(select(Assessment, Skill).join(Skill, Skill.id == Assessment.skill_id).where(Assessment.is_active.is_(True))).all()
        for row in rows:
            technology = row["canonical_technology"]
            if row["state"] not in {"MISSING_EVIDENCE", "EVIDENCE_NEEDS_STRENGTHENING"}:
                continue
            if technology in evidence_actions:
                row["actions"].append({"label": evidence_actions[technology]["recommended_action"], "href": "/evidence", "provenance": "ACIF_CAREER_GPS"})
            else:
                row["actions"].append({"label": "Review your existing evidence before deciding whether to build more.", "href": "/evidence", "provenance": "CURRENT_EVIDENCE_REVIEW"})
            if row["evidence"]["measurement_status"] == "NOT_ASSESSED":
                for assessment, skill in sorted(assessments, key=lambda pair: (pair[0].title, str(pair[0].id))):
                    if normalize_technology_name(skill.canonical_name) == technology:
                        row["actions"].append({"label": f"Available assessment: {assessment.title} (v{assessment.version})", "href": "/assessment", "provenance": f"ACTIVE_ASSESSMENT:{assessment.id}"})
            for cert in certificates:
                if technology in cert["relevant_skills"]:
                    row["actions"].append({"label": f"Optional evidence pathway: {cert['name']} ({cert['provider']}). Review official eligibility; recommendations page uses your career goal.", "href": "/certifications", "provenance": f"EXISTING_CURATED_CATALOG:{cert['key']}"})
    return {
        "analysis_id": analysis.id, "status": "AVAILABLE" if snapshot else "UNAVAILABLE",
        "unavailable_reason": unavailable, "career_twin_id": twin.id if twin else None,
        "snapshot_version": snapshot.version if snapshot else None,
        "snapshot_created_at": snapshot.created_at if snapshot else None,
        "evaluated_at": now, "model_version": ACIF_MODEL_VERSION,
        "matching_version": MATCHING_VERSION, "extractor_version": analysis.extractor_version,
        "requirements": rows, "alignment": alignment,
        "interpretation": "Read-only comparison against the latest recorded snapshot, not unsaved profile changes. Source types remain distinct from ACIF evidence families. Assessment measurement is assessment-specific, not universal proficiency. Missing evidence is not missing skill. No hiring probability is estimated.",
    }
