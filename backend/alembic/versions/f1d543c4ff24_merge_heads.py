"""merge heads

Revision ID: f1d543c4ff24
Revises: 286fb97c4a3c, 471bafbbdcd7
Create Date: 2026-08-27 12:58:28.865609

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = 'f1d543c4ff24'
down_revision: Union[str, Sequence[str], None] = ('286fb97c4a3c', '471bafbbdcd7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass