from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SkillEvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_type: str
    source_reference: str
    source_section: str | None
    evidence_text: str | None
    evidence_status: str
    evidence_strength: float | None
    observed_at: datetime


class StudentSkillResponse(BaseModel):
    id: UUID
    skill_id: UUID
    canonical_name: str
    category: str | None

    claimed_proficiency: float | None
    estimated_proficiency: float | None
    evidence_confidence: float | None
    freshness_score: float | None
    last_verified_at: datetime | None

    evidence: list[SkillEvidenceResponse]


class StudentSkillsSummaryResponse(BaseModel):
    total_skills: int
    total_evidence: int
    skills: list[StudentSkillResponse]