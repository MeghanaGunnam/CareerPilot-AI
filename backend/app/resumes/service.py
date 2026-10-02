import hashlib
import io
import uuid
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from pypdf import PdfReader
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from backend.app.career_twin.service import create_career_twin_snapshot
from backend.app.resumes.models import Resume, ResumeVersion
from backend.app.resumes.parser import parse_resume_sections
from backend.app.resumes.skill_extractor import extract_skills_from_sections
from backend.app.skills.service import save_resume_skill_evidence


PROJECT_ROOT = Path(__file__).resolve().parents[3]

RESUME_STORAGE_DIR = PROJECT_ROOT / "storage" / "resumes"

MAX_RESUME_SIZE_BYTES = 5 * 1024 * 1024

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
}

PARSER_VERSION = "pypdf-v1"


def validate_pdf(
    filename: str | None,
    content_type: str | None,
    file_bytes: bytes,
) -> None:
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A filename is required.",
        )

    if Path(filename).suffix.lower() != ".pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF resumes are supported.",
        )

    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PDF content type.",
        )

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty.",
        )

    if len(file_bytes) > MAX_RESUME_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Resume file must not exceed 5 MB.",
        )

    if not file_bytes.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is not a valid PDF.",
        )


def extract_pdf_text(file_bytes: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(file_bytes))

        pages: list[str] = []

        for page in reader.pages:
            text = page.extract_text()

            if text:
                pages.append(text.strip())

        extracted_text = "\n\n".join(
            page for page in pages if page
        ).strip()

        if not extracted_text:
            raise ValueError(
                "No readable text was found in the PDF."
            )

        return extracted_text

    except Exception as exc:
        raise ValueError(
            f"PDF text extraction failed: {exc}"
        ) from exc


def calculate_sha256(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()


def create_storage_key(
    user_id: UUID,
    resume_id: UUID,
    version_number: int,
) -> str:
    random_name = uuid.uuid4().hex

    return (
        f"{user_id}/"
        f"{resume_id}/"
        f"v{version_number}/"
        f"{random_name}.pdf"
    )


def save_private_file(
    storage_key: str,
    file_bytes: bytes,
) -> None:
    file_path = RESUME_STORAGE_DIR / storage_key

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path.write_bytes(file_bytes)


def delete_private_file(storage_key: str) -> None:
    file_path = RESUME_STORAGE_DIR / storage_key

    if file_path.exists():
        file_path.unlink()


def get_next_version_number(
    db: Session,
    resume_id: UUID,
) -> int:
    statement = select(
        func.max(ResumeVersion.version_number)
    ).where(
        ResumeVersion.resume_id == resume_id
    )

    current_max = db.scalar(statement)

    return (current_max or 0) + 1


async def upload_resume(
    db: Session,
    user_id: UUID,
    uploaded_file: UploadFile,
    title: str,
    resume_id: UUID | None = None,
) -> tuple[Resume, ResumeVersion]:

    file_bytes = await uploaded_file.read()

    validate_pdf(
        filename=uploaded_file.filename,
        content_type=uploaded_file.content_type,
        file_bytes=file_bytes,
    )

    file_hash = calculate_sha256(file_bytes)

    # ---------------------------------------------------------
    # Create a new resume or load an existing resume
    # ---------------------------------------------------------

    if resume_id is None:
        resume = Resume(
            user_id=user_id,
            title=title.strip() or "My Resume",
        )

        db.add(resume)
        db.flush()

        version_number = 1

    else:
        statement = select(Resume).where(
            Resume.id == resume_id,
            Resume.user_id == user_id,
        )

        resume = db.scalar(statement)

        if resume is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found.",
            )

        version_number = get_next_version_number(
            db=db,
            resume_id=resume.id,
        )

    # ---------------------------------------------------------
    # Duplicate file detection
    # ---------------------------------------------------------

    duplicate_statement = (
        select(ResumeVersion)
        .join(
            Resume,
            Resume.id == ResumeVersion.resume_id,
        )
        .where(
            Resume.user_id == user_id,
            ResumeVersion.file_sha256 == file_hash,
        )
    )

    duplicate = db.scalar(duplicate_statement)

    if duplicate is not None:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This resume file has already been uploaded.",
        )

    # ---------------------------------------------------------
    # Generate private storage location
    # ---------------------------------------------------------

    storage_key = create_storage_key(
        user_id=user_id,
        resume_id=resume.id,
        version_number=version_number,
    )

    saved_to_storage = False

    try:
        # -----------------------------------------------------
        # Save original PDF privately
        # -----------------------------------------------------

        save_private_file(
            storage_key=storage_key,
            file_bytes=file_bytes,
        )

        saved_to_storage = True

        # -----------------------------------------------------
        # Extract text from PDF
        # -----------------------------------------------------

        extraction_status = "COMPLETED"
        extracted_text = None
        extraction_error = None

        try:
            extracted_text = extract_pdf_text(
                file_bytes
            )

        except ValueError as exc:
            extraction_status = "FAILED"
            extraction_error = str(exc)

        # -----------------------------------------------------
        # Create resume version
        # -----------------------------------------------------

        resume_version = ResumeVersion(
            resume_id=resume.id,
            version_number=version_number,
            original_filename=(
                uploaded_file.filename
                or "resume.pdf"
            ),
            storage_key=storage_key,
            content_type=(
                uploaded_file.content_type
                or "application/pdf"
            ),
            file_size_bytes=len(file_bytes),
            file_sha256=file_hash,
            extraction_status=extraction_status,
            extracted_text=extracted_text,
            extraction_error=extraction_error,
            parser_version=PARSER_VERSION,
        )

        db.add(resume_version)

        # Generate the ResumeVersion UUID before
        # creating SkillEvidence records.
        db.flush()

        resume.active_version_number = version_number

        # -----------------------------------------------------
        # Resume Intelligence Pipeline
        # -----------------------------------------------------

        if (
            resume_version.extraction_status == "COMPLETED"
            and resume_version.extracted_text
        ):
            # Step 1: Detect resume sections
            sections = parse_resume_sections(
                resume_version.extracted_text
            )

            # Step 2: Extract normalized skills
            extracted_skills = (
                extract_skills_from_sections(
                    sections
                )
            )

            # Step 3: Persist Skill → StudentSkill → Evidence
            save_resume_skill_evidence(
                db=db,
                user_id=user_id,
                resume_version_id=resume_version.id,
                extracted_skills=extracted_skills,
                sections=sections,
            )
        # -----------------------------------------------------
        # Commit resume + evidence together
        # -----------------------------------------------------

        db.commit()

        db.refresh(resume)
        db.refresh(resume_version)

        # -----------------------------------------------------
        # Refresh Career Twin after successful resume evidence
        # -----------------------------------------------------

        if (
            resume_version.extraction_status == "COMPLETED"
            and resume_version.extracted_text
        ):
            create_career_twin_snapshot(
                db=db,
                user_id=user_id,
                trigger_type="RESUME_PROCESSED",
                source_type="RESUME",
                source_reference=str(resume_version.id),
            )

        return resume, resume_version
    except HTTPException:
        db.rollback()

        if saved_to_storage:
            delete_private_file(storage_key)

        raise

    except Exception:
        db.rollback()

        if saved_to_storage:
            delete_private_file(storage_key)

        raise