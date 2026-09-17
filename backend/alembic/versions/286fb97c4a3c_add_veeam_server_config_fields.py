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
    # Use a PL/pgSQL DO block so each column addition is independent —
    # if one column already exists the block continues to the next.
    # This survives being wrapped in a single alembic transaction.
    op.execute("""
        DO $$
        DECLARE
            col_exists boolean;
        BEGIN
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name   = 'veeam_backup_servers'
                  AND column_name  = 'ssh_host'
            ) INTO col_exists;
            IF NOT col_exists THEN
                ALTER TABLE veeam_backup_servers ADD COLUMN ssh_host VARCHAR(200);
            END IF;

            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name   = 'veeam_backup_servers'
                  AND column_name  = 'ssh_port'
            ) INTO col_exists;
            IF NOT col_exists THEN
                ALTER TABLE veeam_backup_servers ADD COLUMN ssh_port INTEGER NOT NULL DEFAULT 22;
            END IF;

            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name   = 'veeam_backup_servers'
                  AND column_name  = 'ssh_username'
            ) INTO col_exists;
            IF NOT col_exists THEN
                ALTER TABLE veeam_backup_servers ADD COLUMN ssh_username VARCHAR(200);
            END IF;

            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name   = 'veeam_backup_servers'
                  AND column_name  = 'encrypted_ssh_password'
            ) INTO col_exists;
            IF NOT col_exists THEN
                ALTER TABLE veeam_backup_servers ADD COLUMN encrypted_ssh_password TEXT;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.drop_column('veeam_backup_servers', 'encrypted_ssh_password')
    op.drop_column('veeam_backup_servers', 'ssh_username')
    op.drop_column('veeam_backup_servers', 'ssh_port')
    op.drop_column('veeam_backup_servers', 'ssh_host')
