"""add veeam server config fields

Revision ID: 286fb97c4a3c
Revises: m1dlink0001
Create Date: 2026-08-26 10:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '286fb97c4a3c'
down_revision = 'm1dlink0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add columns to veeam_backup_servers table (only missing ones)
    op.add_column('veeam_backup_servers',
        sa.Column('ssh_host', sa.String(200), nullable=True))
    op.add_column('veeam_backup_servers',
        sa.Column('ssh_port', sa.Integer(), nullable=False, server_default='22'))
    op.add_column('veeam_backup_servers',
        sa.Column('ssh_username', sa.String(200), nullable=True))
    op.add_column('veeam_backup_servers',
        sa.Column('encrypted_ssh_password', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('veeam_backup_servers', 'ssh_host')
    op.drop_column('veeam_backup_servers', 'ssh_port')
    op.drop_column('veeam_backup_servers', 'ssh_username')
    op.drop_column('veeam_backup_servers', 'encrypted_ssh_password')