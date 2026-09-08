"""add_mikrotik_plugin_tables

Revision ID: m1kr0t1k0001
Revises: 7d81f75aecf6
Create Date: 2026-08-24

Creates the tables backing the official_mikrotik plugin: registered
servers, command audit log, and cached interfaces/firewall/DHCP data.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "m1kr0t1k0001"
down_revision: str | None = "7d81f75aecf6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "mikrotik_servers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("host", sa.String(500), nullable=False, index=True),
        sa.Column("ssh_port", sa.Integer(), nullable=False, server_default=sa.text("22")),
        sa.Column("telnet_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("telnet_port", sa.Integer(), nullable=True),
        sa.Column("username", sa.String(200), nullable=False, server_default=sa.text("'admin'")),
        sa.Column("password_encrypted", sa.Text(), nullable=True),
        sa.Column("api_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("api_port", sa.Integer(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true"), index=True),
        sa.Column("last_sync_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'unknown'"), index=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("version", sa.String(50), nullable=True),
        sa.Column("board_name", sa.String(100), nullable=True),
        sa.Column("cpu_load", sa.String(20), nullable=True),
        sa.Column("memory_usage_pct", sa.Integer(), nullable=True),
        sa.Column("uptime", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "mikrotik_command_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "server_id",
            sa.Integer(),
            sa.ForeignKey("mikrotik_servers.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("connector_type", sa.String(20), nullable=False),
        sa.Column("command", sa.Text(), nullable=False),
        sa.Column("output", sa.Text(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("executed_by", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True, index=True),
    )

    op.create_table(
        "mikrotik_interfaces",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "server_id",
            sa.Integer(),
            sa.ForeignKey("mikrotik_servers.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(200), nullable=False, index=True),
        sa.Column("type", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=True),
        sa.Column("link_status", sa.String(20), nullable=True),
        sa.Column("rx_byte_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("tx_byte_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("rx_packet_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("tx_packet_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("mac_address", sa.String(50), nullable=True),
        sa.Column("actual_mtu", sa.Integer(), nullable=True),
        sa.Column("last_seen", sa.DateTime(), nullable=True),
        sa.Column("synced_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "mikrotik_firewall_rules",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "server_id",
            sa.Integer(),
            sa.ForeignKey("mikrotik_servers.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("chain", sa.String(50), nullable=False, index=True),
        sa.Column("action", sa.String(50), nullable=True),
        sa.Column("comment", sa.String(300), nullable=True),
        sa.Column("disabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("bytes_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("packet_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("synced_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "mikrotik_dhcp_leases",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "server_id",
            sa.Integer(),
            sa.ForeignKey("mikrotik_servers.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("address", sa.String(50), nullable=True),
        sa.Column("mac_address", sa.String(50), nullable=False, index=True),
        sa.Column("host_name", sa.String(200), nullable=True),
        sa.Column("client_id", sa.String(200), nullable=True),
        sa.Column("status", sa.String(30), nullable=True),
        sa.Column("expires_after", sa.String(100), nullable=True),
        sa.Column("synced_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("mikrotik_dhcp_leases")
    op.drop_table("mikrotik_firewall_rules")
    op.drop_table("mikrotik_interfaces")
    op.drop_table("mikrotik_command_logs")
    op.drop_table("mikrotik_servers")
