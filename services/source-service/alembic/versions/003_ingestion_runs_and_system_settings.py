"""ingestion_runs history, system_settings (schedule) и fix hh.ru default_query.

Revision ID: 003
Revises: 002
Create Date: 2026-05-11
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── ingestion_runs ────────────────────────────────────────────────────
    op.create_table(
        "ingestion_runs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_name", sa.String(200), nullable=True),
        sa.Column("source_type", sa.String(50), nullable=True),
        sa.Column("task_id", sa.String(80), nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="running",
        ),
        sa.Column("new_vacancies", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_vacancies", sa.Integer(), nullable=True),
        sa.Column("reason", sa.String(200), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_ingestion_runs_source_id", "ingestion_runs", ["source_id"])
    op.create_index("ix_ingestion_runs_task_id", "ingestion_runs", ["task_id"])
    op.create_index("ix_ingestion_runs_started_at", "ingestion_runs", ["started_at"])
    op.create_index("ix_ingestion_runs_status", "ingestion_runs", ["status"])

    # ── system_settings ───────────────────────────────────────────────────
    op.create_table(
        "system_settings",
        sa.Column("key", sa.String(100), primary_key=True),
        sa.Column(
            "value",
            postgresql.JSONB(),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # Расписание ingestion по умолчанию (часы между запусками fetch_all_sources
    # и минуты между нормализацией). Админ сможет менять через UI.
    op.execute(
        """
        INSERT INTO system_settings (key, value)
        VALUES ('ingestion_schedule',
                '{"fetch_interval_hours": 2, "normalize_interval_minutes": 30}')
        ON CONFLICT (key) DO NOTHING
        """
    )

    # ── Fix hh.ru default_query (исходный запрос ломал API 400) ───────────
    op.execute(
        """
        UPDATE vacancy_sources
        SET config = jsonb_set(
            jsonb_set(
                COALESCE(config, '{}'::jsonb),
                '{default_queries}',
                '["python developer","backend developer","data engineer","ml engineer","frontend developer"]'::jsonb,
                true
            ),
            '{per_page}',
            '50'::jsonb,
            true
        ) - 'default_query'
        WHERE name ILIKE '%hh.ru%'
        """
    )


def downgrade() -> None:
    op.drop_table("system_settings")
    op.drop_index("ix_ingestion_runs_status", table_name="ingestion_runs")
    op.drop_index("ix_ingestion_runs_started_at", table_name="ingestion_runs")
    op.drop_index("ix_ingestion_runs_task_id", table_name="ingestion_runs")
    op.drop_index("ix_ingestion_runs_source_id", table_name="ingestion_runs")
    op.drop_table("ingestion_runs")
