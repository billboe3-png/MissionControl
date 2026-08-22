"""Add enabled_plugins to agents and target_plugins to agent_remote_targets

Revision ID: 20260822093000
Revises: 20260814094746
Create Date: 2026-08-22T09:30:00
"""

from alembic import op

revision = "20260822093000"
down_revision = "20260814094746"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "agents",
        op.Column("enabled_plugins", op.Text(), nullable=True),
    )
    op.add_column(
        "agent_remote_targets",
        op.Column("target_plugins", op.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("agent_remote_targets", "target_plugins")
    op.drop_column("agents", "enabled_plugins")
