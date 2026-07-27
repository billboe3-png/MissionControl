"""merge heads - a1b2c3d4e5f7 and d4e5f6a7b8c0

Revision ID: merge_heads_rc1
Revises: a1b2c3d4e5f7, d4e5f6a7b8c0
Create Date: 2026-07-27

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "merge_heads_rc1"
down_revision: Union[str, None] = ("a1b2c3d4e5f7", "d4e5f6a7b8c0")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge the two heads into one."""
    pass


def downgrade() -> None:
    pass
