"""add missing veeam server fields

Revision ID: 471bafbbdcd7
Revises: m1dlink0001
Create Date: 2026-08-27 10:45:00.000000

Revision that shares a down_revision with 286fb97c4a3c (both branch from
m1dlink0001).  The merge point f1d543c4ff24 joins the two branches; both
migrations touch `veeam_backup_servers`, so when the DB is migrated for the
first time one branch may create columns that the other also tries to add.
Guard every ADD with an IF NOT EXISTS check so the migration succeeds
regardless of which branch ran first.

IMPORTANT: use op.get_bind().execute() — NOT op.execute() — because
op.execute() silently drops bind parameters in alembic 1.13.x.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '471bafbbdcd7'
down_revision = 'm1dlink0001'
branch_labels = None
depends_on = None


def _col_exists(name: str) -> bool:
    """Return True if *name* is already a column on veeam_backup_servers."""
    bind = op.get_bind()
    result = bind.execute(
        sa.text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'public' "
            "  AND table_name = 'veeam_backup_servers' "
            "  AND column_name = :n"
        ),
        {"n": name},
    )
    # result is None in sql/offline mode; guard before iterating.
    if result is None:
        return False
    return name in {row[0] for row in result}


def upgrade() -> None:
    for col_name, col_def in [
        ("ssh_host", sa.Column("ssh_host", sa.String(200), nullable=True)),
        ("ssh_port", sa.Column("ssh_port", sa.Integer(), nullable=False, server_default="22")),
        ("ssh_username", sa.Column("ssh_username", sa.String(200), nullable=True)),
        ("encrypted_ssh_password", sa.Column("encrypted_ssh_password", sa.Text(), nullable=True)),
        ("data_source", sa.Column("data_source", sa.String(20), nullable=False, server_default="both")),
        ("db_type", sa.Column("db_type", sa.String(20), nullable=False, server_default="postgresql")),
        ("column_case", sa.Column("column_case", sa.String(20), nullable=False, server_default="pascal")),
    ]:
        if not _col_exists(col_name):
            op.add_column("veeam_backup_servers", col_def)


def downgrade() -> None:
    for col_name in [
        "ssh_host", "ssh_port", "ssh_username",
        "encrypted_ssh_password", "data_source", "db_type", "column_case",
    ]:
        try:
            op.drop_column("veeam_backup_servers", col_name)
        except Exception:
            pass
