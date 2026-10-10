from typing import Literal

from pydantic import BaseModel

from backend.app.assistant.schemas import AssistantStatus
from backend.app.jobs.schemas import JDAnalysisSummary
from backend.app.jobs.matching_schemas import EvidenceAlignment


class CertificationPreview(BaseModel):
    name: str
    provider: str


class ProgressPreview(BaseModel):
    message: str
    snapshot_version: int | None
    evidence_entry_change: int | None


class DashboardSummary(BaseModel):
    resume_count: int
    completed_assessment_attempts: int
    roadmap_status_counts: dict[str, int]
    roadmap_total: int
    certification_status: Literal["AVAILABLE", "UNAVAILABLE"]
    certification_preview: list[CertificationPreview]
    latest_jd: JDAnalysisSummary | None
    latest_alignment: EvidenceAlignment | None
    application_status_counts: dict[str, int]
    application_total: int
    progress: ProgressPreview
    assistant: AssistantStatus
