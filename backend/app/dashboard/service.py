from typing import get_args

from fastapi import HTTPException
from sqlalchemy import func, select

from backend.app.applications.models import Application
from backend.app.applications.schemas import ApplicationStatus
from backend.app.assistant.service import provider_status
from backend.app.career_twin.progress import get_progress
from backend.app.certification_recommendations.service import get_certification_recommendations
from backend.app.jobs.matching import get_job_match
from backend.app.jobs.service import list_analyses
from backend.app.resumes.models import Resume


def get_dashboard_summary(db, user_id, provider):
    progress = get_progress(db, user_id, limit=1)
    applications = dict.fromkeys(get_args(ApplicationStatus), 0)
    for status, count in db.execute(select(Application.status, func.count()).where(Application.user_id == user_id).group_by(Application.status)).all():
        applications[status] = count
    recent = list_analyses(db, user_id, limit=1)["items"]
    latest = recent[0] if recent else None
    alignment = get_job_match(db, user_id, latest.id)["alignment"] if latest else None
    certificates, certification_status = [], "UNAVAILABLE"
    try:
        recommendations = get_certification_recommendations(db, user_id)
        certificates = [{"name": item["name"], "provider": item["provider"]} for item in recommendations["recommendations"][:2]]
        certification_status = "AVAILABLE"
    except HTTPException as error:
        if error.status_code != 404:
            raise
    change = next((row["change"] for row in progress["comparison"] if row["key"] == "evidence_entries"), None)
    return {
        "resume_count": db.scalar(select(func.count()).select_from(Resume).where(Resume.user_id == user_id)),
        "completed_assessment_attempts": progress["completed_assessment_attempts"],
        "roadmap_status_counts": progress["roadmap_status_counts"], "roadmap_total": progress["roadmap_total"],
        "certification_status": certification_status, "certification_preview": certificates,
        "latest_jd": latest, "latest_alignment": alignment,
        "application_status_counts": applications, "application_total": sum(applications.values()),
        "progress": {"message": progress["history_message"], "snapshot_version": progress["current_snapshot"]["version"] if progress["current_snapshot"] else None, "evidence_entry_change": change},
        "assistant": provider_status(provider),
    }
