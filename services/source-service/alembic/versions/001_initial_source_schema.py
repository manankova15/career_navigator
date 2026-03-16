"""initial source schema

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
        "vacancy_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("base_url", sa.String(500), nullable=True),
        sa.Column("schedule", sa.String(100), nullable=False, server_default="0 */2 * * *"),
        sa.Column("ttl_hours", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("config", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_vacancy_sources_enabled", "vacancy_sources", ["enabled"])

    # Seed hh.ru as default source
    op.execute("""
        INSERT INTO vacancy_sources (id, name, source_type, base_url, schedule, ttl_hours, enabled, config)
        VALUES (
            gen_random_uuid(),
            'hh.ru',
            'api',
            'https://api.hh.ru',
            '0 */2 * * *',
            48,
            true,
            '{"area_id": 1, "per_page": 100, "default_query": "python OR fastapi OR backend"}'
        )
    """)


def downgrade() -> None:
    op.drop_index("ix_vacancy_sources_enabled", table_name="vacancy_sources")
    op.drop_table("vacancy_sources")
