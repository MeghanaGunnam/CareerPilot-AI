from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User
from backend.app.core.database import get_db
from backend.app.jobs.schemas import JDAnalysisCreate, JDAnalysisList, JDAnalysisResponse
from backend.app.jobs.service import create_analysis, get_analysis, list_analyses
from backend.app.jobs.matching import get_job_match
from backend.app.jobs.matching_schemas import JDMatchResponse

router = APIRouter(prefix="/api/v1/jobs/analyses", tags=["Job descriptions"])


@router.post("", response_model=JDAnalysisResponse, status_code=201)
def create_analysis_endpoint(payload: JDAnalysisCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return create_analysis(db=db, user_id=current_user.id, payload=payload)


@router.get("", response_model=JDAnalysisList)
def list_analyses_endpoint(limit: int = Query(default=20, ge=1, le=100), offset: int = Query(default=0, ge=0, le=1000000), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return list_analyses(db=db, user_id=current_user.id, limit=limit, offset=offset)


@router.get("/{analysis_id}", response_model=JDAnalysisResponse)
def get_analysis_endpoint(analysis_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_analysis(db=db, user_id=current_user.id, analysis_id=analysis_id)


@router.get("/{analysis_id}/match", response_model=JDMatchResponse)
def get_job_match_endpoint(analysis_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_job_match(db=db, user_id=current_user.id, analysis_id=analysis_id)
