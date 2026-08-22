"""Add SOP tables

Revision ID: 20260822093001
Revises: 20260822093000
Create Date: 2026-08-22T09:30:01
"""

from alembic import op

revision = "20260822093001"
down_revision = "20260822093000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sop_documents",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("file_path", sa.String(1000), nullable=True),
        sa.Column("content_text", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("approval_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("version", sa.String(50), nullable=True),
        sa.Column("created_by", sa.String(200), nullable=True),
        sa.Column("approved_by", sa.String(200), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "sop_approvals",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("sop_document_id", sa.Integer(), sa.ForeignKey("sop_documents.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("approver_name", sa.String(200), nullable=False),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("acted_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("sop_approvals")
    op.drop_table("sop_documents")
