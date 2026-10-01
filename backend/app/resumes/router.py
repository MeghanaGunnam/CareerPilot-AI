from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User
from backend.app.core.database import get_db
from backend.app.resumes.schemas import (
    ResumeUploadResponse,
)
from backend.app.resumes.service import upload_resume


router = APIRouter(
    prefix="/api/v1/resumes",
    tags=["Resumes"],
)


@router.post(
    "/upload",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_resume_file(
    file: UploadFile = File(...),
    title: str = Form(default="My Resume"),
    resume_id: UUID | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resume, version = await upload_resume(
        db=db,
        user_id=current_user.id,
        uploaded_file=file,
        title=title,
        resume_id=resume_id,
    )

    return ResumeUploadResponse(
        resume_id=resume.id,
        title=resume.title,
        active_version_number=(
            resume.active_version_number
        ),
        version=version,
    )