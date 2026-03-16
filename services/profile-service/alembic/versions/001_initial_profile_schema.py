"""initial profile schema

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
        "profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("headline", sa.String(200), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("ix_profiles_user_id", "profiles", ["user_id"])

    op.create_table(
        "profile_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("preferred_locations", postgresql.ARRAY(sa.String(100)),
                  nullable=False, server_default="{}"),
        sa.Column("work_formats", postgresql.ARRAY(sa.String(50)),
                  nullable=False, server_default="{}"),
        sa.Column("target_roles", postgresql.ARRAY(sa.String(100)),
                  nullable=False, server_default="{}"),
        sa.Column("salary_from", sa.Integer(), nullable=True),
        sa.Column("salary_to", sa.Integer(), nullable=True),
        sa.Column("seniority", sa.String(50), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("now()")),
    )

    op.create_table(
        "skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("normalized_name", sa.String(100), nullable=False, unique=True),
        sa.Column("category", sa.String(100), nullable=True),
    )
    op.create_index("ix_skills_normalized_name", "skills", ["normalized_name"])

    op.create_table(
        "profile_skills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("skills.id", ondelete="CASCADE"), nullable=False),
        sa.Column("self_assessed_level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("confirmed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("years_of_experience", sa.Integer(), nullable=True),
        sa.UniqueConstraint("profile_id", "skill_id", name="uq_profile_skills"),
    )

    op.create_table(
        "work_experiences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company", sa.String(200), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("now()")),
    )

    op.create_table(
        "educations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("institution", sa.String(200), nullable=False),
        sa.Column("degree", sa.String(100), nullable=True),
        sa.Column("field", sa.String(100), nullable=True),
        sa.Column("start_year", sa.Integer(), nullable=True),
        sa.Column("end_year", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("educations")
    op.drop_table("work_experiences")
    op.drop_table("profile_skills")
    op.drop_index("ix_skills_normalized_name", table_name="skills")
    op.drop_table("skills")
    op.drop_table("profile_preferences")
    op.drop_index("ix_profiles_user_id", table_name="profiles")
    op.drop_table("profiles")
