"""create companies table

Revision ID: c1d2e3f4a5b6
Revises: b2c3d4e5f6a7
Create Date: 2026-07-16
"""

import sqlalchemy as sa

from alembic import op

revision = "c1d2e3f4a5b6"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("uuid", sa.String(36), nullable=False, unique=True, index=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("license_type", sa.String(50), nullable=True),
        sa.Column("max_sites", sa.Integer(), nullable=False, server_default=sa.text("10")),
        sa.Column("max_agents", sa.Integer(), nullable=False, server_default=sa.text("100")),
        sa.Column("max_users", sa.Integer(), nullable=False, server_default=sa.text("50")),
        sa.Column("primary_contact", sa.String(200), nullable=True),
        sa.Column("contact_email", sa.String(500), nullable=True),
        sa.Column("contact_phone", sa.String(50), nullable=True),
        sa.Column("timezone", sa.String(100), nullable=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("theme", sa.String(50), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_global", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_index("ix_companies_status", "companies", ["status"])


def downgrade() -> None:
    op.drop_index("ix_companies_status", "companies")
    op.drop_table("companies")
