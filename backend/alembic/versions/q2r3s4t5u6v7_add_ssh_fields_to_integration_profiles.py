"""add ssh fields to integration profiles

Revision ID: q2r3s4t5u6v7
Revises: p1u2g3i4n5e6
Create Date: 2026-07-21

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = 'q2r3s4t5u6v7'
down_revision: str | Sequence[str] | None = 'p1u2g3i4n5e6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('integration_profiles', sa.Column('ssh_host', sa.String(500), nullable=True))
    op.add_column('integration_profiles', sa.Column('ssh_port', sa.Integer(), nullable=True, server_default='22'))
    op.add_column('integration_profiles', sa.Column('ssh_username', sa.String(500), nullable=True))
    op.add_column('integration_profiles', sa.Column('ssh_password_encrypted', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('integration_profiles', 'ssh_password_encrypted')
    op.drop_column('integration_profiles', 'ssh_username')
    op.drop_column('integration_profiles', 'ssh_port')
    op.drop_column('integration_profiles', 'ssh_host')
