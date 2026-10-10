"""Deterministic literal extraction, not candidate matching or mandatory-status inference.

Grouping and canonical labels are interpretations. Only the exact source quote is
a FACT_FROM_JD. No URL is retrieved and no unknown skill is guessed.
"""
import re
from dataclasses import dataclass

from backend.app.acif.technology_matching import TECHNOLOGY_ALIASES, normalize_technology_name
from backend.app.jobs.schemas import MAX_REQUIREMENTS
from backend.app.resumes.skill_extractor import SKILL_ALIASES

EXTRACTOR_VERSION = "jd-literal-v2"


@dataclass(frozen=True)
class ExtractedRequirement:
    group: str
    quote: str
    source_start: int
    source_end: int
    normalized_name: str | None = None
    evidence_type: str = "FACT_FROM_JD"

    @property
    def interpretation_type(self) -> str | None:
        return "NORMALIZED_INTERPRETATION" if self.normalized_name else None


# Share the application's finite vocabularies; do not normalize arbitrary JD words.
_aliases = {alias: normalize_technology_name(canonical)
            for canonical, aliases in SKILL_ALIASES.items() for alias in aliases}
_aliases.update({alias: normalize_technology_name(canonical)
                 for alias, canonical in TECHNOLOGY_ALIASES.items()})
_technology_pattern = re.compile(
    r"(?<![\w+#])(?ai:" + "|".join(
        re.escape(alias).replace(r"\ ", r"\s+")
        for alias in sorted(_aliases, key=lambda value: (-len(value), value))
    ) + r")(?![\w+#])",
)
_preferred = re.compile(r"\b(preferred|nice[ -]to[ -]have|desirable|bonus|a plus)\b", re.I)
_experience = re.compile(r"\b(?:\d+\s*(?:[-–]\s*\d+|\+)?\s*years?\b|experience\b)", re.I)
_education = re.compile(r"\b(?:bachelor(?:[’']s)?|master(?:[’']s)?|ph\.?d\.?|degree|diploma)\b", re.I)
_responsibility = re.compile(r"^(?:[-*•]\s*)?(?:you will\s+|responsible for\b|design\b|develop\b|build\b|maintain\b|implement\b|collaborate\b|lead\b|manage\b|deliver\b|support\b)", re.I)
_headings = {
    "preferred": "preferred", "preferred qualifications": "preferred",
    "nice to have": "preferred", "nice-to-have": "preferred",
    "responsibilities": "responsibility", "key responsibilities": "responsibility",
    "what you will do": "responsibility", "what you'll do": "responsibility",
    "experience": "experience", "education": "education",
    "requirements": None, "qualifications": None, "required qualifications": None,
    "minimum qualifications": None, "required": None, "skills": None,
    "technical skills": None, "about us": None, "benefits": None,
}


def extract_requirements(source: str) -> tuple[list[ExtractedRequirement], bool]:
    result: list[ExtractedRequirement] = []
    seen: set[tuple] = set()
    section = None
    truncated = False

    def add(group: str, start: int, end: int, normalized: str | None = None) -> None:
        nonlocal truncated
        key = (group, start, end, normalized)
        if key in seen:
            return
        seen.add(key)
        if len(result) >= MAX_REQUIREMENTS:
            truncated = True
            return
        result.append(ExtractedRequirement(group, source[start:end], start, end, normalized))

    # Sentence delimiters keep dotted aliases (Node.js) intact. All offsets point
    # into the original Unicode string, including CRLF and leading whitespace.
    clauses = (
        (line.start() + sentence.start(), sentence.group())
        for line in re.finditer(r"[^\r\n;]+", source)
        for sentence in re.finditer(r".+?(?:[.!?](?=\s|$)|$)", line.group())
    )
    for clause_start, raw in clauses:
        text = raw.strip()
        start = clause_start + len(raw) - len(raw.lstrip())
        end = start + len(text)
        if not text:
            continue
        heading = text.rstrip(":").lower()
        if heading in _headings:
            section = _headings[heading]
            continue
        # An unknown explicit heading ends inherited classification conservatively.
        if text.endswith(":"):
            section = None
            continue
        preferred = section == "preferred" or bool(_preferred.search(text))
        if preferred:
            add("preferred", start, end)
        elif _education.search(text):
            add("education", start, end)
        elif _experience.search(text):
            add("experience", start, end)
        elif section in {"responsibility", "education", "experience"}:
            add(section, start, end)
        elif _responsibility.search(text):
            add("responsibility", start, end)
        for match in _technology_pattern.finditer(text):
            alias = re.sub(r"\s+", " ", match.group().lower())
            # Quote the surrounding clause, never an isolated skill token that
            # drops "not required", "optional", or other source qualifiers.
            # Canonical names describe mentions, not mandatory requirements.
            add("preferred" if preferred else "technology",
                start, end, _aliases[alias])
    return result, truncated
