"""Add target_plugins to agent_remote_targets

Revision ID: 20260814094746
Revises: f1a2b3c4d5e6
Create Date: 2026-08-14T09:47:46.821681
"""

from alembic import op
import sqlalchemy as sa

revision = "20260814094746"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "agent_remote_targets",
        sa.Column("target_plugins", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("agent_remote_targets", "target_plugins")
