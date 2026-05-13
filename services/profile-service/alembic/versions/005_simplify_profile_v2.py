"""Simplify profile schema v2: drop free-text fields, add canonical specialization.

Profile changes:
  - drop columns: bio, target_role, headline, summary
  - shrink/repurpose: location (VARCHAR 64, canonical city code)
  - shrink/repurpose: target_industry (VARCHAR 64, canonical profession_area code)
  - add: specialization (VARCHAR 64, canonical specialization code)

ProfilePreference changes:
  - drop columns: preferred_locations, target_roles

Существующие значения (свободный текст) обнуляются: новые dropdown-поля используют
канонические коды из ``vacanciesConstants.ts`` (PROFESSION_AREAS, SPECIALIZATION_OPTIONS,
CITIES). Совмещать произвольные строки и коды смысла нет — пользователю
предлагается выбрать значения заново.

Revision ID: 005
Revises: 004
Create Date: 2026-05-11
"""

from alembic import op
import sqlalchemy as sa


revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── profiles ────────────────────────────────────────────────────────────
    op.drop_column("profiles", "bio")
    op.drop_column("profiles", "headline")
    op.drop_column("profiles", "summary")
    op.drop_column("profiles", "target_role")

    # Schubert: clear existing free-text values, then shrink type to VARCHAR(64).
    op.execute("UPDATE profiles SET location = NULL")
    op.execute("UPDATE profiles SET target_industry = NULL")
    op.alter_column(
        "profiles",
        "location",
        existing_type=sa.String(length=200),
        type_=sa.String(length=64),
        existing_nullable=True,
    )
    op.alter_column(
        "profiles",
        "target_industry",
        existing_type=sa.String(length=200),
        type_=sa.String(length=64),
        existing_nullable=True,
    )
    op.add_column(
        "profiles",
        sa.Column("specialization", sa.String(length=64), nullable=True),
    )

    # ── profile_preferences ─────────────────────────────────────────────────
    op.drop_column("profile_preferences", "preferred_locations")
    op.drop_column("profile_preferences", "target_roles")


def downgrade() -> None:
    # Восстанавливаем структуру до v2 (значения свободного текста не возвращаем).
    op.add_column(
        "profile_preferences",
        sa.Column(
            "target_roles",
            sa.dialects.postgresql.ARRAY(sa.String(length=100)),
            nullable=False,
            server_default="{}",
        ),
    )
    op.add_column(
        "profile_preferences",
        sa.Column(
            "preferred_locations",
            sa.dialects.postgresql.ARRAY(sa.String(length=100)),
            nullable=False,
            server_default="{}",
        ),
    )

    op.drop_column("profiles", "specialization")
    op.alter_column(
        "profiles",
        "target_industry",
        existing_type=sa.String(length=64),
        type_=sa.String(length=200),
        existing_nullable=True,
    )
    op.alter_column(
        "profiles",
        "location",
        existing_type=sa.String(length=64),
        type_=sa.String(length=200),
        existing_nullable=True,
    )
    op.add_column("profiles", sa.Column("target_role", sa.String(length=200), nullable=True))
    op.add_column("profiles", sa.Column("summary", sa.Text(), nullable=True))
    op.add_column("profiles", sa.Column("headline", sa.String(length=200), nullable=True))
    op.add_column("profiles", sa.Column("bio", sa.Text(), nullable=True))
