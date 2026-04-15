"""add ml_score to vacancy_recommendations

Revision ID: 002
Revises: 001
Create Date: 2026-03-25
"""

from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "vacancy_recommendations",
        sa.Column("ml_score", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("vacancy_recommendations", "ml_score")
