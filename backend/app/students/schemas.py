from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StudentProfileCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    phone: str | None = Field(default=None, max_length=30)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    headline: str | None = Field(default=None, max_length=200)
    bio: str | None = Field(default=None, max_length=2000)


class StudentProfileUpdate(BaseModel):
    full_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )
    phone: str | None = Field(default=None, max_length=30)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    headline: str | None = Field(default=None, max_length=200)
    bio: str | None = Field(default=None, max_length=2000)


class StudentProfileResponse(BaseModel):
    id: UUID
    user_id: UUID

    full_name: str
    phone: str | None
    city: str | None
    state: str | None
    country: str | None
    headline: str | None
    bio: str | None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
class EducationCreate(BaseModel):
    institution_name: str = Field(min_length=2, max_length=200)
    degree: str = Field(min_length=2, max_length=150)
    field_of_study: str | None = Field(default=None, max_length=150)
    start_year: int | None = Field(default=None, ge=1900, le=2100)
    end_year: int | None = Field(default=None, ge=1900, le=2100)
    grade: str | None = Field(default=None, max_length=50)


class EducationUpdate(BaseModel):
    institution_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=200,
    )
    degree: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )
    field_of_study: str | None = Field(default=None, max_length=150)
    start_year: int | None = Field(default=None, ge=1900, le=2100)
    end_year: int | None = Field(default=None, ge=1900, le=2100)
    grade: str | None = Field(default=None, max_length=50)


class EducationResponse(BaseModel):
    id: UUID
    user_id: UUID
    institution_name: str
    degree: str
    field_of_study: str | None
    start_year: int | None
    end_year: int | None
    grade: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
from pydantic import model_validator


class ExperienceCreate(BaseModel):
    company_name: str = Field(min_length=2, max_length=200)
    job_title: str = Field(min_length=2, max_length=150)
    employment_type: str | None = Field(default=None, max_length=50)
    location: str | None = Field(default=None, max_length=150)
    start_date: datetime | None = None
    end_date: datetime | None = None
    is_current: bool = False
    description: str | None = Field(default=None, max_length=3000)

    @model_validator(mode="after")
    def validate_dates(self):
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError(
                "end_date cannot be earlier than start_date."
            )

        if self.is_current and self.end_date is not None:
            raise ValueError(
                "Current experience cannot have an end_date."
            )

        return self


class ExperienceUpdate(BaseModel):
    company_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=200,
    )
    job_title: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )
    employment_type: str | None = Field(
        default=None,
        max_length=50,
    )
    location: str | None = Field(
        default=None,
        max_length=150,
    )
    start_date: datetime | None = None
    end_date: datetime | None = None
    is_current: bool | None = None
    description: str | None = Field(
        default=None,
        max_length=3000,
    )


class ExperienceResponse(BaseModel):
    id: UUID
    user_id: UUID
    company_name: str
    job_title: str
    employment_type: str | None
    location: str | None
    start_date: datetime | None
    end_date: datetime | None
    is_current: bool
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
class ProjectCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    role: str | None = Field(default=None, max_length=150)
    technologies: str | None = Field(default=None, max_length=2000)
    project_url: str | None = Field(default=None, max_length=500)
    repository_url: str | None = Field(default=None, max_length=500)
    start_date: datetime | None = None
    end_date: datetime | None = None
    is_ongoing: bool = False

    @model_validator(mode="after")
    def validate_dates(self):
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError(
                "end_date cannot be earlier than start_date."
            )

        if self.is_ongoing and self.end_date is not None:
            raise ValueError(
                "Ongoing project cannot have an end_date."
            )

        return self


class ProjectUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=2,
        max_length=200,
    )
    description: str | None = Field(
        default=None,
        max_length=5000,
    )
    role: str | None = Field(
        default=None,
        max_length=150,
    )
    technologies: str | None = Field(
        default=None,
        max_length=2000,
    )
    project_url: str | None = Field(
        default=None,
        max_length=500,
    )
    repository_url: str | None = Field(
        default=None,
        max_length=500,
    )
    start_date: datetime | None = None
    end_date: datetime | None = None
    is_ongoing: bool | None = None


class ProjectResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    description: str | None
    role: str | None
    technologies: str | None
    project_url: str | None
    repository_url: str | None
    start_date: datetime | None
    end_date: datetime | None
    is_ongoing: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
class CertificationCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=200,
    )
    issuing_organization: str = Field(
        min_length=2,
        max_length=200,
    )
    issue_date: datetime | None = None
    expiration_date: datetime | None = None
    credential_id: str | None = Field(
        default=None,
        max_length=200,
    )
    credential_url: str | None = Field(
        default=None,
        max_length=500,
    )
    description: str | None = Field(
        default=None,
        max_length=5000,
    )

    @model_validator(mode="after")
    def validate_dates(self):
        if (
            self.issue_date is not None
            and self.expiration_date is not None
            and self.expiration_date < self.issue_date
        ):
            raise ValueError(
                "expiration_date cannot be earlier than issue_date."
            )

        return self


class CertificationUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=200,
    )
    issuing_organization: str | None = Field(
        default=None,
        min_length=2,
        max_length=200,
    )
    issue_date: datetime | None = None
    expiration_date: datetime | None = None
    credential_id: str | None = Field(
        default=None,
        max_length=200,
    )
    credential_url: str | None = Field(
        default=None,
        max_length=500,
    )
    description: str | None = Field(
        default=None,
        max_length=5000,
    )


class CertificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    issuing_organization: str
    issue_date: datetime | None
    expiration_date: datetime | None
    credential_id: str | None
    credential_url: str | None
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)