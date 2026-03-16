"""initial analytics schema

Revision ID: 001
Revises:
Create Date: 2026-03-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analytics_user_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=True),
        sa.Column("resource_id", sa.String(100), nullable=True),
        sa.Column("properties", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("occurred_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_aue_user_id", "analytics_user_events", ["user_id"])
    op.create_index("ix_aue_event_type", "analytics_user_events", ["event_type"])
    op.create_index("ix_aue_occurred_at", "analytics_user_events", ["occurred_at"])

    op.create_table(
        "analytics_assessment_stats",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assessment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("topic", sa.String(100), nullable=True),
        sa.Column("attempts_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("best_percentage", sa.Float(), nullable=False, server_default="0"),
        sa.Column("last_percentage", sa.Float(), nullable=False, server_default="0"),
        sa.Column("avg_percentage", sa.Float(), nullable=False, server_default="0"),
        sa.Column("last_attempted_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("user_id", "assessment_id", name="uq_astat_user_assessment"),
    )
    op.create_index("ix_aas_user_id", "analytics_assessment_stats", ["user_id"])

    op.create_table(
        "analytics_daily_active_users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("date", sa.String(10), nullable=False, unique=True),
        sa.Column("user_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("event_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("analytics_daily_active_users")
    op.drop_table("analytics_assessment_stats")
    op.drop_table("analytics_user_events")
