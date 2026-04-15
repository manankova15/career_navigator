"""user liked vacancies for recommendation signals

Revision ID: 003
Revises: 002
Create Date: 2026-04-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_liked_vacancies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vacancy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("liked_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("unliked_at", sa.DateTime(), nullable=True),
        sa.Column("vacancy_title", sa.String(300), nullable=True),
        sa.Column("vacancy_skills", postgresql.JSONB(), nullable=True, server_default="[]"),
        sa.UniqueConstraint("user_id", "vacancy_id", name="uq_user_liked_vacancy"),
    )
    op.create_index("ix_user_liked_vacancies_user_id", "user_liked_vacancies", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_user_liked_vacancies_user_id", table_name="user_liked_vacancies")
    op.drop_table("user_liked_vacancies")
