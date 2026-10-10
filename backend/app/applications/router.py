from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User
from backend.app.core.database import get_db
from backend.app.applications import service
from backend.app.applications.schemas import ApplicationCreate, ApplicationList, ApplicationResponse, ApplicationStatus, ApplicationUpdate

router = APIRouter(prefix="/api/v1/applications", tags=["Applications"])


@router.post("", response_model=ApplicationResponse, status_code=201)
def create(payload: ApplicationCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.create_application(db, user.id, payload)


@router.get("", response_model=ApplicationList)
def listing(status: ApplicationStatus | None = None, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0, le=1000000), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.list_applications(db, user.id, status, limit, offset)


@router.get("/{application_id}", response_model=ApplicationResponse)
def detail(application_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.get_application(db, user.id, application_id)


@router.patch("/{application_id}", response_model=ApplicationResponse)
def update(application_id: UUID, payload: ApplicationUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.update_application(db, user.id, application_id, payload)


@router.delete("/{application_id}", status_code=204)
def delete(application_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service.delete_application(db, user.id, application_id)
    return Response(status_code=204)
