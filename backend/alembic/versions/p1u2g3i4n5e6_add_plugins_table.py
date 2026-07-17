"""add plugins table

Revision ID: p1u2g3i4n5e6
Revises: n1a2b3c4d5e6
Create Date: 2026-07-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'p1u2g3i4n5e6'
down_revision: Union[str, Sequence[str], None] = 'n1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'plugins',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('slug', sa.String(100), nullable=False, unique=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('description', sa.String(2000), nullable=True),
        sa.Column('author', sa.String(200), nullable=True),
        sa.Column('execution_target', sa.String(20), nullable=False),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('status', sa.String(30), nullable=False, server_default='registered'),
        sa.Column('config_json', sa.Text(), nullable=True),
        sa.Column('capabilities_json', sa.Text(), nullable=True),
        sa.Column('min_core_version', sa.String(50), nullable=True),
        sa.Column('permissions_json', sa.Text(), nullable=True),
        sa.Column('dependencies_json', sa.Text(), nullable=True),
        sa.Column('last_heartbeat', sa.DateTime(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    op.create_index('ix_plugins_slug', 'plugins', ['slug'], unique=True)
    op.create_index('ix_plugins_execution_target', 'plugins', ['execution_target'])
    op.create_index('ix_plugins_category', 'plugins', ['category'])
    op.create_index('ix_plugins_enabled', 'plugins', ['enabled'])
    op.create_index('ix_plugins_status', 'plugins', ['status'])


def downgrade() -> None:
    op.drop_index('ix_plugins_status', table_name='plugins')
    op.drop_index('ix_plugins_enabled', table_name='plugins')
    op.drop_index('ix_plugins_category', table_name='plugins')
    op.drop_index('ix_plugins_execution_target', table_name='plugins')
    op.drop_index('ix_plugins_slug', table_name='plugins')
    op.drop_table('plugins')
