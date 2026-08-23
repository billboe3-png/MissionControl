"""Add zabbix plugin tables

Revision ID: a1b2c3d4e5f7
Revises: t1u2v3w4x5y6
Create Date: 2026-07-27
"""

import sqlalchemy as sa

from alembic import op

revision = "a1b2c3d4e5f7"
down_revision = "t1u2v3w4x5y6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "zabbix_servers",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("username", sa.String(200), nullable=False),
        sa.Column("encrypted_password", sa.Text(), nullable=True),
        sa.Column("verify_ssl", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("timeout", sa.Integer(), nullable=False, server_default=sa.text("30")),
        sa.Column("retries", sa.Integer(), nullable=False, server_default=sa.text("3")),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true"), index=True),
        sa.Column("last_connected_at", sa.DateTime(), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(), nullable=True),
        sa.Column("version", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="unknown"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "zabbix_hosts",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "server_id",
            sa.Integer(),
            sa.ForeignKey("zabbix_servers.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("zabbix_hostid", sa.String(20), nullable=False, index=True),
        sa.Column("host", sa.String(200), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="enabled"),
        sa.Column("available", sa.String(20), nullable=False, server_default="unknown"),
        sa.Column("interface_ip", sa.String(50), nullable=True),
        sa.Column("groups_json", sa.Text(), nullable=True),
        sa.Column("templates_json", sa.Text(), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "ix_zabbix_hosts_server_hostid",
        "zabbix_hosts",
        ["server_id", "zabbix_hostid"],
        unique=True,
    )

    op.create_table(
        "zabbix_problems",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "server_id",
            sa.Integer(),
            sa.ForeignKey("zabbix_servers.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("zabbix_eventid", sa.String(20), nullable=False, index=True),
        sa.Column("name", sa.String(1000), nullable=False),
        sa.Column("severity", sa.String(30), nullable=False, server_default="not_classified"),
        sa.Column("acknowledged", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("host", sa.String(200), nullable=True),
        sa.Column("zabbix_hostid", sa.String(20), nullable=True),
        sa.Column("timestamp", sa.String(30), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "ix_zabbix_problems_server_eventid",
        "zabbix_problems",
        ["server_id", "zabbix_eventid"],
        unique=True,
    )

    op.create_table(
        "zabbix_events",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "server_id",
            sa.Integer(),
            sa.ForeignKey("zabbix_servers.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("zabbix_eventid", sa.String(20), nullable=False, index=True),
        sa.Column("name", sa.String(1000), nullable=False),
        sa.Column("severity", sa.String(30), nullable=False, server_default="not_classified"),
        sa.Column("status", sa.String(20), nullable=False, server_default="OK"),
        sa.Column("host", sa.String(200), nullable=True),
        sa.Column("zabbix_hostid", sa.String(20), nullable=True),
        sa.Column("timestamp", sa.String(30), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("zabbix_events")
    op.drop_table("zabbix_problems")
    op.drop_table("zabbix_hosts")
    op.drop_table("zabbix_servers")
