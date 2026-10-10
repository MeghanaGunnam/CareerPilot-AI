from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

ApplicationStatus = Literal["SAVED", "APPLIED", "ASSESSMENT", "INTERVIEW", "OFFER", "REJECTED", "WITHDRAWN"]


class ApplicationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    company: str = Field(min_length=1, max_length=200)
    job_title: str = Field(min_length=1, max_length=200)
    location: str | None = Field(default=None, max_length=200)
    employment_type: str | None = Field(default=None, max_length=100)
    job_url: HttpUrl | None = Field(default=None, max_length=2048)
    jd_analysis_id: UUID | None = None
    applied_date: date | None = None
    status: ApplicationStatus = "SAVED"
    notes: str | None = Field(default=None, max_length=10000)

    @field_validator("company", "job_title", "location", "employment_type")
    @classmethod
    def labels(cls, value):
        if value is None:
            return value
        value = value.strip()
        if not value or any(ord(char) < 32 for char in value):
            raise ValueError("Use a nonblank single-line label without control characters.")
        return value

    @field_validator("notes")
    @classmethod
    def notes_without_nulls(cls, value):
        if value is not None and "\0" in value:
            raise ValueError("Notes cannot contain null characters.")
        return value


class ApplicationUpdate(ApplicationCreate):
    company: str | None = Field(default=None, min_length=1, max_length=200)
    job_title: str | None = Field(default=None, min_length=1, max_length=200)
    status: ApplicationStatus | None = None

    @model_validator(mode="after")
    def require_nonnull_fields(self):
        for field in ("company", "job_title", "status"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null.")
        return self


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    company: str
    job_title: str
    location: str | None
    employment_type: str | None
    job_url: str | None
    jd_analysis_id: UUID | None
    applied_date: date | None
    status: ApplicationStatus
    notes: str | None
    created_at: datetime
    updated_at: datetime


class ApplicationList(BaseModel):
    items: list[ApplicationResponse]
    total: int
    limit: int
    offset: int
