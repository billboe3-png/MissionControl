"""Add SOP knowledge tables

Revision ID: 20260822093002
Revises: 20260822093001
Create Date: 2026-08-22T09:30:02
"""

from alembic import op
import sqlalchemy as sa

revision = "20260822093002"
down_revision = "20260822093001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sop_categories",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("parent_id", sa.Integer(), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "sops",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("company_id", sa.Integer(), nullable=True, index=True),
        sa.Column("site_id", sa.Integer(), nullable=True, index=True),
        sa.Column("title", sa.String(500), nullable=False, index=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=True, index=True),
        sa.Column("owner_id", sa.Integer(), nullable=True, index=True),
        sa.Column("approved_by_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft", index=True),
        sa.Column("current_version", sa.String(50), nullable=True),
        sa.Column("review_date", sa.DateTime(), nullable=True, index=True),
        sa.Column("approval_date", sa.DateTime(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("tags", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("purpose", sa.Text(), nullable=True),
        sa.Column("scope", sa.Text(), nullable=True),
        sa.Column("audience", sa.Text(), nullable=True),
        sa.Column("responsibilities", sa.Text(), nullable=True),
        sa.Column("prerequisites", sa.Text(), nullable=True),
        sa.Column("required_permissions", sa.Text(), nullable=True),
        sa.Column("required_tools", sa.Text(), nullable=True),
        sa.Column("procedure", sa.Text(), nullable=True),
        sa.Column("decision_points", sa.Text(), nullable=True),
        sa.Column("validation", sa.Text(), nullable=True),
        sa.Column("troubleshooting", sa.Text(), nullable=True),
        sa.Column("escalation", sa.Text(), nullable=True),
        sa.Column("rollback", sa.Text(), nullable=True),
        sa.Column("safety_requirements", sa.Text(), nullable=True),
        sa.Column("references", sa.Text(), nullable=True),
        sa.Column("related_sops", sa.Text(), nullable=True),
    )
    op.create_table(
        "sop_versions",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("sop_id", sa.Integer(), nullable=False, index=True),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft", index=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("content_type", sa.String(30), nullable=False, server_default="user_provided", index=True),
        sa.Column("purpose", sa.Text(), nullable=True),
        sa.Column("scope", sa.Text(), nullable=True),
        sa.Column("audience", sa.Text(), nullable=True),
        sa.Column("responsibilities", sa.Text(), nullable=True),
        sa.Column("prerequisites", sa.Text(), nullable=True),
        sa.Column("required_permissions", sa.Text(), nullable=True),
        sa.Column("required_tools", sa.Text(), nullable=True),
        sa.Column("procedure", sa.Text(), nullable=True),
        sa.Column("decision_points", sa.Text(), nullable=True),
        sa.Column("validation", sa.Text(), nullable=True),
        sa.Column("troubleshooting", sa.Text(), nullable=True),
        sa.Column("escalation", sa.Text(), nullable=True),
        sa.Column("rollback", sa.Text(), nullable=True),
        sa.Column("safety_requirements", sa.Text(), nullable=True),
        sa.Column("references", sa.Text(), nullable=True),
        sa.Column("related_sops", sa.Text(), nullable=True),
        sa.Column("change_reason", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), index=True),
        sa.Column("approved_by", sa.String(200), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "sop_sources",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("sop_id", sa.Integer(), nullable=True, index=True),
        sa.Column("source_name", sa.String(500), nullable=False),
        sa.Column("source_type", sa.String(20), nullable=False, index=True),
        sa.Column("source_hash", sa.String(128), nullable=True, index=True),
        sa.Column("source_size_bytes", sa.Integer(), nullable=True),
        sa.Column("source_author", sa.String(300), nullable=True),
        sa.Column("source_version", sa.String(100), nullable=True),
        sa.Column("source_pages", sa.String(200), nullable=True),
        sa.Column("source_sections", sa.Text(), nullable=True),
        sa.Column("imported_by", sa.String(200), nullable=True),
        sa.Column("imported_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("processing_error", sa.Text(), nullable=True),
    )
    op.create_table(
        "sop_audit_events",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("sop_id", sa.Integer(), nullable=True, index=True),
        sa.Column("sop_version_id", sa.Integer(), nullable=True, index=True),
        sa.Column("company_id", sa.Integer(), nullable=True, index=True),
        sa.Column("site_id", sa.Integer(), nullable=True, index=True),
        sa.Column("action", sa.String(50), nullable=False, index=True),
        sa.Column("actor", sa.String(200), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("source", sa.String(200), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False, server_default=sa.func.now(), index=True),
    )
    with op.batch_alter_table("sop_approvals", schema=None) as batch_op:
        batch_op.add_column(sa.Column("sop_version_id", sa.Integer(), nullable=True, index=True))
        batch_op.create_foreign_key("fk_sop_approvals_sop_version_id", "sop_versions", ["sop_version_id"], ["id"], ondelete="CASCADE")


def downgrade() -> None:
    with op.batch_alter_table("sop_approvals", schema=None) as batch_op:
        batch_op.drop_constraint("fk_sop_approvals_sop_version_id", type_="foreignkey")
        batch_op.drop_column("sop_version_id")
    op.drop_table("sop_audit_events")
    op.drop_table("sop_sources")
    op.drop_table("sop_versions")
    op.drop_table("sops")
    op.drop_table("sop_categories")
