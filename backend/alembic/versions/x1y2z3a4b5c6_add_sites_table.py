"""add sites table and site_id foreign keys

Revision ID: x1y2z3a4b5c6
Revises: w1x2y3z4a5b6
Create Date: 2026-07-14
"""

from alembic import op
import sqlalchemy as sa

revision = "x1y2z3a4b5c6"
down_revision = "w1x2y3z4a5b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sites",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("code", sa.String(100), nullable=False, unique=True, index=True),
        sa.Column("description", sa.String(1000), nullable=True),
        sa.Column("color", sa.String(7), nullable=True),
        sa.Column("icon", sa.String(50), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("city", sa.String(200), nullable=True),
        sa.Column("state", sa.String(200), nullable=True),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("timezone", sa.String(100), nullable=True),
        sa.Column("contact_name", sa.String(200), nullable=True),
        sa.Column("contact_email", sa.String(500), nullable=True),
        sa.Column("contact_phone", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.add_column(
        "integration_profiles",
        sa.Column("site_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_integration_profiles_site_id",
        "integration_profiles",
        "sites",
        ["site_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_integration_profiles_site_id",
        "integration_profiles",
        ["site_id"],
    )

    op.add_column(
        "remote_hosts",
        sa.Column("site_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_remote_hosts_site_id",
        "remote_hosts",
        "sites",
        ["site_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_remote_hosts_site_id",
        "remote_hosts",
        ["site_id"],
    )

    op.add_column(
        "credential_profiles",
        sa.Column("site_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_credential_profiles_site_id",
        "credential_profiles",
        "sites",
        ["site_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_credential_profiles_site_id",
        "credential_profiles",
        ["site_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_credential_profiles_site_id", "credential_profiles")
    op.drop_constraint("fk_credential_profiles_site_id", "credential_profiles", type_="foreignkey")
    op.drop_column("credential_profiles", "site_id")

    op.drop_index("ix_remote_hosts_site_id", "remote_hosts")
    op.drop_constraint("fk_remote_hosts_site_id", "remote_hosts", type_="foreignkey")
    op.drop_column("remote_hosts", "site_id")

    op.drop_index("ix_integration_profiles_site_id", "integration_profiles")
    op.drop_constraint("fk_integration_profiles_site_id", "integration_profiles", type_="foreignkey")
    op.drop_column("integration_profiles", "site_id")

    op.drop_table("sites")
