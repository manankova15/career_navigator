"""resume hh import tables

Revision ID: 004
Revises: 003
Create Date: 2026-04-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "resume_files",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("original_name", sa.String(512), nullable=False),
        sa.Column("mime_type", sa.String(128), nullable=False),
        sa.Column("extension", sa.String(16), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("storage_path", sa.String(1024), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("source_type", sa.String(32), nullable=False, server_default="hh_resume"),
        sa.Column("uploaded_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_resume_files_user_uploaded", "resume_files", ["user_id", "uploaded_at"])

    op.create_table(
        "resume_parse_jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("resume_file_id", UUID(as_uuid=True), sa.ForeignKey("resume_files.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("parser_version", sa.String(32), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_resume_parse_jobs_file", "resume_parse_jobs", ["resume_file_id"])

    op.create_table(
        "resume_parse_results",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("resume_file_id", UUID(as_uuid=True), sa.ForeignKey("resume_files.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_hh_resume", sa.Boolean(), nullable=False),
        sa.Column("hh_confidence_score", sa.Float(), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("normalized_text", sa.Text(), nullable=True),
        sa.Column("parsed_json", JSONB(), nullable=True),
        sa.Column("warnings_json", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_resume_parse_results_file", "resume_parse_results", ["resume_file_id"])

    op.create_table(
        "profile_import_drafts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("resume_file_id", UUID(as_uuid=True), sa.ForeignKey("resume_files.id", ondelete="CASCADE"), nullable=False),
        sa.Column("draft_json", JSONB(), nullable=False),
        sa.Column("field_confidence_json", JSONB(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("applied_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_profile_import_drafts_user_created", "profile_import_drafts", ["user_id", "created_at"])

    op.create_table(
        "profile_import_audit_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("resume_file_id", UUID(as_uuid=True), sa.ForeignKey("resume_files.id", ondelete="SET NULL"), nullable=True),
        sa.Column("draft_id", UUID(as_uuid=True), sa.ForeignKey("profile_import_drafts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("field_name", sa.String(256), nullable=False),
        sa.Column("old_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column("source", sa.String(64), nullable=False, server_default="hh_resume_import"),
        sa.Column("changed_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("profile_import_audit_log")
    op.drop_table("profile_import_drafts")
    op.drop_table("resume_parse_results")
    op.drop_table("resume_parse_jobs")
    op.drop_table("resume_files")
