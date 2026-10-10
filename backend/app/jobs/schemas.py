"""Public contract: quotes use zero-based, end-exclusive Unicode code-point offsets."""
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

MAX_SOURCE_LENGTH = 30000
MAX_REQUIREMENTS = 100
RequirementGroup = Literal["technology", "experience", "education", "responsibility", "preferred"]


class JDAnalysisCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    company: str | None = Field(default=None, max_length=200)
    source_url: HttpUrl | None = Field(default=None, max_length=2048)
    source_text: str = Field(min_length=1, max_length=MAX_SOURCE_LENGTH)

    @field_validator("title", "company")
    @classmethod
    def clean_label(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value or any(ord(char) < 32 for char in value):
            raise ValueError("Use a nonblank, single-line label without control characters.")
        return value

    @field_validator("source_text")
    @classmethod
    def validate_source(cls, value: str) -> str:
        if not value.strip() or "\x00" in value:
            raise ValueError("Job description must contain text without null characters.")
        # Do not strip: every persisted quote points into the original pasted text.
        return value


class RequirementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    position: int
    group: RequirementGroup = Field(description="Deterministic inferred grouping, not a literal claim of mandatory status.")
    quote: str
    source_start: int
    source_end: int
    evidence_type: Literal["FACT_FROM_JD"] = Field(description="Applies only to the verbatim quote; grouping and canonical labels are interpretations.")
    normalized_name: str | None = Field(description="Known canonical technology alias interpretation, otherwise null.")
    interpretation_type: Literal["NORMALIZED_INTERPRETATION"] | None


class JDAnalysisSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    company: str | None
    source_url: str | None
    created_at: datetime
    extractor_version: str
    requirement_count: int
    truncated: bool


class JDAnalysisResponse(JDAnalysisSummary):
    source_text: str
    requirements: list[RequirementResponse]


class JDAnalysisList(BaseModel):
    items: list[JDAnalysisSummary]
    total: int
    limit: int
    offset: int
