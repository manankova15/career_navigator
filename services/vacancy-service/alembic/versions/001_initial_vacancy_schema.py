"""initial vacancy schema with FTS trigger

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
    # Enable pg_trgm for future similarity deduplication
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        "raw_vacancies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_id", sa.String(300), nullable=False),
        sa.Column("canonical_url", sa.String(1000), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("processed", sa.Boolean(), nullable=False, server_default="false"),
        sa.UniqueConstraint("source_id", "external_id", name="uq_raw_vacancies_source_external"),
    )
    op.create_index("ix_raw_vacancies_processed", "raw_vacancies", ["processed"])
    op.create_index("ix_raw_vacancies_source_id", "raw_vacancies", ["source_id"])

    op.create_table(
        "canonical_vacancies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_id", sa.String(300), nullable=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("company", sa.String(300), nullable=False),
        sa.Column("canonical_url", sa.String(1000), nullable=False),
        sa.Column("location", sa.String(200), nullable=True),
        sa.Column("salary_from", sa.Integer(), nullable=True),
        sa.Column("salary_to", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(10), nullable=True, server_default="RUB"),
        sa.Column("seniority", sa.String(50), nullable=True),
        sa.Column("employment_type", sa.String(50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("skills", postgresql.ARRAY(sa.String(100)),
                  nullable=False, server_default="{}"),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("search_vector", postgresql.TSVECTOR(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("now()")),
        sa.UniqueConstraint("source_id", "external_id",
                            name="uq_canonical_source_external"),
    )
    op.create_index(
        "ix_canonical_vacancies_search_vector",
        "canonical_vacancies",
        ["search_vector"],
        postgresql_using="gin",
    )
    op.create_index("ix_canonical_vacancies_status", "canonical_vacancies", ["status"])
    op.create_index("ix_canonical_vacancies_location", "canonical_vacancies", ["location"])
    op.create_index("ix_canonical_vacancies_seniority", "canonical_vacancies", ["seniority"])
    op.create_index(
        "ix_canonical_vacancies_skills",
        "canonical_vacancies",
        ["skills"],
        postgresql_using="gin",
    )
    # Trigram index for similarity-based deduplication on title
    op.execute(
        "CREATE INDEX ix_canonical_vacancies_title_trgm "
        "ON canonical_vacancies USING gin (title gin_trgm_ops)"
    )

    # FTS trigger: rebuilds search_vector on INSERT / UPDATE
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
    op.execute("""
        CREATE TRIGGER trg_canonical_vacancies_search_vector
        BEFORE INSERT OR UPDATE ON canonical_vacancies
        FOR EACH ROW EXECUTE FUNCTION trg_canonical_vacancies_search_vector()
    """)

    op.create_table(
        "dedup_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("primary_vacancy_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("canonical_vacancies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("duplicate_vacancy_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("canonical_vacancies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("similarity_score", sa.Float(), nullable=False),
        sa.Column("detected_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("dedup_log")
    op.execute("DROP TRIGGER IF EXISTS trg_canonical_vacancies_search_vector ON canonical_vacancies")
    op.execute("DROP FUNCTION IF EXISTS trg_canonical_vacancies_search_vector()")
    op.drop_table("canonical_vacancies")
    op.drop_table("raw_vacancies")
