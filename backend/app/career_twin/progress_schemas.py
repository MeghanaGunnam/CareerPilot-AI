from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class RecordedCounts(BaseModel):
    skill_records: int | None
    evidence_entries: int | None
    assessment_evidence_entries: int | None


class SnapshotSummary(BaseModel):
    id: UUID
    version: int
    schema_version: str
    created_at: datetime
    trigger_type: str
    counts: RecordedCounts


class RecordedChange(BaseModel):
    key: str
    label: str
    current_recorded_value: int | None
    previous_recorded_value: int | None
    change: int | None


class ProgressEvent(BaseModel):
    id: UUID
    event_type: str
    source_type: str
    occurred_at: datetime
    snapshot_version: int | None


class ProgressResponse(BaseModel):
    career_twin_id: UUID | None
    history_status: Literal["COMPARABLE_HISTORY", "NOT_ENOUGH_HISTORY"]
    history_message: str
    current_snapshot: SnapshotSummary | None
    previous_snapshot: SnapshotSummary | None
    comparison: list[RecordedChange]
    snapshots: list[SnapshotSummary]
    snapshot_total: int
    limit: int
    offset: int
    events: list[ProgressEvent]
    event_total: int
    event_offset: int
    roadmap_status_counts: dict[str, int]
    roadmap_total: int
    completed_assessment_attempts: int
    interpretation: str
