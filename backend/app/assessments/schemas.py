import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AssessmentListItemResponse(BaseModel):
    id: uuid.UUID
    skill_id: uuid.UUID
    skill_name: str
    title: str
    description: str | None
    difficulty: str
    version: int

    model_config = ConfigDict(from_attributes=True)


class AssessmentQuestionResponse(BaseModel):
    id: uuid.UUID
    position: int
    question_text: str
    options: list[dict[str, str]]

    model_config = ConfigDict(from_attributes=True)


class AssessmentDetailResponse(BaseModel):
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


class AssessmentAttemptResultResponse(BaseModel):
    attempt_id: uuid.UUID
    assessment_id: uuid.UUID
    skill_id: uuid.UUID
    skill_name: str
    status: str
    raw_score: int
    total_questions: int
    percentage: float
    completed_at: datetime
    answers: list[AssessmentAnswerResult]