from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.applications.models import Application
from backend.app.applications.schemas import ApplicationCreate, ApplicationUpdate
from backend.app.jobs.service import get_analysis


def get_application(db: Session, user_id: UUID, application_id: UUID) -> Application:
    result = db.scalar(select(Application).where(Application.id == application_id, Application.user_id == user_id))
    if result is None:
        raise HTTPException(404, "Application not found.")
    return result


def list_applications(db: Session, user_id: UUID, status: str | None, limit: int, offset: int) -> dict:
    conditions = [Application.user_id == user_id]
    if status is not None:
        conditions.append(Application.status == status)
    return {"items": list(db.scalars(select(Application).where(*conditions).order_by(Application.updated_at.desc(), Application.id.desc()).limit(limit).offset(offset)).all()),
            "total": db.scalar(select(func.count()).select_from(Application).where(*conditions)), "limit": limit, "offset": offset}


def _values(db, user_id, payload):
    values = payload.model_dump(exclude_unset=True)
    if values.get("jd_analysis_id") is not None:
        get_analysis(db, user_id, values["jd_analysis_id"])
    if values.get("job_url") is not None:
        values["job_url"] = str(values["job_url"])
    return values


def create_application(db: Session, user_id: UUID, payload: ApplicationCreate) -> Application:
    values = _values(db, user_id, payload)
    item = Application(user_id=user_id, **values)
    try:
        db.add(item); db.commit(); db.refresh(item)
    except Exception:
        db.rollback(); raise
    return item


def update_application(db: Session, user_id: UUID, application_id: UUID, payload: ApplicationUpdate) -> Application:
    item = get_application(db, user_id, application_id)
    values = _values(db, user_id, payload)
    if not values:
        return item
    try:
        for key, value in values.items():
            setattr(item, key, value)
        item.updated_at = datetime.now(timezone.utc)
        db.commit(); db.refresh(item)
    except Exception:
        db.rollback(); raise
    return item


def delete_application(db: Session, user_id: UUID, application_id: UUID) -> None:
    item = get_application(db, user_id, application_id)
    try:
        db.delete(item); db.commit()
    except Exception:
        db.rollback(); raise
