from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from backend.app.jobs.extractor import EXTRACTOR_VERSION, extract_requirements
from backend.app.jobs.models import JDAnalysis, Requirement
from backend.app.jobs.schemas import JDAnalysisCreate


def create_analysis(db: Session, user_id: UUID, payload: JDAnalysisCreate) -> JDAnalysis:
    """Save one immutable extraction atomically; each POST creates a new record.

    No project-wide idempotency-key pattern exists. A lost response after commit
    can therefore leave a saved record: callers should inspect history before
    retrying an uncertain POST. Reads never regenerate historical extraction.
    """
    extracted, truncated = extract_requirements(payload.source_text)
    analysis = JDAnalysis(
        user_id=user_id, title=payload.title, company=payload.company,
        source_url=str(payload.source_url) if payload.source_url else None,
        source_text=payload.source_text, extractor_version=EXTRACTOR_VERSION,
        requirement_count=len(extracted), truncated=truncated,
        requirements=[Requirement(
            position=position, group=item.group, quote=item.quote,
            source_start=item.source_start, source_end=item.source_end,
            evidence_type=item.evidence_type, normalized_name=item.normalized_name,
            interpretation_type=item.interpretation_type,
        ) for position, item in enumerate(extracted)],
    )
    try:
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return analysis
    except Exception:
        db.rollback()
        raise


def list_analyses(db: Session, user_id: UUID, limit: int = 20, offset: int = 0) -> dict:
    owner = JDAnalysis.user_id == user_id
    return {
        "items": list(db.scalars(select(JDAnalysis).where(owner)
                               .order_by(JDAnalysis.created_at.desc(), JDAnalysis.id.desc())
                               .limit(limit).offset(offset)).all()),
        "total": db.scalar(select(func.count()).select_from(JDAnalysis).where(owner)),
        "limit": limit, "offset": offset,
    }


def get_analysis(db: Session, user_id: UUID, analysis_id: UUID) -> JDAnalysis:
    analysis = db.scalar(select(JDAnalysis).options(selectinload(JDAnalysis.requirements)).where(
        JDAnalysis.id == analysis_id, JDAnalysis.user_id == user_id,
    ))
    if analysis is None:
        raise HTTPException(status_code=404, detail="Job description analysis not found.")
    return analysis
