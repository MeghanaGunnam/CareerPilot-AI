import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AssessmentAttemptSummaryResponse(BaseModel):
    attempt_id: uuid.UUID
    assessment_id: uuid.UUID
    assessment_title: str
    assessment_version: int
    skill_id: uuid.UUID
    skill_name: str
    status: str
    raw_score: int | None
    total_questions: int | None
    percentage: float | None
    started_at: datetime
    completed_at: datetime | None


class AssessmentCatalogMetadataResponse(BaseModel):
    catalog_id: str
    version: int
    skill_name: str
    title: str
    domain: str
    is_active: bool
    provenance: str


class AssessmentListItemResponse(BaseModel):
    id: uuid.UUID
    skill_id: uuid.UUID
    skill_name: str
    title: str
    description: str | None
    difficulty: str
    version: int
    question_count: int
    latest_attempt: AssessmentAttemptSummaryResponse | None = None
    catalog_metadata: AssessmentCatalogMetadataResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class AssessmentQuestionResponse(BaseModel):
    id: uuid.UUID
    position: int
    question_text: str
    options: list[dict[str, str]]

    model_config = ConfigDict(from_attributes=True)


class AssessmentDetailResponse(BaseModel):
    catalog_metadata: AssessmentCatalogMetadataResponse | None = None
    id: uuid.UUID
    skill_id: uuid.UUID
    skill_name: str
    title: str
    description: str | None
    difficulty: str
    version: int
    questions: list[AssessmentQuestionResponse]


class AssessmentAnswerSubmit(BaseModel):
    question_id: uuid.UUID
    selected_option: str = Field(min_length=1, max_length=10)


class AssessmentSubmitRequest(BaseModel):
    answers: list[AssessmentAnswerSubmit]


class AssessmentAnswerResult(BaseModel):
    question_id: uuid.UUID
    selected_option: str
    correct_option: str
    is_correct: bool
    explanation: str | None


class AssessmentAttemptResultResponse(AssessmentAttemptSummaryResponse):
    answers: list[AssessmentAnswerResult]


class AssessmentCompetencyResponse(BaseModel):
    element_id: str
    element_name: str
    skill_type: str
    importance: float | None
    level: float | None
    mapping_type: str
    mapping_version: str
    mapping_rationale: str | None


class AssessmentSoftwareSignalResponse(BaseModel):
    requirement_id: uuid.UUID
    workplace_example: str
    canonical_technology: str
    in_demand: bool
    hot_technology: bool
    onet_version: str
    mapping_type: str


class AssessmentRecommendationResponse(BaseModel):
    assessment_id: uuid.UUID
    skill_id: uuid.UUID
    skill_name: str
    title: str
    description: str | None
    difficulty: str
    version: int

    career_id: uuid.UUID
    career_title: str
    onet_soc_code: str | None

    competency: AssessmentCompetencyResponse | None = None
    recommendation_type: str = "COMPETENCY"
    software_signal: AssessmentSoftwareSignalResponse | None = None

    recommendation_status: str
    reason: str


class CareerAssessmentRecommendationsResponse(BaseModel):
    career_goal_id: uuid.UUID | None = None
    career_id: uuid.UUID
    career_title: str
    onet_soc_code: str | None

    recommended_count: int
    recommendations: list[
        AssessmentRecommendationResponse
    ]

    interpretation: str
