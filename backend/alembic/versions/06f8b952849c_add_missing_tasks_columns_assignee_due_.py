"""add missing tasks columns: assignee, due_date, started_at, completed_at

Revision ID: 06f8b952849c
Revises: 7d81f75aecf6
Create Date: 2026-08-22 22:00:09.517474

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = '06f8b952849c'
down_revision: Union[str, Sequence[str], None] = '7d81f75aecf6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass