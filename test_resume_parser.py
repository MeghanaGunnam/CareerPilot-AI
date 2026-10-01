from sqlalchemy import select

from backend.app.core.database import SessionLocal
from backend.app.resumes.models import ResumeVersion
from backend.app.resumes.parser import parse_resume_sections
from backend.app.resumes.skill_extractor import (
    extract_skills_from_sections,
)


def main():
    db = SessionLocal()

    try:
        statement = (
            select(ResumeVersion)
            .where(
                ResumeVersion.extraction_status
                == "COMPLETED"
            )
            .order_by(
                ResumeVersion.created_at.desc()
            )
            .limit(1)
        )

        resume_version = db.scalar(statement)

        if resume_version is None:
            print("No completed resume found.")
            return

        if not resume_version.extracted_text:
            print("Resume has no extracted text.")
            return

        sections = parse_resume_sections(
            resume_version.extracted_text
        )

        skills = extract_skills_from_sections(
            sections
        )

        print(
            "\n========== EXTRACTED SKILLS ==========\n"
        )

        if not skills:
            print("No skills detected.")

        for skill in skills:
            print(
                f"{skill.canonical_name:<30}"
                f" | Section: {skill.source_section:<15}"
                f" | Match: {skill.matched_text}"
            )

        print(
            "\n======================================\n"
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()