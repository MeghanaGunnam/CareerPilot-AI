import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
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

    skill_requirements: Mapped[
        list["CareerSkillRequirement"]
    ] = relationship(
        back_populates="career",
        cascade="all, delete-orphan",
    )

    software_requirements: Mapped[
        list["CareerSoftwareRequirement"]
    ] = relationship(
        back_populates="career",
        cascade="all, delete-orphan",
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


class CareerSkillRequirement(Base):
    __tablename__ = "career_skill_requirements"

    __table_args__ = (
        UniqueConstraint(
            "career_id",
            "skill_type",
            "element_id",
            "scale_id",
            name="uq_career_skill_requirement",
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

    # ESSENTIAL or TRANSFERABLE
    skill_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    element_id: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    element_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )

    scale_id: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    scale_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    data_value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    not_relevant: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    recommend_suppress: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    source_date: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    domain_source: Mapped[str | None] = mapped_column(
        String(100),
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

    career: Mapped["Career"] = relationship(
        back_populates="skill_requirements"
    )


class CareerSoftwareRequirement(Base):
    __tablename__ = "career_software_requirements"

    __table_args__ = (
        UniqueConstraint(
            "career_id",
            "element_id",
            "workplace_example",
            name="uq_career_software_requirement",
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

    element_id: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    element_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )

    workplace_example: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
        index=True,
    )

    hot_technology: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    in_demand: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
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

    career: Mapped["Career"] = relationship(
        back_populates="software_requirements"
    )