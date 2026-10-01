import re


SECTION_ALIASES = {
    "summary": {
        "summary",
        "professional summary",
        "profile",
        "professional profile",
        "career summary",
        "objective",
        "career objective",
    },
    "skills": {
        "skills",
        "technical skills",
        "core skills",
        "key skills",
        "technologies",
        "technical expertise",
        "technical proficiencies",
    },
    "experience": {
        "experience",
        "work experience",
        "professional experience",
        "employment",
        "employment history",
        "work history",
    },
    "projects": {
        "projects",
        "academic projects",
        "personal projects",
        "key projects",
        "project experience",
    },
    "education": {
        "education",
        "academic background",
        "academic qualifications",
        "educational qualifications",
        "qualifications",
    },
    "certifications": {
        "certifications",
        "certificates",
        "licenses and certifications",
        "courses and certifications",
    },
}


def normalize_heading(text: str) -> str:
    text = text.strip().lower()

    text = re.sub(
        r"[^a-z0-9\s&]",
        "",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def detect_section(line: str) -> str | None:
    normalized = normalize_heading(line)

    for section_name, aliases in SECTION_ALIASES.items():
        if normalized in aliases:
            return section_name

    return None


def clean_resume_text(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip()


def parse_resume_sections(
    text: str,
) -> dict[str, str]:
    cleaned_text = clean_resume_text(text)

    sections = {
        "header": [],
        "summary": [],
        "skills": [],
        "experience": [],
        "projects": [],
        "education": [],
        "certifications": [],
        "other": [],
    }

    current_section = "header"

    for raw_line in cleaned_text.split("\n"):
        line = raw_line.strip()

        if not line:
            continue

        detected_section = detect_section(line)

        if detected_section:
            current_section = detected_section
            continue

        sections[current_section].append(line)

    return {
        section: "\n".join(lines).strip()
        for section, lines in sections.items()
    }