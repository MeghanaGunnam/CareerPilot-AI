"""Controlled catalog metadata; no inferred O*NET equivalence or title parsing."""

from dataclasses import asdict, dataclass
from uuid import NAMESPACE_URL, uuid5

from backend.app.assessments.question_bank import TECHNICAL_ASSESSMENTS


@dataclass(frozen=True)
class CatalogEntry:
    catalog_id: str
    version: int
    skill_name: str
    title: str
    domain: str
    is_active: bool
    provenance: str


CATALOG = (
    CatalogEntry("java-fundamentals", 1, "Java", "Java Fundamentals Assessment", "PROGRAMMING", True, "CareerPilot existing local question bank; preserved verbatim."),
    CatalogEntry("critical-thinking-fundamentals", 1, "Critical Thinking", "Critical Thinking Fundamentals Assessment", "REASONING", True, "CareerPilot existing local question bank; preserved verbatim."),
    CatalogEntry("python-fundamentals", 1, "Python", "Python Fundamentals Assessment", "PROGRAMMING", True, "Original CareerPilot application-authored items, 2026-10; Python 3; not externally validated or standardized."),
    CatalogEntry("sql-fundamentals", 1, "SQL", "SQL Fundamentals Assessment", "DATABASES", True, "Original CareerPilot application-authored items, 2026-10; portable SQL; not externally validated or standardized."),
)


def catalog_assessment_id(entry):
    """Deterministic IDs for new rows; existing legacy UUIDs are retained."""
    return uuid5(NAMESPACE_URL, f"careerpilot:assessment:{entry.catalog_id}:v{entry.version}")


def get_controlled_catalog_metadata(assessment, skill_name=None):
    """Public metadata or None; exact skill/title/version, never title heuristics."""
    if skill_name is None:
        skill_name = assessment.skill.canonical_name
    for entry in CATALOG:
        if (skill_name, assessment.title, assessment.version) == (entry.skill_name, entry.title, entry.version):
            result = asdict(entry)
            result["is_active"] = assessment.is_active
            return result
    return None


def validate_catalog(bank=None, entries=CATALOG):
    bank = TECHNICAL_ASSESSMENTS if bank is None else bank
    identities = set()
    lookup = set()
    for entry in entries:
        identity = (entry.catalog_id, entry.version)
        key = (entry.skill_name, entry.title, entry.version)
        if identity in identities or key in lookup:
            raise ValueError("Duplicate catalog identity/version or database lookup key")
        if not all((entry.catalog_id, entry.skill_name, entry.title, entry.domain, entry.provenance)) or type(entry.version) is not int or entry.version < 1 or type(entry.is_active) is not bool:
            raise ValueError("Invalid catalog metadata")
        identities.add(identity)
        lookup.add(key)
    if len(bank) != len(entries):
        raise ValueError("Question bank and catalog must have equal membership")
    seen = set()
    for item in bank:
        key = (item["skill"], item["title"], item["version"])
        if key not in lookup or key in seen:
            raise ValueError("Unregistered or duplicate assessment")
        seen.add(key)
        questions = item["questions"]
        if not questions or [q["position"] for q in questions] != list(range(1, len(questions) + 1)):
            raise ValueError(f"{key}: positions must be contiguous, ordered, and unique")
        prompts = set()
        for question in questions:
            if type(question["position"]) is not int:
                raise ValueError("Question position must be an integer")
            if not question["question_text"].strip() or question["question_text"] in prompts or not question["explanation"].strip():
                raise ValueError("Questions require unique prompts and explanations")
            prompts.add(question["question_text"])
            options = question["options"]
            if [o["key"] for o in options] != list("ABCD") or question["correct_option"] not in "ABCD" or len(question["correct_option"]) != 1:
                raise ValueError("Questions require ordered unique A-D keys and one valid answer")
            texts = [o["text"].strip() for o in options]
            if not all(texts) or len(set(texts)) != 4:
                raise ValueError("Option text must be nonempty and unique")
    return bank
