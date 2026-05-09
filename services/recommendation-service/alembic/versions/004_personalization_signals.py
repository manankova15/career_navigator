"""personalization signals and feature cache for live rescoring

Revision ID: 004
Revises: 003
Create Date: 2026-04-23
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "vacancy_recommendations",
        sa.Column(
            "role_score",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "vacancy_recommendations",
        sa.Column(
            "format_score",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "vacancy_recommendations",
        sa.Column(
            "base_score",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "vacancy_recommendations",
        sa.Column(
            "features",
            postgresql.JSONB(),
            nullable=False,
            server_default="{}",
        ),
    )

    op.create_table(
        "user_vacancy_signals",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vacancy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sentiment", sa.Float(), nullable=False, server_default="0"),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("source", sa.String(32), nullable=True),
        sa.Column("vacancy_title", sa.String(300), nullable=True),
        sa.Column(
            "vacancy_skills",
            postgresql.JSONB(),
            nullable=True,
            server_default="[]",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "user_id", "vacancy_id", name="uq_user_vacancy_signal"
        ),
    )
    op.create_index(
        "ix_user_vacancy_signals_user_id",
        "user_vacancy_signals",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_user_vacancy_signals_user_id",
        table_name="user_vacancy_signals",
    )
    op.drop_table("user_vacancy_signals")
    op.drop_column("vacancy_recommendations", "features")
    op.drop_column("vacancy_recommendations", "base_score")
    op.drop_column("vacancy_recommendations", "format_score")
    op.drop_column("vacancy_recommendations", "role_score")
