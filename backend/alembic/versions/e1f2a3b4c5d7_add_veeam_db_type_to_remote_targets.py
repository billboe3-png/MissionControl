"""Add veeam db_type/column_case to agent_remote_targets

Revision ID: e1f2a3b4c5d7
Revises: f1d543c4ff24
Create Date: 2026-09-08
"""

import sqlalchemy as sa

from alembic import op

revision = "e1f2a3b4c5d7"
down_revision = "f1d543c4ff24"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "agent_remote_targets",
        sa.Column("db_type", sa.String(20), nullable=False, server_default="postgresql"),
    )
    op.add_column(
        "agent_remote_targets",
        sa.Column("column_case", sa.String(20), nullable=False, server_default="pascal"),
    )
    # Backfill from linked Veeam server rows (existing targets + their
    # auto-provisioned community server rows share target_id).
    op.execute(
        """
        UPDATE agent_remote_targets AS t
        SET db_type = v.db_type,
            column_case = v.column_case
        FROM veeam_backup_servers AS v
        WHERE v.target_id = t.id
        """
    )


def downgrade() -> None:
    op.drop_column("agent_remote_targets", "column_case")
    op.drop_column("agent_remote_targets", "db_type")
