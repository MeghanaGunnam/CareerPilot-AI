from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from backend.app.careers.models import Career
from backend.app.careers.schemas import (
    CareerDetailResponse,
    CareerListResponse,
)
from backend.app.core.database import get_db


router = APIRouter(
    prefix="/api/v1/careers",
    tags=["Careers"],
)


@router.get(
    "",
    response_model=list[CareerListResponse],
)
def list_careers(
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
    ),
    job_zone: int | None = Query(
        default=None,
        ge=1,
        le=5,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    db: Session = Depends(get_db),
):
    statement = select(Career)

    if search:
        search_value = f"%{search.strip()}%"

        statement = statement.where(
            or_(
                Career.title.ilike(search_value),
                Career.onet_soc_code.ilike(search_value),
            )
        )

    if job_zone is not None:
        statement = statement.where(
            Career.job_zone == job_zone
        )

    statement = (
        statement
        .order_by(Career.title)
        .offset(offset)
        .limit(limit)
    )

    return list(
        db.scalars(statement).all()
    )


@router.get(
    "/count",
)
def count_careers(
    db: Session = Depends(get_db),
):
    count = db.scalar(
        select(func.count()).select_from(Career)
    )

    return {
        "count": count,
    }


@router.get(
    "/{career_id}",
    response_model=CareerDetailResponse,
)
def get_career(
    career_id: UUID,
    db: Session = Depends(get_db),
):
    statement = (
        select(Career)
        .options(
            selectinload(Career.riasec_profile)
        )
        .where(
            Career.id == career_id
        )
    )

    career = db.scalar(statement)

    if career is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Career not found.",
        )

    return career