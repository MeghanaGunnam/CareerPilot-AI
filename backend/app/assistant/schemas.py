from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

Topic = Literal["auto", "next_steps", "skills", "profile", "assessments", "certifications", "job_match", "applications", "progress"]
ProviderStatus = Literal["READY", "ASSISTANT_NOT_CONFIGURED", "CONSENT_REQUIRED", "PROVIDER_UNAVAILABLE"]


class AssistantRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str = Field(min_length=1, max_length=2000)
    topic: Topic = "auto"
    jd_analysis_id: UUID | None = None
    application_id: UUID | None = None
    allow_provider_processing: bool = False

    @field_validator("message")
    @classmethod
    def nonblank(cls, value):
        if not value.strip() or "\0" in value:
            raise ValueError("Enter a nonblank question without null characters.")
        return value.strip()


class GroundingSource(BaseModel):
    id: str
    kind: Literal["FACT", "MODEL_OUTPUT", "PERSONALIZED_RECOMMENDATION"]
    text: str
    provenance: str
    href: Literal["/profile", "/assessment", "/roadmap", "/certifications", "/job-match", "/applications", "/progress", "/evidence", "/dashboard"]


class ProviderSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_ids: list[str] = Field(max_length=8)


class AssistantStatus(BaseModel):
    provider_status: ProviderStatus
    mode: Literal["STRUCTURED_GROUNDING"] = "STRUCTURED_GROUNDING"
    generation_mode: Literal["CONSTRAINED_SOURCE_SELECTION"] = "CONSTRAINED_SOURCE_SELECTION"
    message: str


class AssistantResponse(AssistantStatus):
    answer: str | None
    grounding_status: Literal["GROUNDED_SELECTION", "INSUFFICIENT_CONTEXT", "UNAVAILABLE"]
    topic: Topic
    context_sources: list[GroundingSource] = []
    recommended_actions: list[GroundingSource] = []
    limitations: list[str] = []
    explanation_provenance: Literal["LLM_EXPLANATION_SELECTION", "NO_GENERATION"] = "NO_GENERATION"
