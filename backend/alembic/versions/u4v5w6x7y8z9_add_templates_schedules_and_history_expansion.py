"""Add templates, schedules, and history expansion

Adds command_templates and scheduled_commands tables. Expands
command_history with credential_id, username, working_directory,
and execution_source columns.

Revision ID: u4v5w6x7y8z9
Revises: o5p6q7r8s9t0
Create Date: 2026-07-14
"""

import sqlalchemy as sa

from alembic import op

revision = "u4v5w6x7y8z9"
down_revision = "o5p6q7r8s9t0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Expand command_history with audit columns
    op.add_column(
        "command_history",
        sa.Column(
            "credential_id",
            sa.Integer(),
            sa.ForeignKey("credential_profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "command_history",
        sa.Column("username", sa.String(200), nullable=True),
    )
    op.add_column(
        "command_history",
        sa.Column("working_directory", sa.String(500), nullable=True),
    )
    op.add_column(
        "command_history",
        sa.Column(
            "execution_source",
            sa.String(20),
            nullable=False,
            server_default="manual",
        ),
    )

    # Create command_templates table
    op.create_table(
        "command_templates",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "name", sa.String(200), nullable=False, unique=True,
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "protocol", sa.String(20), nullable=False, server_default="ssh",
        ),
        sa.Column("command", sa.Text(), nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Create scheduled_commands table
    op.create_table(
        "scheduled_commands",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "host_id",
            sa.Integer(),
            sa.ForeignKey("remote_hosts.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "credential_id",
            sa.Integer(),
            sa.ForeignKey("credential_profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("command", sa.Text(), nullable=False),
        sa.Column(
            "cron_expression", sa.String(100), nullable=False,
        ),
        sa.Column(
            "enabled",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
        sa.Column("last_run", sa.DateTime(), nullable=True),
        sa.Column("next_run", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("scheduled_commands")
    op.drop_table("command_templates")
    op.drop_column("command_history", "execution_source")
    op.drop_column("command_history", "working_directory")
    op.drop_column("command_history", "username")
    op.drop_column("command_history", "credential_id")
