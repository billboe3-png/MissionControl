"""add company parent_id for sub-tenant hierarchy

Revision ID: z9a1b2c3d4e5
Revises: y2z3a4b5c6d7
Create Date: 2026-07-27
"""

from alembic import op
import sqlalchemy as sa

revision = "z9a1b2c3d4e5"
down_revision = "merge_heads_rc1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "companies",
        sa.Column("parent_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_companies_parent_id",
        "companies",
        "companies",
        ["parent_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_companies_parent_id",
        "companies",
        ["parent_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_companies_parent_id", "companies")
    op.drop_constraint("fk_companies_parent_id", "companies", type_="foreignkey")
    op.drop_column("companies", "parent_id")
