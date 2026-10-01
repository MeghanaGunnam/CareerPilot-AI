import re
from typing import Any


TECHNOLOGY_ALIASES = {
    "oracle java": "java",
    "java": "java",

    "cascading style sheets css": "css",
    "css": "css",

    "hypertext markup language html": "html",
    "html": "html",

    "structured query language sql": "sql",
    "sql": "sql",

    "restful api": "rest api",
    "rest api": "rest api",

    "postgresql": "postgresql",

    "javascript": "javascript",
    "typescript": "typescript",
    "python": "python",
    "react": "react",
    "docker": "docker",
    "git": "git",
    "github": "github",
    "spring boot": "spring boot",
    "spring framework": "spring framework",
    "node js": "node.js",
    "node.js": "node.js",
    "kubernetes": "kubernetes",
    "nosql": "nosql",
}


def normalize_technology_name(
    value: str | None,
) -> str:
    if not value:
        return ""

    normalized = value.strip().lower()

    normalized = re.sub(
        r"[^a-z0-9+#.]+",
        " ",
        normalized,
    )

    normalized = re.sub(
        r"\s+",
        " ",
        normalized,
    ).strip()

    return TECHNOLOGY_ALIASES.get(
        normalized,
        normalized,
    )


def match_student_technology(
    student_skill: dict[str, Any],
    requirement_name: str,
) -> dict[str, Any]:
    student_name = normalize_technology_name(
        student_skill.get("name")
    )

    requirement = normalize_technology_name(
        requirement_name
    )

    matched = (
        bool(student_name)
        and bool(requirement)
        and student_name == requirement
    )

    return {
        "matched": matched,
        "student_normalized": student_name,
        "requirement_normalized": requirement,
    }


def build_student_skill_index(
    skill_states: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}

    for skill in skill_states:
        normalized = normalize_technology_name(
            skill.get("name")
        )

        if not normalized:
            continue

        existing = index.get(normalized)

        if existing is None:
            index[normalized] = skill
            continue

        existing_confidence = float(
            existing.get("evidence_confidence") or 0.0
        )

        new_confidence = float(
            skill.get("evidence_confidence") or 0.0
        )

        if new_confidence > existing_confidence:
            index[normalized] = skill

    return index