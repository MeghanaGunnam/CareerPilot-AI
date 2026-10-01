import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CareerTwin(Base):
    __tablename__ = "career_twins"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            name="uq_career_twin_user",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    current_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    events = relationship(
        "CareerTwinEvent",
        back_populates="career_twin",
        cascade="all, delete-orphan",
    )

    snapshots = relationship(
        "CareerTwinSnapshot",
        back_populates="career_twin",
        cascade="all, delete-orphan",
    )


class CareerTwinEvent(Base):
    __tablename__ = "career_twin_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    career_twin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "career_twins.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    source_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    source_reference: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    event_data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        index=True,
    )

    career_twin = relationship(
        "CareerTwin",
        back_populates="events",
    )


class CareerTwinSnapshot(Base):
    __tablename__ = "career_twin_snapshots"

    __table_args__ = (
        UniqueConstraint(
            "career_twin_id",
            "version",
            name="uq_career_twin_snapshot_version",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    career_twin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "career_twins.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    trigger_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    state_data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    schema_version: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="1.0",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        index=True,
    )

    career_twin = relationship(
        "CareerTwin",
        back_populates="snapshots",
    )