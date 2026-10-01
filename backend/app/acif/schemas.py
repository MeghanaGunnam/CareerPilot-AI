from typing import Any

from pydantic import BaseModel, Field


class EvidenceDetailResponse(BaseModel):
    evidence_id: str | None = None
    family: str
    source_type: str
    status: str
    source_reliability: float
    status_reliability: float
    freshness: float
    strength: float | None = None
    support: float


class SkillStateResponse(BaseModel):
    student_skill_id: str | None = None
    skill_id: str | None = None
    name: str
    category: str | None = None
    model_version: str
    evidence_count: int
    evidence_families: list[str]
    family_support: dict[str, float]
    evidence_confidence: float
    freshness_score: float
    estimated_proficiency: float | None = None
    verified_skill_state: float | None = None
    evidence_details: list[EvidenceDetailResponse]


class AcifSkillStateResponse(BaseModel):
    career_twin_id: str
    snapshot_version: int
    model_version: str
    skills: list[SkillStateResponse]


class SkillEvidenceSimulationRequest(BaseModel):
    simulation_type: str = "ADD_SKILL_EVIDENCE"
    skill_name: str = Field(
        min_length=1,
        max_length=200,
    )
    simulated_confidence: float = Field(
        ge=0.0,
        le=1.0,
    )