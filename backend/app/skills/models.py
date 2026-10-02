import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    canonical_name: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False,
        index=True,
    )

    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )


class StudentSkill(Base):
    __tablename__ = "student_skills"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "skill_id",
            name="uq_student_skill_user_skill",
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

    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "skills.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    claimed_proficiency: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    estimated_proficiency: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    evidence_confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    freshness_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    last_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    skill: Mapped["Skill"] = relationship()


class SkillEvidence(Base):
    __tablename__ = "skill_evidence"

    __table_args__ = (
        UniqueConstraint(
            "student_skill_id",
            "source_type",
            "source_reference",
            "source_section",
            name="uq_skill_evidence_source",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    student_skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "student_skills.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    source_reference: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    source_section: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    evidence_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    evidence_status: Mapped[str] = mapped_column(
        String(30),
        default="DETECTED",
        nullable=False,
        index=True,
    )

    evidence_strength: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    student_skill: Mapped["StudentSkill"] = relationship()
class SkillCompetencyMapping(Base):
    __tablename__ = "skill_competency_mappings"

    __table_args__ = (
        UniqueConstraint(
            "skill_id",
            "onet_element_id",
            name="uq_skill_competency_mapping",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    skill_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "skills.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    onet_element_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    onet_element_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )

    mapping_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="CONTRIBUTES_TO",
    )

    mapping_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="acif-competency-map-v1",
    )

    rationale: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    skill: Mapped["Skill"] = relationship()