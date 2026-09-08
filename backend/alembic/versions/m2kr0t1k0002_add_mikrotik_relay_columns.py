"""add_mikrotik_relay_columns

Revision ID: m2kr0t1k0002
Revises: m1kr0t1k0001
Create Date: 2026-08-24

Adds agent-relay support to mikrotik_servers: an optional relay agent
and the auto-provisioned AgentRemoteTarget used to reach the device
through the agent's SSH connector.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "m2kr0t1k0002"
down_revision: str | None = "m1kr0t1k0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "mikrotik_servers",
        sa.Column("relay_agent_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "mikrotik_servers",
        sa.Column("remote_target_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_mikrotik_servers_relay_agent",
        "mikrotik_servers",
        "agents",
        ["relay_agent_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_mikrotik_servers_relay_agent", "mikrotik_servers", type_="foreignkey"
    )
    op.drop_column("mikrotik_servers", "remote_target_id")
    op.drop_column("mikrotik_servers", "relay_agent_id")
