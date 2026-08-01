from alembic import op
import sqlalchemy as sa

revision = '6b29cb7f19c9'
down_revision = '20260731054858'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('agent_commands') as batch:
        batch.add_column(sa.Column('integration_profile', sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('agent_commands') as batch:
        batch.drop_column('integration_profile')
