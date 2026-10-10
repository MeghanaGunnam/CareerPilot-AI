from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


ROADMAP_STATUSES = ("NOT_STARTED", "IN_PROGRESS", "COMPLETED", "SKIPPED")


class RoadmapItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    item_key: str
    provenance: str
    current_evidence_state: str
    reason: str
    recommended_action: str
    evidence_building_action: str
    milestone: str
    status: str
    display_order: int = Field(
        validation_alias="display_order",
        serialization_alias="order",
    )
    model_version: str
    snapshot_version: int


class RoadmapResponse(BaseModel):
    career_goal_id: UUID
    target_role: str
    career_id: UUID
    items: list[RoadmapItemResponse]


class RoadmapItemStatusUpdate(BaseModel):
    status: str = Field(pattern="^(NOT_STARTED|IN_PROGRESS|COMPLETED|SKIPPED)$")
