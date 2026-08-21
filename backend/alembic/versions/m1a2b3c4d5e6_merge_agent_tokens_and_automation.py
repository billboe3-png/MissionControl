"""merge agent tokens and automation

Revision ID: m1a2b3c4d5e6
Revises: a5b6c7d8e9f0, x3y4z5a6b7c8
Create Date: 2026-07-16 12:00:00.000000

"""
from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = 'm1a2b3c4d5e6'
down_revision: str | Sequence[str] | None = ('a5b6c7d8e9f0', 'x3y4z5a6b7c8')
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
