import re
from dataclasses import dataclass


@dataclass
class ExtractedSkill:
    canonical_name: str
    matched_text: str
    source_section: str


SKILL_ALIASES = {
    "Java": {
        "java",
    },
    "Python": {
        "python",
    },
    "SQL": {
        "sql",
    },
    "PostgreSQL": {
        "postgresql",
        "postgres",
    },
    "MySQL": {
        "mysql",
    },
    "Redis": {
        "redis",
    },
    "Spring Boot": {
        "spring boot",
        "springboot",
    },
    "FastAPI": {
        "fastapi",
    },
    "REST API": {
        "rest api",
        "rest apis",
        "restful api",
        "restful apis",
    },
    "HTML": {
        "html",
        "html5",
    },
    "CSS": {
        "css",
        "css3",
    },
    "JavaScript": {
        "javascript",
        "js",
    },
    "TypeScript": {
        "typescript",
    },
    "React": {
        "react",
        "react.js",
        "reactjs",
    },
    "Next.js": {
        "next.js",
        "nextjs",
    },
    "Docker": {
        "docker",
    },
    "Git": {
        "git",
    },
    "GitHub": {
        "github",
    },
    "Pandas": {
        "pandas",
    },
    "NumPy": {
        "numpy",
    },
    "Scikit-learn": {
        "scikit-learn",
        "sklearn",
    },
    "Machine Learning": {
        "machine learning",
    },
    "Object-Oriented Programming": {
        "object-oriented programming",
        "object oriented programming",
        "oop",
    },
    "DBMS": {
        "dbms",
        "database management system",
    },
}


EVIDENCE_SECTIONS = {
    "skills",
    "experience",
    "projects",
    "certifications",
}


def normalize_text(text: str) -> str:
    text = text.lower()

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def contains_skill(
    text: str,
    alias: str,
) -> bool:
    pattern = (
        r"(?<![a-zA-Z0-9])"
        + re.escape(alias.lower())
        + r"(?![a-zA-Z0-9])"
    )

    return re.search(
        pattern,
        text,
        flags=re.IGNORECASE,
    ) is not None


def extract_skills_from_sections(
    sections: dict[str, str],
) -> list[ExtractedSkill]:
    extracted: list[ExtractedSkill] = []

    seen: set[tuple[str, str]] = set()

    for section_name in EVIDENCE_SECTIONS:
        section_text = sections.get(
            section_name,
            "",
        )

        if not section_text:
            continue

        normalized_section = normalize_text(
            section_text
        )

        for canonical_name, aliases in SKILL_ALIASES.items():
            for alias in aliases:
                if contains_skill(
                    normalized_section,
                    alias,
                ):
                    key = (
                        canonical_name,
                        section_name,
                    )

                    if key not in seen:
                        extracted.append(
                            ExtractedSkill(
                                canonical_name=canonical_name,
                                matched_text=alias,
                                source_section=section_name,
                            )
                        )

                        seen.add(key)

                    break

    return sorted(
        extracted,
        key=lambda item: (
            item.canonical_name.lower(),
            item.source_section,
        ),
    )