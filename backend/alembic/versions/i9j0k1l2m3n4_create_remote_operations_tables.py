"""Create remote operations tables

Revision ID: i9j0k1l2m3n4
Revises: b2c3d4e5f6a7
Create Date: 2026-07-12
"""

import sqlalchemy as sa

from alembic import op

revision = "i9j0k1l2m3n4"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create credential_profiles table
    op.create_table(
        "credential_profiles",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("authentication_type", sa.String(20), nullable=False, server_default="password"),
        sa.Column("username", sa.String(200), nullable=False),
        sa.Column("password", sa.Text(), nullable=True),
        sa.Column("ssh_key", sa.Text(), nullable=True),
        sa.Column("description", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Create remote_hosts table
    op.create_table(
        "remote_hosts",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("hostname", sa.String(500), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("operating_system", sa.String(100), nullable=True),
        sa.Column("connection_type", sa.String(20), nullable=False, server_default="ssh"),
        sa.Column("port", sa.Integer(), nullable=False, server_default="22"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "credential_profile_id",
            sa.Integer(),
            sa.ForeignKey("credential_profiles.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Create command_history table
    op.create_table(
        "command_history",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "host_id",
            sa.Integer(),
            sa.ForeignKey("remote_hosts.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("command", sa.Text(), nullable=False),
        sa.Column("shell", sa.String(20), nullable=False, server_default="bash"),
        sa.Column("stdout", sa.Text(), nullable=True),
        sa.Column("stderr", sa.Text(), nullable=True),
        sa.Column("exit_code", sa.Integer(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("executed_by", sa.String(200), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("command_history")
    op.drop_table("remote_hosts")
    op.drop_table("credential_profiles")
