"""Historical counts from recorded snapshots, never backfilled ACIF scores."""
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.assessments.models import AssessmentAttempt
from backend.app.career_twin.models import CareerTwinEvent, CareerTwinSnapshot
from backend.app.career_twin.service import get_career_twin
from backend.app.roadmap.models import RoadmapItem
from backend.app.roadmap.schemas import ROADMAP_STATUSES

METRICS = {"skill_records": "Recorded skill entries", "evidence_entries": "Recorded evidence entries", "assessment_evidence_entries": "Recorded assessment evidence entries"}


def recorded_counts(snapshot) -> dict:
    unknown = dict.fromkeys(METRICS)
    if snapshot.schema_version != "1.0" or not isinstance(snapshot.state_data, dict):
        return unknown
    skills = snapshot.state_data.get("skills")
    if not isinstance(skills, list) or any(not isinstance(skill, dict) for skill in skills):
        return unknown
    result = {**unknown, "skill_records": len(skills)}
    if any(not isinstance(skill.get("evidence"), list) for skill in skills):
        return result
    entries = [entry for skill in skills for entry in skill["evidence"]]
    if any(not isinstance(entry, dict) for entry in entries):
        return result
    result["evidence_entries"] = len(entries)
    if all(isinstance(entry.get("source_type"), str) for entry in entries):
        result["assessment_evidence_entries"] = sum(entry["source_type"].upper() == "ASSESSMENT" for entry in entries)
    return result


def snapshot_summary(snapshot):
    if snapshot is None:
        return None
    return {"id": snapshot.id, "version": snapshot.version, "schema_version": snapshot.schema_version,
            "created_at": snapshot.created_at, "trigger_type": snapshot.trigger_type, "counts": recorded_counts(snapshot)}


def compare_snapshots(current, previous):
    current_counts = recorded_counts(current) if current else dict.fromkeys(METRICS)
    previous_counts = recorded_counts(previous) if previous else dict.fromkeys(METRICS)
    comparable = bool(current and previous and current.schema_version == previous.schema_version)
    return [{"key": key, "label": label, "current_recorded_value": current_counts[key],
             "previous_recorded_value": previous_counts[key],
             "change": current_counts[key] - previous_counts[key] if comparable and current_counts[key] is not None and previous_counts[key] is not None else None}
            for key, label in METRICS.items()]


def get_progress(db: Session, user_id: UUID, limit: int = 20, offset: int = 0, event_offset: int = 0) -> dict:
    twin = get_career_twin(db, user_id)
    snapshots, latest, events = [], [], []
    snapshot_total = event_total = 0
    if twin:
        owner = CareerTwinSnapshot.career_twin_id == twin.id
        query = select(CareerTwinSnapshot).where(owner).order_by(CareerTwinSnapshot.version.desc())
        snapshots = list(db.scalars(query.limit(limit).offset(offset)).all())
        latest = list(db.scalars(query.limit(2)).all())
        snapshot_total = db.scalar(select(func.count()).select_from(CareerTwinSnapshot).where(owner))
        event_owner = CareerTwinEvent.career_twin_id == twin.id
        event_rows = db.scalars(select(CareerTwinEvent).where(event_owner).order_by(CareerTwinEvent.occurred_at.desc(), CareerTwinEvent.id.desc()).limit(limit).offset(event_offset)).all()
        event_total = db.scalar(select(func.count()).select_from(CareerTwinEvent).where(event_owner))
        for event in event_rows:
            version = event.event_data.get("snapshot_version") if isinstance(event.event_data, dict) else None
            events.append({"id": event.id, "event_type": event.event_type, "source_type": event.source_type,
                           "occurred_at": event.occurred_at, "snapshot_version": version if type(version) is int and version > 0 else None})
    current = latest[0] if latest else None
    previous = latest[1] if len(latest) > 1 else None
    comparison = compare_snapshots(current, previous)
    comparable = any(row["change"] is not None for row in comparison)
    roadmap_counts = dict.fromkeys(ROADMAP_STATUSES, 0)
    # Read existing rows only: get_roadmap would generate/commit new items.
    for status, count in db.execute(select(RoadmapItem.status, func.count()).where(RoadmapItem.user_id == user_id).group_by(RoadmapItem.status)).all():
        key = status if status in roadmap_counts else "OTHER_RECORDED_STATUS"
        roadmap_counts[key] = roadmap_counts.get(key, 0) + count
    completed = db.scalar(select(func.count()).select_from(AssessmentAttempt).where(
        AssessmentAttempt.user_id == user_id, AssessmentAttempt.status == "COMPLETED", AssessmentAttempt.completed_at.is_not(None)))
    return {
        "career_twin_id": twin.id if twin else None,
        "history_status": "COMPARABLE_HISTORY" if comparable else "NOT_ENOUGH_HISTORY",
        "history_message": "Comparison of the latest two recorded snapshots, not continuous tracking." if comparable else "Not enough history yet.",
        "current_snapshot": snapshot_summary(current), "previous_snapshot": snapshot_summary(previous),
        "comparison": comparison, "snapshots": [snapshot_summary(snapshot) for snapshot in snapshots],
        "snapshot_total": snapshot_total, "limit": limit, "offset": offset,
        "events": events, "event_total": event_total, "event_offset": event_offset,
        "roadmap_status_counts": roadmap_counts, "roadmap_total": sum(roadmap_counts.values()),
        "completed_assessment_attempts": completed,
        "interpretation": "Historical values are counts of entries actually stored in compatible snapshots. Missing fields or unknown schemas are unavailable, not zero. Evidence-entry counts do not establish proficiency. Historical ACIF technology/competency coverage and strength were not captured here and are not reconstructed. Roadmap statuses (all your persisted goals) and completed assessment attempts are current database totals, not historical series. No history, event or completion is inferred or written.",
    }
