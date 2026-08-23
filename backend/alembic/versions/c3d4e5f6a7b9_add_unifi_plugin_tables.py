"""add_unifi_plugin_tables

Revision ID: c3d4e5f6a7b9
Revises: b2c3d4e5f6a8
Create Date: 2026-07-27

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b9"
down_revision: str | None = "b2c3d4e5f6a8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "unifi_controllers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("encrypted_api_key", sa.Text(), nullable=True),
        sa.Column("controller_type", sa.String(20), nullable=False, server_default=sa.text("'cloud'")),
        sa.Column("verify_ssl", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("timeout", sa.Integer(), nullable=False, server_default=sa.text("30")),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true"), index=True),
        sa.Column("organization_id", sa.String(100), nullable=True),
        sa.Column("organization_name", sa.String(300), nullable=True),
        sa.Column("version", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'unknown'")),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "unifi_sites",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("controller_id", sa.Integer(), sa.ForeignKey("unifi_controllers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("unifi_id", sa.String(100), nullable=False, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("timezone", sa.String(100), nullable=True),
        sa.Column("isp_name", sa.String(200), nullable=True),
        sa.Column("wan_status", sa.String(20), nullable=False, server_default=sa.text("'unknown'")),
        sa.Column("num_devices", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("num_clients", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("last_seen_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "unifi_devices",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("controller_id", sa.Integer(), sa.ForeignKey("unifi_controllers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("site_id", sa.String(100), nullable=False, index=True),
        sa.Column("unifi_id", sa.String(100), nullable=False, index=True),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("model", sa.String(50), nullable=False, server_default=sa.text("'unknown'")),
        sa.Column("serial", sa.String(50), nullable=True),
        sa.Column("mac_address", sa.String(20), nullable=True),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("firmware_version", sa.String(50), nullable=True),
        sa.Column("adoption_state", sa.String(20), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'offline'")),
        sa.Column("uptime_seconds", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("cpu_utilization", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("memory_utilization", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("temperature_c", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("device_type", sa.String(30), nullable=False, server_default=sa.text("'unknown'")),
        sa.Column("last_seen_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "unifi_clients",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("controller_id", sa.Integer(), sa.ForeignKey("unifi_controllers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("site_id", sa.String(100), nullable=False, index=True),
        sa.Column("unifi_id", sa.String(100), nullable=False, index=True),
        sa.Column("hostname", sa.String(300), nullable=True),
        sa.Column("mac_address", sa.String(20), nullable=False, index=True),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("vlan", sa.String(50), nullable=True),
        sa.Column("connected_ap_name", sa.String(200), nullable=True),
        sa.Column("connected_switch_name", sa.String(200), nullable=True),
        sa.Column("rx_bytes", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("tx_bytes", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_wired", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_guest", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("last_seen_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "unifi_alerts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("controller_id", sa.Integer(), sa.ForeignKey("unifi_controllers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("site_id", sa.String(100), nullable=False, index=True),
        sa.Column("unifi_id", sa.String(100), nullable=False, index=True),
        sa.Column("severity", sa.String(20), nullable=False, server_default=sa.text("'info'")),
        sa.Column("device_name", sa.String(200), nullable=True),
        sa.Column("device_id", sa.String(100), nullable=True),
        sa.Column("message", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("is_acknowledged", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "unifi_wireless_networks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("controller_id", sa.Integer(), sa.ForeignKey("unifi_controllers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("site_id", sa.String(100), nullable=False, index=True),
        sa.Column("unifi_id", sa.String(100), nullable=False, index=True),
        sa.Column("ssid", sa.String(200), nullable=False),
        sa.Column("security", sa.String(30), nullable=False, server_default=sa.text("'open'")),
        sa.Column("vlan", sa.String(50), nullable=True),
        sa.Column("is_guest", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("has_alerts", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("unifi_wireless_networks")
    op.drop_table("unifi_alerts")
    op.drop_table("unifi_clients")
    op.drop_table("unifi_devices")
    op.drop_table("unifi_sites")
    op.drop_table("unifi_controllers")
