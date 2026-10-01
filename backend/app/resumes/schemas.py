from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ResumeVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    resume_id: UUID
    version_number: int
    original_filename: str
    content_type: str
    file_size_bytes: int
    file_sha256: str
    extraction_status: str
    parser_version: str | None
    created_at: datetime


class ResumeUploadResponse(BaseModel):
    resume_id: UUID
    title: str
    active_version_number: int
    version: ResumeVersionResponse


class ResumeListItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    active_version_number: int | None
    created_at: datetime
    updated_at: datetime


class ResumeTextResponse(BaseModel):
    resume_id: UUID
    version_id: UUID
    version_number: int
    extraction_status: str
    extracted_text: str | None
    parser_version: str | None