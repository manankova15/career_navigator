"""add extended profile fields

Revision ID: 002
Revises: 001
Create Date: 2026-03-12
"""

from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("profiles", sa.Column("full_name", sa.String(200), nullable=True))
    op.add_column("profiles", sa.Column("bio", sa.Text(), nullable=True))
    op.add_column("profiles", sa.Column("location", sa.String(200), nullable=True))
    op.add_column("profiles", sa.Column("target_role", sa.String(200), nullable=True))
    op.add_column("profiles", sa.Column("target_industry", sa.String(200), nullable=True))


def downgrade() -> None:
    op.drop_column("profiles", "target_industry")
    op.drop_column("profiles", "target_role")
    op.drop_column("profiles", "location")
    op.drop_column("profiles", "bio")
    op.drop_column("profiles", "full_name")
