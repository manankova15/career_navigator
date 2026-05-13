"""add category/specialization snapshots to signals and likes

Revision ID: 005
Revises: 004
Create Date: 2026-05-10

Адаптивная рекомендательная модель v3 (`hybrid_ahp_v3`) учитывает категорию
(`profession_area`) и специализацию вакансии в поведенческом скоре. Чтобы
аккумулировать предпочтения по этим осям, нужно сохранять снапшот категории и
специализации каждой вакансии в момент сигнала — точно так же, как уже
сохраняется снапшот навыков и заголовка.
"""

from alembic import op
import sqlalchemy as sa


revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_liked_vacancies",
        sa.Column("vacancy_category", sa.String(80), nullable=True),
    )
    op.add_column(
        "user_liked_vacancies",
        sa.Column("vacancy_specialization", sa.String(120), nullable=True),
    )

    op.add_column(
        "user_vacancy_signals",
        sa.Column("vacancy_category", sa.String(80), nullable=True),
    )
    op.add_column(
        "user_vacancy_signals",
        sa.Column("vacancy_specialization", sa.String(120), nullable=True),
    )

    # Версия алгоритма по умолчанию для всех новых сессий — hybrid_ahp_v3.
    op.alter_column(
        "recommendation_sessions",
        "algorithm",
        server_default="hybrid_ahp_v3",
        existing_type=sa.String(50),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "recommendation_sessions",
        "algorithm",
        server_default="content_ahp_v2",
        existing_type=sa.String(50),
        existing_nullable=False,
    )
    op.drop_column("user_vacancy_signals", "vacancy_specialization")
    op.drop_column("user_vacancy_signals", "vacancy_category")
    op.drop_column("user_liked_vacancies", "vacancy_specialization")
    op.drop_column("user_liked_vacancies", "vacancy_category")
