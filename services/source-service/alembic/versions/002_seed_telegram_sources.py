"""Seed Telegram vacancy sources (каналы из scripts/telegram_channels.txt).

Revision ID: 002
Revises: 001
"""

from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    rows = [
        (
            "TG @job_for_analysts",
            "telegram",
            "https://t.me/job_for_analysts",
            '{"channel_username": "job_for_analysts"}',
        ),
        (
            "TG @vacancy_cs",
            "telegram",
            "https://t.me/vacancy_cs",
            '{"channel_username": "vacancy_cs"}',
        ),
        (
            "TG @jtbl_vacancy",
            "telegram",
            "https://t.me/jtbl_vacancy",
            '{"channel_username": "jtbl_vacancy"}',
        ),
    ]
    for name, stype, base, cfg in rows:
        op.execute(
            f"""
            INSERT INTO vacancy_sources (name, source_type, base_url, schedule, ttl_hours, enabled, config)
            SELECT '{name}', '{stype}', '{base}', '0 */6 * * *', 48, true, '{cfg}'::jsonb
            WHERE NOT EXISTS (SELECT 1 FROM vacancy_sources WHERE name = '{name}');
            """
        )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM vacancy_sources
        WHERE name IN (
            'TG @job_for_analysts',
            'TG @vacancy_cs',
            'TG @jtbl_vacancy'
        );
        """
    )
