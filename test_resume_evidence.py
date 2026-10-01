from sqlalchemy import select
from backend.app.auth.models import User  # noqa: F401
from backend.app.core.database import SessionLocal
from backend.app.resumes.models import Resume, ResumeVersion
from backend.app.resumes.parser import (
    parse_resume_sections,
)
from backend.app.resumes.skill_extractor import (
    extract_skills_from_sections,
)
from backend.app.skills.service import (
    save_resume_skill_evidence,
)


def main():
    db = SessionLocal()

    try:
        statement = (
            select(ResumeVersion, Resume)
            .join(
                Resume,
                Resume.id == ResumeVersion.resume_id,
            )
            .where(
                ResumeVersion.extraction_status
                == "COMPLETED"
            )
            .order_by(
                ResumeVersion.created_at.desc()
            )
            .limit(1)
        )

        result = db.execute(statement).first()

        if result is None:
            print("No completed resume found.")
            return

        resume_version, resume = result

        if not resume_version.extracted_text:
            print("Resume has no extracted text.")
            return

        sections = parse_resume_sections(
            resume_version.extracted_text
        )

        extracted_skills = (
            extract_skills_from_sections(
                sections
            )
        )

        evidence_count = (
            save_resume_skill_evidence(
                db=db,
                user_id=resume.user_id,
                resume_version_id=resume_version.id,
                extracted_skills=extracted_skills,
                sections=sections,
            )
        )

        db.commit()

        print()
        print("========== EVIDENCE SAVED ==========")
        print(
            f"Detected skill mentions: "
            f"{len(extracted_skills)}"
        )
        print(
            f"New evidence records: "
            f"{evidence_count}"
        )
        print("====================================")
        print()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()