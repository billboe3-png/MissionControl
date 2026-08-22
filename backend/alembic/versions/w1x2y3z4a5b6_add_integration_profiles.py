"""add integration profiles

Revision ID: w1x2y3z4a5b6
Revises: u4v5w6x7y8z9
Create Date: 2026-07-14
"""

import sqlalchemy as sa

from alembic import op

revision = "w1x2y3z4a5b6"
down_revision = "u4v5w6x7y8z9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "integration_profiles",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("integration_type", sa.String(50), nullable=False, index=True),
        sa.Column("description", sa.String(1000), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("base_url", sa.String(500), nullable=True),
        sa.Column("username", sa.String(500), nullable=True),
        sa.Column("encrypted_secret", sa.Text(), nullable=True),
        sa.Column("tenant_id", sa.String(500), nullable=True),
        sa.Column("client_id", sa.String(500), nullable=True),
        sa.Column("client_secret_encrypted", sa.Text(), nullable=True),
        sa.Column("authority_url", sa.String(500), nullable=True),
        sa.Column("domain", sa.String(500), nullable=True),
        sa.Column("base_dn", sa.String(500), nullable=True),
        sa.Column("use_ssl", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("verify_ssl", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("timeout", sa.Integer(), nullable=False, server_default=sa.text("30")),
        sa.Column("poll_interval", sa.Integer(), nullable=False, server_default=sa.text("60")),
        sa.Column("last_test", sa.DateTime(), nullable=True),
        sa.Column("last_success", sa.DateTime(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("integration_profiles")
