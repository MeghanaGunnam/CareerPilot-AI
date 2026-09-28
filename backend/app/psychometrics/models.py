import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RiasecAssessment(Base):
    __tablename__ = "riasec_assessments"

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

    assessment_version: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="careerpilot-v1",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="IN_PROGRESS",
        index=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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

    answers: Mapped[list["RiasecAnswer"]] = relationship(
        back_populates="assessment",
        cascade="all, delete-orphan",
    )

    profile: Mapped["RiasecProfile | None"] = relationship(
        back_populates="assessment",
        cascade="all, delete-orphan",
        uselist=False,
    )


class RiasecAnswer(Base):
    __tablename__ = "riasec_answers"

    __table_args__ = (
        UniqueConstraint(
            "assessment_id",
            "question_id",
            name="uq_riasec_answer_assessment_question",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "riasec_assessments.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    question_id: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    dimension: Mapped[str] = mapped_column(
        String(1),
        nullable=False,
    )

    response_value: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    assessment: Mapped["RiasecAssessment"] = relationship(
        back_populates="answers",
    )


class RiasecProfile(Base):
    __tablename__ = "riasec_profiles"

    __table_args__ = (
        UniqueConstraint(
            "assessment_id",
            name="uq_riasec_profile_assessment",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "riasec_assessments.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
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

    realistic: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    investigative: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    artistic: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    social: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    enterprising: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    conventional: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    dominant_code: Mapped[str] = mapped_column(
        String(6),
        nullable=False,
    )

    scoring_version: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="careerpilot-v1",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    assessment: Mapped["RiasecAssessment"] = relationship(
        back_populates="profile",
    )