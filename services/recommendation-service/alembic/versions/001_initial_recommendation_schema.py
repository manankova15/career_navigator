"""initial recommendation schema

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
        "recommendation_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("algorithm", sa.String(50), nullable=False, server_default="content_v1"),
        sa.Column("total_scored", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_rec_sessions_user_id", "recommendation_sessions", ["user_id"])

    op.create_table(
        "vacancy_recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("session_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("recommendation_sessions.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vacancy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("skill_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("location_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("salary_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("seniority_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("matched_skills", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("missing_skills", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("reasons", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("feedback", sa.String(20), nullable=True),
        sa.Column("feedback_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("now()")),
        sa.UniqueConstraint("session_id", "vacancy_id", name="uq_rec_session_vacancy"),
    )
    op.create_index("ix_vacancy_rec_user_id", "vacancy_recommendations", ["user_id"])
    op.create_index("ix_vacancy_rec_score", "vacancy_recommendations", ["score"])
    op.create_index("ix_vacancy_rec_feedback", "vacancy_recommendations", ["feedback"])

    op.create_table(
        "skill_gap_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("session_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("recommendation_sessions.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_name", sa.String(100), nullable=False),
        sa.Column("importance_score", sa.Float(), nullable=False),
        sa.Column("frequency", sa.Integer(), nullable=False),
        sa.Column("recommended_resources", postgresql.JSONB(),
                  nullable=False, server_default="[]"),
        sa.Column("rank", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_skill_gap_user_id", "skill_gap_records", ["user_id"])


def downgrade() -> None:
    op.drop_table("skill_gap_records")
    op.drop_table("vacancy_recommendations")
    op.drop_table("recommendation_sessions")
