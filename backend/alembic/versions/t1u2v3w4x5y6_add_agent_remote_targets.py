"""Add agent_remote_targets table

Revision ID: t1u2v3w4x5y6
Revises: r1s2t3u4v5w6
Create Date: 2026-07-24
"""

from alembic import op
import sqlalchemy as sa


revision = "t1u2v3w4x5y6"
down_revision = "r1s2t3u4v5w6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_remote_targets",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "agent_id",
            sa.Integer(),
            sa.ForeignKey("agents.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("hostname", sa.String(500), nullable=False),
        sa.Column("protocol", sa.String(20), nullable=False, server_default="psremoting"),
        sa.Column("port", sa.Integer(), nullable=False, server_default="5985"),
        sa.Column("username", sa.String(200), nullable=False),
        sa.Column("password_encrypted", sa.Text(), nullable=True),
        sa.Column("ssh_key_encrypted", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true"), index=True),
        sa.Column("tags", sa.String(500), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("last_collected_at", sa.DateTime(), nullable=True),
        sa.Column("last_status", sa.String(20), nullable=False, server_default="unknown"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("agent_remote_targets")
