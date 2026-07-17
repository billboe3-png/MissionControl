"""add company_id to sites

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2026-07-16
"""

from alembic import op
import sqlalchemy as sa

revision = "d2e3f4a5b6c7"
down_revision = "c1d2e3f4a5b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sites",
        sa.Column("company_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_sites_company_id",
        "sites",
        "companies",
        ["company_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_sites_company_id",
        "sites",
        ["company_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_sites_company_id", "sites")
    op.drop_constraint("fk_sites_company_id", "sites", type_="foreignkey")
    op.drop_column("sites", "company_id")
