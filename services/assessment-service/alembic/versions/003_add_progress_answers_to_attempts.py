"""add progress_answers to assessment_attempts for in-progress attempts

Revision ID: 003
Revises: 002
Create Date: 2026-03-16

"""
from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE assessment_attempts ADD COLUMN IF NOT EXISTS progress_answers JSONB NOT NULL DEFAULT '[]'"
    )


def downgrade() -> None:
    op.drop_column("assessment_attempts", "progress_answers")
