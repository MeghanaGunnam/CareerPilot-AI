from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RiasecQuestionResponse(BaseModel):
    id: str
    dimension: str
    text: str


class RiasecResponseOption(BaseModel):
    value: int
    label: str


class RiasecQuestionnaireResponse(BaseModel):
    assessment_version: str
    instructions: str
    questions: list[RiasecQuestionResponse]
    response_options: list[RiasecResponseOption]


class RiasecAnswerRequest(BaseModel):
    question_id: str

    response_value: int = Field(
        ge=1,
        le=5,
    )


class RiasecAssessmentRequest(BaseModel):
    answers: list[RiasecAnswerRequest]


class RiasecScoresResponse(BaseModel):
    realistic: float
    investigative: float
    artistic: float
    social: float
    enterprising: float
    conventional: float


class RiasecProfileResponse(BaseModel):
    id: UUID
    assessment_id: UUID
    scores: RiasecScoresResponse
    dominant_code: str
    scoring_version: str
    created_at: datetime


class RiasecAssessmentResultResponse(BaseModel):
    assessment_id: UUID
    assessment_version: str
    status: str
    completed_at: datetime
    profile: RiasecProfileResponse


class CareerInterestMatchResponse(BaseModel):
    career_id: UUID
    onet_soc_code: str
    title: str
    description: str | None
    job_zone: int | None

    interest_alignment: float = Field(
        ge=0.0,
        le=1.0,
    )

    interest_alignment_percent: float = Field(
        ge=0.0,
        le=100.0,
    )

    career_riasec: RiasecScoresResponse

    dominant_code: str