import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base


class JDAnalysis(Base):
    __tablename__ = "jd_analyses"
    __table_args__ = (
        CheckConstraint("char_length(source_text) BETWEEN 1 AND 30000", name="ck_jd_source_length"),
        CheckConstraint("requirement_count BETWEEN 0 AND 100", name="ck_jd_requirement_count"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    company: Mapped[str | None] = mapped_column(String(200))
    source_url: Mapped[str | None] = mapped_column(String(2048))
    source_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    extractor_version: Mapped[str] = mapped_column(String(40))
    requirement_count: Mapped[int] = mapped_column(Integer)
    truncated: Mapped[bool] = mapped_column(Boolean, default=False)
    requirements: Mapped[list["Requirement"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", order_by="Requirement.position",
    )


class Requirement(Base):
    __tablename__ = "jd_requirements"
    __table_args__ = (
        UniqueConstraint("analysis_id", "position", name="uq_jd_requirement_position"),
        CheckConstraint("position BETWEEN 0 AND 99", name="ck_jd_requirement_position"),
        CheckConstraint("source_start >= 0 AND source_end > source_start AND source_end <= 30000", name="ck_jd_requirement_span"),
        CheckConstraint("char_length(quote) = source_end - source_start", name="ck_jd_requirement_quote"),
        CheckConstraint("\"group\" IN ('technology', 'experience', 'education', 'responsibility', 'preferred')", name="ck_jd_requirement_group"),
        CheckConstraint("evidence_type = 'FACT_FROM_JD'", name="ck_jd_requirement_evidence"),
        CheckConstraint("(normalized_name IS NULL AND interpretation_type IS NULL) OR (normalized_name IS NOT NULL AND interpretation_type IS NOT NULL AND interpretation_type = 'NORMALIZED_INTERPRETATION')", name="ck_jd_requirement_interpretation"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jd_analyses.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    group: Mapped[str] = mapped_column(String(30))
    quote: Mapped[str] = mapped_column(Text)
    source_start: Mapped[int] = mapped_column(Integer)
    source_end: Mapped[int] = mapped_column(Integer)
    evidence_type: Mapped[str] = mapped_column(String(30), default="FACT_FROM_JD")
    normalized_name: Mapped[str | None] = mapped_column(String(200))
    interpretation_type: Mapped[str | None] = mapped_column(String(40))
    analysis: Mapped[JDAnalysis] = relationship(back_populates="requirements")
