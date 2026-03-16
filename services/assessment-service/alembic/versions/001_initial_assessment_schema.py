"""initial assessment schema

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
    # ── assessments ──────────────────────────────────────────────────────────
    op.create_table(
        "assessments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("topic", sa.String(100), nullable=False),
        sa.Column("difficulty", sa.String(20), nullable=False, server_default="medium"),
        sa.Column(
            "related_skills",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "is_published",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_assessments_topic", "assessments", ["topic"])
    op.create_index("ix_assessments_difficulty", "assessments", ["difficulty"])
    op.create_index("ix_assessments_is_published", "assessments", ["is_published"])

    # ── assessment_items ─────────────────────────────────────────────────────
    op.create_table(
        "assessment_items",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "assessment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assessments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("mode", sa.String(20), nullable=False),
        sa.Column("options", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column(
            "correct_option_ids",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "expected_keywords",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "rubric_checklist",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("max_score", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column(
            "related_skills",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_assessment_items_assessment_id", "assessment_items", ["assessment_id"])
    op.create_index("ix_assessment_items_mode", "assessment_items", ["mode"])

    # ── assessment_attempts ───────────────────────────────────────────────────
    op.create_table(
        "assessment_attempts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "assessment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assessments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="completed"),
        sa.Column("earned_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("max_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("percentage", sa.Float(), nullable=False, server_default="0"),
        sa.Column("weak_skills", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_assessment_attempts_user_id", "assessment_attempts", ["user_id"])
    op.create_index(
        "ix_assessment_attempts_assessment_id",
        "assessment_attempts",
        ["assessment_id"],
    )
    op.create_index(
        "ix_assessment_attempts_user_assessment",
        "assessment_attempts",
        ["user_id", "assessment_id"],
    )

    # ── assessment_answers ────────────────────────────────────────────────────
    op.create_table(
        "assessment_answers",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "attempt_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assessment_attempts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assessment_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("mode", sa.String(20), nullable=False),
        sa.Column(
            "selected_option_ids",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("text_answer", sa.Text(), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.Column("earned_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("auto_feedback", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("attempt_id", "item_id", name="uq_answer_attempt_item"),
    )
    op.create_index("ix_assessment_answers_attempt_id", "assessment_answers", ["attempt_id"])

    # ── assessment_feedback ───────────────────────────────────────────────────
    op.create_table(
        "assessment_feedback",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "attempt_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assessment_attempts.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("rubric_notes", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column(
            "recommended_materials",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("weak_skills", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_assessment_feedback_attempt_id", "assessment_feedback", ["attempt_id"]
    )


def downgrade() -> None:
    op.drop_table("assessment_feedback")
    op.drop_table("assessment_answers")
    op.drop_table("assessment_attempts")
    op.drop_table("assessment_items")
    op.drop_table("assessments")
