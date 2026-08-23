"""add_data_source_to_integration_profiles

Revision ID: r1s2t3u4v5w6
Revises: q2r3s4t5u6v7
Create Date: 2026-07-21
"""

import sqlalchemy as sa

from alembic import op

revision = "r1s2t3u4v5w6"
down_revision = "q2r3s4t5u6v7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "integration_profiles",
        sa.Column(
            "data_source",
            sa.String(20),
            nullable=False,
            server_default="both",
        ),
    )


def downgrade() -> None:
    op.drop_column("integration_profiles", "data_source")
