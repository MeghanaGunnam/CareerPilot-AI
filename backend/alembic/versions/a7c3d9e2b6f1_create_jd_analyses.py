"""Create user-owned job description analyses and source-backed requirements.

Revision ID: a7c3d9e2b6f1
Revises: f4a2b7c9d1e3
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "a7c3d9e2b6f1"
down_revision = "f4a2b7c9d1e3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "jd_analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("company", sa.String(200), nullable=True),
        sa.Column("source_url", sa.String(2048), nullable=True),
        sa.Column("source_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("extractor_version", sa.String(40), nullable=False),
        sa.Column("requirement_count", sa.Integer(), nullable=False),
        sa.Column("truncated", sa.Boolean(), nullable=False),
        sa.CheckConstraint("char_length(source_text) BETWEEN 1 AND 30000", name="ck_jd_source_length"),
        sa.CheckConstraint("requirement_count BETWEEN 0 AND 100", name="ck_jd_requirement_count"),
    )
    op.create_index("ix_jd_analyses_user_id", "jd_analyses", ["user_id"])
    op.create_table(
        "jd_requirements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jd_analyses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("group", sa.String(30), nullable=False),
        sa.Column("quote", sa.Text(), nullable=False),
        sa.Column("source_start", sa.Integer(), nullable=False),
        sa.Column("source_end", sa.Integer(), nullable=False),
        sa.Column("evidence_type", sa.String(30), nullable=False),
        sa.Column("normalized_name", sa.String(200), nullable=True),
        sa.Column("interpretation_type", sa.String(40), nullable=True),
        sa.UniqueConstraint("analysis_id", "position", name="uq_jd_requirement_position"),
        sa.CheckConstraint("position BETWEEN 0 AND 99", name="ck_jd_requirement_position"),
        sa.CheckConstraint("source_start >= 0 AND source_end > source_start AND source_end <= 30000", name="ck_jd_requirement_span"),
        sa.CheckConstraint("char_length(quote) = source_end - source_start", name="ck_jd_requirement_quote"),
        sa.CheckConstraint("\"group\" IN ('technology', 'experience', 'education', 'responsibility', 'preferred')", name="ck_jd_requirement_group"),
        sa.CheckConstraint("evidence_type = 'FACT_FROM_JD'", name="ck_jd_requirement_evidence"),
        sa.CheckConstraint("(normalized_name IS NULL AND interpretation_type IS NULL) OR (normalized_name IS NOT NULL AND interpretation_type IS NOT NULL AND interpretation_type = 'NORMALIZED_INTERPRETATION')", name="ck_jd_requirement_interpretation"),
    )
    op.create_index("ix_jd_requirements_analysis_id", "jd_requirements", ["analysis_id"])


def downgrade() -> None:
    op.drop_table("jd_requirements")
    op.drop_table("jd_analyses")
