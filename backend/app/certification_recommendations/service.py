import re
import unicodedata
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.acif.service import get_career_gap_analysis
from backend.app.acif.technology_matching import normalize_technology_name
from backend.app.careers.models import Career
from backend.app.certification_recommendations.catalog import CATALOG, CertificationDefinition
from backend.app.students.service import get_user_certifications, get_user_primary_career_goal


METHODOLOGY = (
    "CURATED_EXACT_TECHNOLOGY_GAP_V1: active primary goal -> mapped O*NET career -> "
    "existing ACIF technology gaps. Exact equality under the ACIF technology normalizer; "
    "no occupational-title or competency inference. Rank by missing-evidence gap count "
    "descending, total matched gap count descending, then stable catalogue key ascending. "
    "Priority is a 1-based display rank, not proficiency or readiness. Earned certifications "
    "are excluded only by exact normalized name/explicit alias AND provider/explicit alias."
)
INTERPRETATION = (
    "Suggestions are optional ways to build evidence, not proof of skill deficiency, "
    "proficiency, exam eligibility or employability. Missing evidence does not prove a lack "
    "of skill. Recommendations do not add evidence, change proficiency or create roadmap "
    "items. An empty list means no unsuppressed curated exact technology-gap match. "
    "Prices, availability and prerequisites are not live verified; consult official providers."
)


def normalize_credential_identity(value: str) -> str:
    # Preserve punctuation: version numbers, +, #, and other distinctions matter.
    # Typography/spacing and trademark symbols are presentation differences only.
    value = value.replace("™", "").replace("®", "").replace("©", "")
    value = unicodedata.normalize("NFKC", value).casefold()
    value = value.translate(str.maketrans({"–": "-", "—": "-", "‑": "-"}))
    return re.sub(r"\s+", " ", value).strip()


def _is_earned(cert: CertificationDefinition, earned: list) -> bool:
    names = {normalize_credential_identity(n) for n in (cert.name, *cert.name_aliases)}
    providers = {normalize_credential_identity(p) for p in (cert.provider, *cert.provider_aliases)}
    return any(
        normalize_credential_identity(row.name) in names
        and normalize_credential_identity(row.issuing_organization) in providers
        for row in earned
    )


def build_recommendations(gap_analysis: dict, earned: list) -> list[dict]:
    technology = gap_analysis.get("technology_analysis", {})
    gaps: dict[str, str] = {}
    # Process missing last for deterministic precedence on duplicate input labels.
    for bucket, state in (
        ("evidence_needs_strengthening", "EVIDENCE_NEEDS_STRENGTHENING"),
        ("missing_evidence", "MISSING_EVIDENCE"),
    ):
        for gap in technology.get(bucket, []):
            skill = normalize_technology_name(gap.get("technology"))
            if skill:
                gaps[skill] = state

    recommendations = []
    for cert in CATALOG:
        if _is_earned(cert, earned):
            continue
        covered = {normalize_technology_name(skill) for skill in cert.skills}
        matched = sorted(covered & gaps.keys())
        if not matched:
            continue
        recommendations.append({
            "key": cert.key,
            "name": cert.name,
            "provider": cert.provider,
            "category": cert.category,
            "relevant_skills": matched,
            "reason": "Curated technology coverage exactly matches current ACIF evidence gaps: "
                      + "; ".join(f"{skill} ({gaps[skill]})" for skill in matched) + ".",
            "gaps": [{"skill": skill, "state": gaps[skill]} for skill in matched],
            "official_url": cert.official_url,
            "provenance": cert.provenance(),
        })
    recommendations.sort(key=lambda rec: (
        -sum(gap["state"] == "MISSING_EVIDENCE" for gap in rec["gaps"]),
        -len(rec["gaps"]), rec["key"],
    ))
    for priority, recommendation in enumerate(recommendations, start=1):
        recommendation["priority"] = priority
    return recommendations


def get_certification_recommendations(db: Session, user_id: UUID) -> dict:
    goal = get_user_primary_career_goal(db=db, user_id=user_id)
    if goal is None:
        raise HTTPException(status_code=404, detail="Primary career goal not found.")
    if not goal.onet_soc_code:
        raise HTTPException(status_code=404, detail="Primary career goal has no target career mapping.")
    career = db.scalar(select(Career).where(Career.onet_soc_code == goal.onet_soc_code))
    if career is None:
        raise HTTPException(status_code=404, detail="Mapped target career not found.")
    gap_result = get_career_gap_analysis(db=db, user_id=user_id, career_id=career.id)
    earned = get_user_certifications(db=db, user_id=user_id)
    return {
        "target_role": goal.target_role,
        "occupational_anchor": {
            "id": str(career.id), "title": career.title, "onet_soc_code": career.onet_soc_code,
        },
        "snapshot_version": gap_result["snapshot_version"],
        "model_version": gap_result["model_version"],
        "methodology": METHODOLOGY,
        "recommendations": build_recommendations(gap_result["gap_analysis"], earned),
        "interpretation": INTERPRETATION,
    }
