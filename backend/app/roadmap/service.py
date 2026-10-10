from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.acif.service import get_minimum_action_path
from backend.app.careers.models import Career
from backend.app.roadmap.models import RoadmapItem
from backend.app.students.models import CareerGoal
from backend.app.students.service import get_user_primary_career_goal


def _action_value(action: dict, key: str) -> str:
    value = action.get(key)
    return str(value) if value is not None else "Not available in current evidence."


def _build_item_fields(action: dict, goal: CareerGoal, path_result: dict, order: int) -> dict:
    subject = action.get("technology") or action.get("competency") or "career requirement"
    action_type = action.get("action_type", "ACIF_ACTION")
    confidence = action.get("current_evidence_confidence")
    if confidence is None:
        evidence_state = "NOT_ASSESSED"
    else:
        evidence_state = f"Evidence confidence: {confidence:.2f}"
    if action_type == "STRENGTHEN_EVIDENCE":
        evidence_action = f"Complete and document a relevant project, assessment, certification, or experience demonstrating {subject}."
        milestone = f"A verifiable evidence record for {subject} is added to the Career Twin."
    else:
        evidence_action = f"Complete an appropriate CareerPilot assessment or provide valid evidence for {subject}."
        milestone = f"CareerPilot records a measured competency state for {subject}."
    return {
        "item_key": f"{action_type}:{str(subject).strip().lower()}",
        "provenance": "ACIF_MINIMUM_ACTION_PATH",
        "current_evidence_state": evidence_state,
        "reason": action.get("selection_reason") or action.get("reason") or "ACIF identified this as a current career requirement.",
        "recommended_action": _action_value(action, "recommended_action"),
        "evidence_building_action": evidence_action,
        "milestone": milestone,
        "display_order": order,
        "model_version": path_result["model_version"],
        "snapshot_version": path_result["snapshot_version"],
        "user_id": goal.user_id,
        "career_goal_id": goal.id,
    }


def get_roadmap(db: Session, user_id: UUID) -> dict:
    goal = get_user_primary_career_goal(db=db, user_id=user_id)
    if goal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Primary career goal not found.")
    if not goal.onet_soc_code:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Primary career goal has no target career mapping.")
    career = db.scalar(select(Career).where(Career.onet_soc_code == goal.onet_soc_code))
    if career is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target career is not available for ACIF roadmap generation.")
    path_result = get_minimum_action_path(db=db, user_id=user_id, career_id=career.id)
    actions = path_result["minimum_action_path"].get("path", [])
    if not actions:
        return {"career_goal_id": goal.id, "target_role": goal.target_role, "career_id": career.id, "items": []}

    existing = {item.item_key: item for item in db.scalars(select(RoadmapItem).where(RoadmapItem.user_id == user_id, RoadmapItem.career_goal_id == goal.id)).all()}
    items = []
    for order, action in enumerate(actions, start=1):
        fields = _build_item_fields(action, goal, path_result, order)
        item = existing.get(fields["item_key"])
        if item is None:
            item = RoadmapItem(status="NOT_STARTED", **fields)
            db.add(item)
        else:
            current_status = item.status
            for key, value in fields.items():
                setattr(item, key, value)
            item.status = current_status
        items.append(item)
    db.commit()
    for item in items:
        db.refresh(item)
    return {"career_goal_id": goal.id, "target_role": goal.target_role, "career_id": career.id, "items": items}


def update_roadmap_item_status(db: Session, user_id: UUID, item_id: UUID, new_status: str) -> RoadmapItem:
    item = db.scalar(select(RoadmapItem).where(RoadmapItem.id == item_id, RoadmapItem.user_id == user_id))
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap item not found.")
    item.status = new_status
    db.commit()
    db.refresh(item)
    return item
