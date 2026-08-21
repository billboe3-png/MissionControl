"""Add project_id to notes

Revision ID: g8a4c2f1b9e3
Revises: f13b69579d37
Create Date: 2026-07-12 18:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "g8a4c2f1b9e3"
down_revision: str | Sequence[str] | None = "f13b69579d37"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("notes", sa.Column("project_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_notes_project_id"), "notes", ["project_id"], unique=False)
    op.create_foreign_key(
        "fk_notes_project_id_projects",
        "notes",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_notes_project_id_projects", "notes", type_="foreignkey")
    op.drop_index(op.f("ix_notes_project_id"), table_name="notes")
    op.drop_column("notes", "project_id")
