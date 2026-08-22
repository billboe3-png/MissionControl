"""Add backlog fields to parking_lot

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-12
"""

import sqlalchemy as sa

from alembic import op

revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "parking_lot",
        sa.Column("owner", sa.String(200), nullable=True),
    )
    op.add_column(
        "parking_lot",
        sa.Column("category", sa.String(100), nullable=True),
    )
    op.add_column(
        "parking_lot",
        sa.Column("labels", sa.Text(), nullable=True),
    )
    op.add_column(
        "parking_lot",
        sa.Column("target_sprint", sa.String(100), nullable=True),
    )
    op.add_column(
        "parking_lot",
        sa.Column("archived", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "parking_lot",
        sa.Column("created_by", sa.String(200), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("parking_lot", "created_by")
    op.drop_column("parking_lot", "archived")
    op.drop_column("parking_lot", "target_sprint")
    op.drop_column("parking_lot", "labels")
    op.drop_column("parking_lot", "category")
    op.drop_column("parking_lot", "owner")
