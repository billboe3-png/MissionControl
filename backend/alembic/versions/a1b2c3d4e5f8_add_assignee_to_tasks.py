"""add assignee and datetime columns to tasks

Revision ID: a1b2c3d4e5f8
Revises: 7d81f75aecf6
Create Date: 2026-09-17 08:40:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'a1b2c3d4e5f8'
down_revision = 'e1f2a3b4c5d7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('tasks', sa.Column('assignee', sa.String(200), nullable=True))
    op.add_column('tasks', sa.Column('due_date', sa.Date(), nullable=True))
    op.add_column('tasks', sa.Column('started_at', sa.DateTime(), nullable=True))
    op.add_column('tasks', sa.Column('completed_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('tasks', 'completed_at')
    op.drop_column('tasks', 'started_at')
    op.drop_column('tasks', 'due_date')
    op.drop_column('tasks', 'assignee')
