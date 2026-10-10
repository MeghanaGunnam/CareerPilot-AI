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
    ResumeDetailResponse,
    ResumeListItemResponse,
    ResumeUploadResponse,
)
from backend.app.resumes.service import (
    get_user_resume,
    list_user_resumes,
    upload_resume,
)


router = APIRouter(
    prefix="/api/v1/resumes",
    tags=["Resumes"],
)


@router.get(
    "",
    response_model=list[ResumeListItemResponse],
    status_code=status.HTTP_200_OK,
)
def list_resumes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_user_resumes(
        db=db,
        user_id=current_user.id,
    )


@router.get(
    "/{resume_id}",
    response_model=ResumeDetailResponse,
    status_code=status.HTTP_200_OK,
)
def get_resume(
    resume_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_user_resume(
        db=db,
        user_id=current_user.id,
        resume_id=resume_id,
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