from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class OccupationalAnchor(BaseModel):
    id: UUID
    title: str
    onet_soc_code: str


class CertificationGap(BaseModel):
    skill: str
    state: Literal["MISSING_EVIDENCE", "EVIDENCE_NEEDS_STRENGTHENING"]


class CertificationProvenance(BaseModel):
    source: str
    catalog_version: str
    source_url: str
    url_checked_on: str
    verification_status: Literal["OFFICIAL_PAGE_RETRIEVED", "FETCH_BLOCKED_HTTP_403"]
    verification_note: str
    coverage_basis: str
    limitations: str


class CertificationRecommendation(BaseModel):
    key: str
    name: str
    provider: str
    category: str
    relevant_skills: list[str]
    priority: int = Field(ge=1)
    reason: str
    gaps: list[CertificationGap]
    official_url: str
    provenance: CertificationProvenance


class CertificationRecommendationsResponse(BaseModel):
    target_role: str
    occupational_anchor: OccupationalAnchor
    snapshot_version: int
    model_version: str
    methodology: str
    recommendations: list[CertificationRecommendation]
    interpretation: str
