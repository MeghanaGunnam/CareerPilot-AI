"""create roadmap items

Revision ID: f4a2b7c9d1e3
Revises: c326b0c451ac
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f4a2b7c9d1e3"
down_revision: Union[str, Sequence[str], None] = "c326b0c451ac"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "roadmap_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("career_goal_id", sa.UUID(), nullable=False),
        sa.Column("item_key", sa.String(length=255), nullable=False),
        sa.Column("provenance", sa.String(length=100), nullable=False),
        sa.Column("current_evidence_state", sa.String(length=255), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("recommended_action", sa.Text(), nullable=False),
        sa.Column("evidence_building_action", sa.Text(), nullable=False),
        sa.Column("milestone", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), server_default="NOT_STARTED", nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("model_version", sa.String(length=50), nullable=False),
        sa.Column("snapshot_version", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["career_goal_id"], ["career_goals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "career_goal_id", "item_key", name="uq_roadmap_item_owner_key"),
    )
    op.create_index("ix_roadmap_items_user_id", "roadmap_items", ["user_id"])
    op.create_index("ix_roadmap_items_career_goal_id", "roadmap_items", ["career_goal_id"])


def downgrade() -> None:
    op.drop_index("ix_roadmap_items_career_goal_id", table_name="roadmap_items")
    op.drop_index("ix_roadmap_items_user_id", table_name="roadmap_items")
    op.drop_table("roadmap_items")
