"""add missing resume columns: context, started_at, paused_at, resumed_at, target_page

Revision ID: 7d81f75aecf6
Revises: 20260822093002
Create Date: 2026-08-22 21:47:04.839742

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7d81f75aecf6'
down_revision: Union[str, Sequence[str], None] = '20260822093002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('resumes', sa.Column('context', sa.Text(), nullable=True))
    op.add_column('resumes', sa.Column('started_at', sa.DateTime(), nullable=True))
    op.add_column('resumes', sa.Column('paused_at', sa.DateTime(), nullable=True))
    op.add_column('resumes', sa.Column('resumed_at', sa.DateTime(), nullable=True))
    op.add_column('resumes', sa.Column('target_page', sa.String(200), nullable=True))


def downgrade() -> None:
    op.drop_column('resumes', 'target_page')
    op.drop_column('resumes', 'resumed_at')
    op.drop_column('resumes', 'paused_at')
    op.drop_column('resumes', 'started_at')
    op.drop_column('resumes', 'context')
