"""create agent registration tokens table

Revision ID: a5b6c7d8e9f0
Revises: f4a5b6c7d8e9
Create Date: 2026-07-16
"""

from alembic import op
import sqlalchemy as sa

revision = "a5b6c7d8e9f0"
down_revision = "f4a5b6c7d8e9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_registration_tokens",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("token", sa.String(100), nullable=False, unique=True),
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
        sa.Column(
            "max_agents", sa.Integer(), nullable=False, server_default=sa.text("10")
        ),
        sa.Column(
            "used_count", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column("label", sa.String(200), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column(
            "enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "ix_agent_registration_tokens_token",
        "agent_registration_tokens",
        ["token"],
        unique=True,
    )
    op.create_index(
        "ix_agent_registration_tokens_company_id",
        "agent_registration_tokens",
        ["company_id"],
    )
    op.create_index(
        "ix_agent_registration_tokens_site_id",
        "agent_registration_tokens",
        ["site_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_agent_registration_tokens_site_id",
        "agent_registration_tokens",
    )
    op.drop_index(
        "ix_agent_registration_tokens_company_id",
        "agent_registration_tokens",
    )
    op.drop_index(
        "ix_agent_registration_tokens_token",
        "agent_registration_tokens",
    )
    op.drop_table("agent_registration_tokens")
