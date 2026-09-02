"""add missing veeam server fields

Revision ID: 471bafbbdcd7
Revises: m1dlink0001
Create Date: 2026-08-27 10:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '471bafbbdcd7'
down_revision = 'm1dlink0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add columns to veeam_backup_servers table
    op.add_column('veeam_backup_servers',
        sa.Column('ssh_host', sa.String(200), nullable=True))
    op.add_column('veeam_backup_servers',
        sa.Column('ssh_port', sa.Integer(), nullable=False, server_default='22'))
    op.add_column('veeam_backup_servers',
        sa.Column('ssh_username', sa.String(200), nullable=True))
    op.add_column('veeam_backup_servers',
        sa.Column('encrypted_ssh_password', sa.Text(), nullable=True))
    op.add_column('veeam_backup_servers',
        sa.Column('data_source', sa.String(20), nullable=False, server_default='both'))
    op.add_column('veeam_backup_servers',
        sa.Column('db_type', sa.String(20), nullable=False, server_default='postgresql'))
    op.add_column('veeam_backup_servers',
        sa.Column('column_case', sa.String(20), nullable=False, server_default='pascal'))


def downgrade() -> None:
    op.drop_column('veeam_backup_servers', 'ssh_host')
    op.drop_column('veeam_backup_servers', 'ssh_port')
    op.drop_column('veeam_backup_servers', 'ssh_username')
    op.drop_column('veeam_backup_servers', 'encrypted_ssh_password')
    op.drop_column('veeam_backup_servers', 'data_source')
    op.drop_column('veeam_backup_servers', 'db_type')
    op.drop_column('veeam_backup_servers', 'column_case')