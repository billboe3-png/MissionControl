"""create users table

Revision ID: f4a5b6c7d8e9
Revises: e3f4a5b6c7d8
Create Date: 2026-07-16
"""

import sqlalchemy as sa

from alembic import op

revision = "f4a5b6c7d8e9"
down_revision = "e3f4a5b6c7d8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "company_id",
            sa.Integer(),
            sa.ForeignKey("companies.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "site_id",
            sa.Integer(),
            sa.ForeignKey("sites.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("email", sa.String(500), nullable=False, unique=True),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column(
            "role",
            sa.String(30),
            nullable=False,
            server_default="readonly",
        ),
        sa.Column(
            "enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("last_login", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_company_id", "users", ["company_id"])
    op.create_index("ix_users_site_id", "users", ["site_id"])
    op.create_index("ix_users_role", "users", ["role"])


def downgrade() -> None:
    op.drop_index("ix_users_role", "users")
    op.drop_index("ix_users_site_id", "users")
    op.drop_index("ix_users_company_id", "users")
    op.drop_index("ix_users_email", "users")
    op.drop_table("users")
