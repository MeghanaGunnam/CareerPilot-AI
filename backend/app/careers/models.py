import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


class Career(Base):
    __tablename__ = "careers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    onet_soc_code: Mapped[str] = mapped_column(
        String(10),
        unique=True,
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    job_zone: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    onet_version: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="31.0",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    riasec_profile: Mapped[
        "CareerRiasecProfile | None"
    ] = relationship(
        back_populates="career",
        cascade="all, delete-orphan",
        uselist=False,
    )


class CareerRiasecProfile(Base):
    __tablename__ = "career_riasec_profiles"

    __table_args__ = (
        UniqueConstraint(
            "career_id",
            name="uq_career_riasec_profile_career_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    career_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "careers.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    realistic: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    investigative: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    artistic: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    social: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    enterprising: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    conventional: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="O*NET",
    )

    onet_version: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="31.0",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    career: Mapped["Career"] = relationship(
        back_populates="riasec_profile"
    )