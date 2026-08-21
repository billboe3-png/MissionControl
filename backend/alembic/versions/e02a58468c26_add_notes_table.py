"""Add notes table

Revision ID: e02a58468c26
Revises: d91f47357b15
Create Date: 2026-07-08 14:25:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e02a58468c26"
down_revision: str | Sequence[str] | None = "d91f47357b15"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "notes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_notes_id"), "notes", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_notes_id"), table_name="notes")
    op.drop_table("notes")
