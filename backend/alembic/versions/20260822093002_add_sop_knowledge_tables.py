"""Add SOP knowledge tables and plugin target columns

Revision ID: 20260822093002
Revises: 20260814094746
Create Date: 2026-08-22T09:30:02
"""

from alembic import op
import sqlalchemy as sa


revision = "20260822093002"
down_revision = "20260814094746"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "agents",
        sa.Column("enabled_plugins", sa.Text(), nullable=True),
    )
    op.add_column(
        "agent_remote_targets",
        sa.Column("target_plugins", sa.Text(), nullable=True),
    )

    op.create_table(
        "sops",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("company_id", sa.Integer(), nullable=True, index=True),
        sa.Column("site_id", sa.Integer(), nullable=True, index=True),
        sa.Column("category_id", sa.Integer(), nullable=True, index=True),
        sa.Column("owner_id", sa.Integer(), nullable=True, index=True),
        sa.Column("title", sa.String(length=255), nullable=False, index=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="draft", index=True),
        sa.Column("current_version", sa.String(length=50), nullable=True),
        sa.Column("tags", sa.Text(), nullable=True),
        sa.Column("purpose", sa.Text(), nullable=True),
        sa.Column("scope", sa.Text(), nullable=True),
        sa.Column("audience", sa.Text(), nullable=True),
        sa.Column("responsibilities", sa.Text(), nullable=True),
        sa.Column("prerequisites", sa.Text(), nullable=True),
        sa.Column("procedure", sa.Text(), nullable=True),
        sa.Column("validation", sa.Text(), nullable=True),
        sa.Column("troubleshooting", sa.Text(), nullable=True),
        sa.Column("escalation", sa.Text(), nullable=True),
        sa.Column("rollback", sa.Text(), nullable=True),
        sa.Column("safety_requirements", sa.Text(), nullable=True),
        sa.Column('"references"', sa.Text(), nullable=True),
        sa.Column("related_sops", sa.Text(), nullable=True),
        sa.Column("review_date", sa.DateTime(), nullable=True),
        sa.Column("approval_date", sa.DateTime(), nullable=True),
        sa.Column("approved_by_id", sa.Integer(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "sop_versions",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("sop_id", sa.Integer(), sa.ForeignKey("sops.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="draft"),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tags", sa.Text(), nullable=True),
        sa.Column("purpose", sa.Text(), nullable=True),
        sa.Column("procedure", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("change_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "sop_sources",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("sop_id", sa.Integer(), sa.ForeignKey("sops.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("source_name", sa.String(length=512), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("source_hash", sa.String(length=255), nullable=True, index=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("importing_user", sa.String(length=255), nullable=True),
        sa.Column("processing_error", sa.Text(), nullable=True),
        sa.Column("imported_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "sop_approvals",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("sop_id", sa.Integer(), sa.ForeignKey("sops.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("sop_version_id", sa.Integer(), sa.ForeignKey("sop_versions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("approver_name", sa.String(length=255), nullable=False),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("acted_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "sop_audit_events",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("sop_id", sa.Integer(), sa.ForeignKey("sops.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("action", sa.String(length=100), nullable=False, index=True),
        sa.Column("actor", sa.String(length=255), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "sop_categories",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(length=255), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("sop_categories")
    op.drop_table("sop_audit_events")
    op.drop_table("sop_approvals")
    op.drop_table("sop_sources")
    op.drop_table("sop_versions")
    op.drop_table("sops")
    op.drop_column("agent_remote_targets", "target_plugins")
    op.drop_column("agents", "enabled_plugins")
