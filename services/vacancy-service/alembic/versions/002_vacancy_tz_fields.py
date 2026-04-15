"""vacancy TZ fields: profession, work conditions, salary meta, location split, FTS skills

Revision ID: 002
Revises: 001
Create Date: 2026-04-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE canonical_vacancies "
        "ALTER COLUMN employment_type TYPE text[] "
        "USING CASE WHEN employment_type IS NULL THEN NULL "
        "ELSE ARRAY[employment_type] END"
    )

    op.alter_column("canonical_vacancies", "currency", new_column_name="salary_currency")

    op.add_column(
        "canonical_vacancies",
        sa.Column("profession_area", sa.String(40), nullable=True),
    )
    op.add_column(
        "canonical_vacancies",
        sa.Column("specialization", sa.String(80), nullable=True),
    )
    op.add_column(
        "canonical_vacancies",
        sa.Column(
            "work_format",
            postgresql.ARRAY(sa.String(30)),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
    )
    op.add_column(
        "canonical_vacancies",
        sa.Column("schedule_type", sa.String(30), nullable=True),
    )
    op.add_column(
        "canonical_vacancies",
        sa.Column("experience_level", sa.String(30), nullable=True),
    )
    op.add_column(
        "canonical_vacancies",
        sa.Column("salary_gross_type", sa.String(20), nullable=True),
    )
    op.add_column(
        "canonical_vacancies",
        sa.Column("salary_period", sa.String(20), nullable=True),
    )
    op.add_column(
        "canonical_vacancies",
        sa.Column("location_country", sa.String(120), nullable=True),
    )
    op.add_column(
        "canonical_vacancies",
        sa.Column("location_city", sa.String(120), nullable=True),
    )
    op.add_column(
        "canonical_vacancies",
        sa.Column("education_level", sa.String(30), nullable=True),
    )
    op.add_column(
        "canonical_vacancies",
        sa.Column("english_level", sa.String(20), nullable=True),
    )
    op.add_column(
        "canonical_vacancies",
        sa.Column("company_industry", sa.String(200), nullable=True),
    )
    op.add_column(
        "canonical_vacancies",
        sa.Column("source_name", sa.String(50), nullable=True),
    )

    op.create_index(
        "ix_canonical_vacancies_profession_area",
        "canonical_vacancies",
        ["profession_area"],
    )
    op.create_index(
        "ix_canonical_vacancies_location_city",
        "canonical_vacancies",
        ["location_city"],
    )
    op.create_index(
        "ix_canonical_vacancies_experience_level",
        "canonical_vacancies",
        ["experience_level"],
    )
    op.create_index(
        "ix_canonical_vacancies_published_at",
        "canonical_vacancies",
        ["published_at"],
    )

    op.execute("""
        CREATE OR REPLACE FUNCTION trg_canonical_vacancies_search_vector()
        RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('simple', coalesce(NEW.title, '')), 'A') ||
                setweight(to_tsvector('simple', coalesce(NEW.company, '')), 'B') ||
                setweight(to_tsvector('simple', coalesce(NEW.location, '')), 'C') ||
                setweight(to_tsvector('simple', coalesce(NEW.description, '')), 'D') ||
                setweight(
                    to_tsvector(
                        'simple',
                        coalesce(array_to_string(NEW.skills, ' '), '')
                    ),
                    'C'
                );
            RETURN NEW;
        END;
        $$
    """)

    op.execute(
        "UPDATE canonical_vacancies SET search_vector = NULL "
        "WHERE id IS NOT NULL"
    )
    op.execute("""
        UPDATE canonical_vacancies SET
            search_vector =
                setweight(to_tsvector('simple', coalesce(title, '')), 'A') ||
                setweight(to_tsvector('simple', coalesce(company, '')), 'B') ||
                setweight(to_tsvector('simple', coalesce(location, '')), 'C') ||
                setweight(to_tsvector('simple', coalesce(description, '')), 'D') ||
                setweight(
                    to_tsvector('simple', coalesce(array_to_string(skills, ' '), '')),
                    'C'
                )
    """)


def downgrade() -> None:
    op.execute("""
        CREATE OR REPLACE FUNCTION trg_canonical_vacancies_search_vector()
        RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('simple', coalesce(NEW.title, '')), 'A') ||
                setweight(to_tsvector('simple', coalesce(NEW.company, '')), 'B') ||
                setweight(to_tsvector('simple', coalesce(NEW.location, '')), 'C') ||
                setweight(to_tsvector('simple', coalesce(NEW.description, '')), 'D');
            RETURN NEW;
        END;
        $$
    """)
    op.drop_index("ix_canonical_vacancies_published_at", table_name="canonical_vacancies")
    op.drop_index("ix_canonical_vacancies_experience_level", table_name="canonical_vacancies")
    op.drop_index("ix_canonical_vacancies_location_city", table_name="canonical_vacancies")
    op.drop_index("ix_canonical_vacancies_profession_area", table_name="canonical_vacancies")

    op.drop_column("canonical_vacancies", "source_name")
    op.drop_column("canonical_vacancies", "company_industry")
    op.drop_column("canonical_vacancies", "english_level")
    op.drop_column("canonical_vacancies", "education_level")
    op.drop_column("canonical_vacancies", "location_city")
    op.drop_column("canonical_vacancies", "location_country")
    op.drop_column("canonical_vacancies", "salary_period")
    op.drop_column("canonical_vacancies", "salary_gross_type")
    op.drop_column("canonical_vacancies", "experience_level")
    op.drop_column("canonical_vacancies", "schedule_type")
    op.drop_column("canonical_vacancies", "work_format")
    op.drop_column("canonical_vacancies", "specialization")
    op.drop_column("canonical_vacancies", "profession_area")

    op.alter_column("canonical_vacancies", "salary_currency", new_column_name="currency")

    op.execute(
        "ALTER TABLE canonical_vacancies "
        "ALTER COLUMN employment_type TYPE varchar(50) "
        "USING CASE WHEN employment_type IS NULL OR cardinality(employment_type) = 0 "
        "THEN NULL ELSE employment_type[1] END"
    )
