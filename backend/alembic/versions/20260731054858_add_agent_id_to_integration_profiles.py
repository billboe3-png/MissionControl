import sqlalchemy as sa

from alembic import op

revision = '20260731054858'
down_revision = 'merge_heads_rc1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('integration_profiles') as batch:
        batch.add_column(sa.Column('agent_id', sa.Integer(), nullable=True))
        batch.create_index('ix_integration_profiles_agent_id', ['agent_id'])


def downgrade() -> None:
    with op.batch_alter_table('integration_profiles') as batch:
        batch.drop_index('ix_integration_profiles_agent_id')
        batch.drop_column('agent_id')
