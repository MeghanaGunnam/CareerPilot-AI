import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CareerTwinSnapshotResponse(BaseModel):
    id: uuid.UUID
    career_twin_id: uuid.UUID
    version: int
    trigger_type: str
    state_data: dict
    schema_version: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CareerTwinEventResponse(BaseModel):
    id: uuid.UUID
    event_type: str
    source_type: str
    source_reference: str | None
    event_data: dict
    occurred_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CareerTwinResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    current_version: int
    created_at: datetime
    updated_at: datetime
    latest_snapshot: CareerTwinSnapshotResponse | None


class CareerTwinHistoryResponse(BaseModel):
    career_twin_id: uuid.UUID
    current_version: int
    snapshots: list[CareerTwinSnapshotResponse]