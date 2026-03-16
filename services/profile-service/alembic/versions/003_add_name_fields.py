"""add first_name, last_name, patronymic to profiles

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
    op.add_column("profiles", sa.Column("first_name", sa.String(100), nullable=True))
    op.add_column("profiles", sa.Column("last_name", sa.String(100), nullable=True))
    op.add_column("profiles", sa.Column("patronymic", sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column("profiles", "patronymic")
    op.drop_column("profiles", "last_name")
    op.drop_column("profiles", "first_name")
