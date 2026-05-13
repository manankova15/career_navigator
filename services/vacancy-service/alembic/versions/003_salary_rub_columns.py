"""salary RUB equivalents: salary_from_rub / salary_to_rub for cross-currency sort/filter.

Revision ID: 003
Revises: 002
Create Date: 2026-05-10
"""

from alembic import op
import sqlalchemy as sa


revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "canonical_vacancies",
        sa.Column("salary_from_rub", sa.Integer(), nullable=True),
    )
    op.add_column(
        "canonical_vacancies",
        sa.Column("salary_to_rub", sa.Integer(), nullable=True),
    )

    # Индекс по верхней границе вилки в рублях — основной ключ сортировки
    # «по зарплате».
    op.create_index(
        "ix_canonical_vacancies_salary_to_rub",
        "canonical_vacancies",
        ["salary_to_rub"],
    )
    op.create_index(
        "ix_canonical_vacancies_salary_from_rub",
        "canonical_vacancies",
        ["salary_from_rub"],
    )

    # Заполняем RUB-эквиваленты у уже существующих RUB-вакансий: для них
    # курс = 1, поэтому копируем значения как есть. Для других валют
    # необходимо запустить scripts/backfill_classification.py --recompute-salary.
    op.execute(
        """
        UPDATE canonical_vacancies
        SET salary_from_rub = salary_from,
            salary_to_rub = salary_to
        WHERE (salary_currency IS NULL OR salary_currency IN ('RUB', 'RUR'))
          AND (salary_from IS NOT NULL OR salary_to IS NOT NULL)
        """
    )


def downgrade() -> None:
    op.drop_index(
        "ix_canonical_vacancies_salary_from_rub",
        table_name="canonical_vacancies",
    )
    op.drop_index(
        "ix_canonical_vacancies_salary_to_rub",
        table_name="canonical_vacancies",
    )
    op.drop_column("canonical_vacancies", "salary_to_rub")
    op.drop_column("canonical_vacancies", "salary_from_rub")
