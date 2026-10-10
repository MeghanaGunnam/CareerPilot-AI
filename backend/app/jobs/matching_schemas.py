from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from backend.app.jobs.schemas import RequirementResponse

MatchState = Literal["EVIDENCE_BACKED_ALIGNMENT", "EVIDENCE_NEEDS_STRENGTHENING", "MISSING_EVIDENCE", "NOT_ASSESSED", "UNKNOWN_OR_UNMAPPED"]
Strength = Literal["EXPLICIT_REQUIRED", "OPTIONAL_OR_PREFERRED", "NEGATED_OR_NON_REQUIRED", "UNCERTAIN"]


class EvidenceSummary(BaseModel):
    skill_id: str | None = None
    evidence_count: int = 0
    source_types: list[str] = []
    evidence_families: list[str] = []
    evidence_ids: list[str] = []
    evidence_confidence: float | None = None
    assessment_measurement: float | None = None
    measurement_status: Literal["ASSESSMENT_MEASUREMENT_AVAILABLE", "NOT_ASSESSED"] = "NOT_ASSESSED"


class MatchAction(BaseModel):
    label: str
    href: Literal["/evidence", "/assessment", "/roadmap", "/certifications"]
    provenance: str


class RequirementMatch(BaseModel):
    requirement: RequirementResponse
    canonical_technology: str | None
    strength: Strength
    strength_explanation: str
    state: MatchState
    evidence: EvidenceSummary
    explanation: str
    included_in_alignment: bool
    exclusion_reason: str | None
    actions: list[MatchAction]


class EvidenceAlignment(BaseModel):
    label: Literal["CareerPilot Evidence Alignment"] = "CareerPilot Evidence Alignment"
    value: float | None
    numerator: int
    denominator: int
    eligible_technologies: list[str]
    methodology: str


class JDMatchResponse(BaseModel):
    analysis_id: UUID
    status: Literal["AVAILABLE", "UNAVAILABLE"]
    unavailable_reason: str | None
    career_twin_id: UUID | None
    snapshot_version: int | None
    snapshot_created_at: datetime | None
    evaluated_at: datetime
    model_version: str
    matching_version: str
    extractor_version: str
    requirements: list[RequirementMatch]
    alignment: EvidenceAlignment
    interpretation: str
