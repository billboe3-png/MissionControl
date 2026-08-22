"""Add agents and agent_commands tables

Revision ID: x1y2z3a4b5c6
Revises: w1x2y3z4a5b6
Create Date: 2026-07-14
"""

import sqlalchemy as sa

from alembic import op

revision = "x1y2z3a4b5c6"
down_revision = "w1x2y3z4a5b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agents",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("hostname", sa.String(500), nullable=False, index=True),
        sa.Column("api_key", sa.String(200), nullable=False, unique=True, index=True),
        sa.Column("status", sa.String(20), nullable=False, default="offline", index=True),
        sa.Column("operating_system", sa.String(100), nullable=True),
        sa.Column("os_version", sa.String(200), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("agent_version", sa.String(50), nullable=True),
        sa.Column("inventory_json", sa.Text(), nullable=True),
        sa.Column("last_heartbeat", sa.DateTime(), nullable=True),
        sa.Column("heartbeat_interval", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("tags", sa.String(500), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("health", sa.String(20), nullable=False, server_default="unknown"),
        sa.Column("cpu_percent", sa.Float(), nullable=True),
        sa.Column("memory_percent", sa.Float(), nullable=True),
        sa.Column("disk_percent", sa.Float(), nullable=True),
        sa.Column("active_plugins", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("registered_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "agent_commands",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "agent_id",
            sa.Integer(),
            sa.ForeignKey("agents.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("command_type", sa.String(50), nullable=False, index=True),
        sa.Column("command", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, default="pending", index=True),
        sa.Column("stdout", sa.Text(), nullable=True),
        sa.Column("stderr", sa.Text(), nullable=True),
        sa.Column("exit_code", sa.Integer(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("file_path", sa.String(1000), nullable=True),
        sa.Column("file_content_b64", sa.Text(), nullable=True),
        sa.Column("file_name", sa.String(500), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("timeout", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("requested_by", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("agent_commands")
    op.drop_table("agents")
