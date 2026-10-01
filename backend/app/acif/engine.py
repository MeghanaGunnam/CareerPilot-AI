from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any


ACIF_MODEL_VERSION = "acif-v1"

# V1 heuristic parameters.
# These are implementation parameters, not empirically validated constants.
SOURCE_RELIABILITY = {
    "ASSESSMENT": 0.90,
    "PROJECT": 0.75,
    "CERTIFICATION": 0.70,
    "EXPERIENCE": 0.80,
    "RESUME": 0.40,
    "CLAIM": 0.30,
}

STATUS_RELIABILITY = {
    "ASSESSED": 1.00,
    "VERIFIED": 1.00,
    "DETECTED": 0.70,
    "CLAIMED": 0.50,
    "PLANNED": 0.20,
}

# Half-life in days for V1 freshness estimation.
DEFAULT_HALF_LIFE_DAYS = 365.0


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def parse_datetime(value: str | datetime | None) -> datetime | None:
    if value is None:
        return None

    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )
        except (ValueError, TypeError):
            return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def calculate_freshness(
    observed_at: str | datetime | None,
    now: datetime | None = None,
    half_life_days: float = DEFAULT_HALF_LIFE_DAYS,
) -> float:
    if observed_at is None:
        return 0.0

    observed = parse_datetime(observed_at)

    if observed is None:
        return 0.0

    current = now or datetime.now(timezone.utc)

    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)

    age_days = max(
        0.0,
        (current - observed).total_seconds() / 86400.0,
    )

    decay = math.exp(
        -math.log(2.0) * age_days / half_life_days
    )

    return clamp(decay)


def infer_evidence_family(evidence: dict[str, Any]) -> str:
    source_type = str(
        evidence.get("source_type") or ""
    ).upper()

    source_section = str(
        evidence.get("source_section") or ""
    ).lower()

    if source_type == "ASSESSMENT":
        return "ASSESSMENT"

    if source_type == "PROJECT":
        return "PROJECT"

    if source_type == "CERTIFICATION":
        return "CERTIFICATION"

    if source_type == "EXPERIENCE":
        return "EXPERIENCE"

    # Resume evidence currently carries semantic meaning
    # through source_section.
    if source_type == "RESUME":
        if "project" in source_section:
            return "PROJECT"

        if "certification" in source_section:
            return "CERTIFICATION"

        if "experience" in source_section:
            return "EXPERIENCE"

        return "CLAIM"

    return source_type or "UNKNOWN"


def calculate_single_evidence_support(
    evidence: dict[str, Any],
    now: datetime | None = None,
) -> dict[str, Any]:
    family = infer_evidence_family(evidence)

    source_type = str(
        evidence.get("source_type") or ""
    ).upper()

    status = str(
        evidence.get("evidence_status") or ""
    ).upper()

    source_reliability = SOURCE_RELIABILITY.get(
        family,
        SOURCE_RELIABILITY.get(source_type, 0.25),
    )

    status_reliability = STATUS_RELIABILITY.get(
        status,
        0.25,
    )

    freshness = calculate_freshness(
        evidence.get("observed_at"),
        now=now,
    )

    raw_strength = evidence.get(
        "evidence_strength"
    )

    if raw_strength is None:
        strength = 1.0
        strength_available = False
    else:
        strength = clamp(float(raw_strength))
        strength_available = True

    support = (
        source_reliability
        * status_reliability
        * freshness
        * strength
    )

    return {
        "evidence_id": evidence.get("id"),
        "family": family,
        "source_type": source_type,
        "status": status,
        "source_reliability": round(
            source_reliability,
            4,
        ),
        "status_reliability": round(
            status_reliability,
            4,
        ),
        "freshness": round(freshness, 4),
        "strength": (
            round(strength, 4)
            if strength_available
            else None
        ),
        "support": round(
            clamp(support),
            4,
        ),
    }


def aggregate_family_support(
    evidence_scores: list[dict[str, Any]],
) -> dict[str, float]:
    families: dict[str, list[float]] = defaultdict(list)

    for item in evidence_scores:
        families[item["family"]].append(
            float(item["support"])
        )

    result: dict[str, float] = {}

    for family, supports in families.items():
        # Repeated evidence from the same family should not
        # linearly inflate confidence.
        result[family] = round(
            max(supports),
            4,
        )

    return result


def combine_independent_support(
    family_support: dict[str, float],
) -> float:
    if not family_support:
        return 0.0

    remaining_uncertainty = 1.0

    for support in family_support.values():
        remaining_uncertainty *= (
            1.0 - clamp(support)
        )

    return clamp(
        1.0 - remaining_uncertainty
    )


def calculate_skill_state(
    skill: dict[str, Any],
    now: datetime | None = None,
) -> dict[str, Any]:
    evidence = skill.get("evidence") or []

    evidence_scores = [
        calculate_single_evidence_support(
            item,
            now=now,
        )
        for item in evidence
    ]

    family_support = aggregate_family_support(
        evidence_scores
    )

    confidence = combine_independent_support(
        family_support
    )

    freshness_values = [
        float(item["freshness"])
        for item in evidence_scores
    ]

    freshness = (
        max(freshness_values)
        if freshness_values
        else 0.0
    )

    assessed_strengths = [
        float(item["strength"])
        for item in evidence_scores
        if item["family"] == "ASSESSMENT"
        and item["strength"] is not None
    ]

    estimated_proficiency = (
        max(assessed_strengths)
        if assessed_strengths
        else None
    )

    # Verified state exists only when we have an actual
    # proficiency estimate. Evidence confidence alone is
    # not treated as proficiency.
    verified_state = (
        estimated_proficiency
        * confidence
        * freshness
        if estimated_proficiency is not None
        else None
    )

    return {
        "student_skill_id": skill.get(
            "student_skill_id"
        ),
        "skill_id": skill.get("skill_id"),
        "name": skill.get("name"),
        "category": skill.get("category"),
        "model_version": ACIF_MODEL_VERSION,
        "evidence_count": len(evidence_scores),
        "evidence_families": sorted(
            family_support.keys()
        ),
        "family_support": family_support,
        "evidence_confidence": round(
            confidence,
            4,
        ),
        "freshness_score": round(
            freshness,
            4,
        ),
        "estimated_proficiency": (
            round(estimated_proficiency, 4)
            if estimated_proficiency is not None
            else None
        ),
        "verified_skill_state": (
            round(verified_state, 4)
            if verified_state is not None
            else None
        ),
        "evidence_details": evidence_scores,
    }


def calculate_all_skill_states(
    twin_state: dict[str, Any],
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    skills = twin_state.get("skills") or []

    states = [
        calculate_skill_state(
            skill,
            now=now,
        )
        for skill in skills
    ]

    states.sort(
        key=lambda item: (
            -item["evidence_confidence"],
            item["name"].lower(),
        )
    )

    return states