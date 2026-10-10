"""Create user-owned applications; keep optional JD references separate.

Revision ID: b8d4e0f3c7a2
Revises: a7c3d9e2b6f1
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "b8d4e0f3c7a2"
down_revision = "a7c3d9e2b6f1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company", sa.String(200), nullable=False),
        sa.Column("job_title", sa.String(200), nullable=False),
        sa.Column("location", sa.String(200), nullable=True),
        sa.Column("employment_type", sa.String(100), nullable=True),
        sa.Column("job_url", sa.String(2048), nullable=True),
        sa.Column("jd_analysis_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jd_analyses.id", ondelete="SET NULL"), nullable=True),
        sa.Column("applied_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(30), server_default="SAVED", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('SAVED','APPLIED','ASSESSMENT','INTERVIEW','OFFER','REJECTED','WITHDRAWN')", name="ck_application_status"),
    )
    for column in ("user_id", "jd_analysis_id", "status"):
        op.create_index(f"ix_applications_{column}", "applications", [column])


def downgrade():
    op.drop_table("applications")
