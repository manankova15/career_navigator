"""add explanation column to assessment_items

Revision ID: 002
Revises: 001
Create Date: 2026-03-13
"""

from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use IF NOT EXISTS so re-running is safe if the column was added manually
    op.execute("ALTER TABLE assessment_items ADD COLUMN IF NOT EXISTS explanation TEXT")


def downgrade() -> None:
    op.drop_column("assessment_items", "explanation")
