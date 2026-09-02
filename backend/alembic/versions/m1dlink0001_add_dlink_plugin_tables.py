"""
Add D-Link DGS-1210 plugin tables

Revision ID: m1dlink0001
Revises: m3kr0t1k0003
Create Date: 2026-08-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "m1dlink0001"
down_revision = "m2kr0t1k0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # D-Link Switches
    op.create_table(
        "dlink_switches",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("host", sa.String(length=255), nullable=False),
        sa.Column("ssh_port", sa.Integer(), nullable=False, server_default="22"),
        sa.Column("telnet_port", sa.Integer(), nullable=False, server_default="23"),
        sa.Column("webui_port", sa.Integer(), nullable=False, server_default="443"),
        sa.Column("webui_use_https", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("relay_agent_id", sa.Integer(), nullable=False),
        sa.Column("remote_target_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("site_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="unknown"),
        sa.Column("firmware_version", sa.String(length=64), nullable=True),
        sa.Column("hardware_version", sa.String(length=64), nullable=True),
        sa.Column("serial_number", sa.String(length=64), nullable=True),
        sa.Column("model_name", sa.String(length=64), nullable=True),
        sa.Column("mac_address", sa.String(length=17), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_seen", sa.DateTime(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dlink_switches_host", "dlink_switches", ["host"], unique=False)
    op.create_index("ix_dlink_switches_relay_agent", "dlink_switches", ["relay_agent_id"], unique=False)
    op.create_index("ix_dlink_switches_remote_target", "dlink_switches", ["remote_target_id"], unique=False)
    op.create_index("ix_dlink_switches_status", "dlink_switches", ["status"], unique=False)

    # D-Link Remote Targets
    op.create_table(
        "dlink_remote_targets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("hostname", sa.String(length=255), nullable=False),
        sa.Column("protocol", sa.String(length=16), nullable=False, server_default="ssh"),
        sa.Column("port", sa.Integer(), nullable=False, server_default="22"),
        sa.Column("username", sa.String(length=64), nullable=False, server_default="admin"),
        sa.Column("password_encrypted", sa.Text(), nullable=False),
        sa.Column("ssh_key_encrypted", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("tags", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("target_plugins", sa.String(length=128), nullable=False, server_default="dlink"),
        sa.Column("last_collected_at", sa.DateTime(), nullable=True),
        sa.Column("last_status", sa.String(length=32), nullable=False, server_default="unknown"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dlink_remote_targets_agent", "dlink_remote_targets", ["agent_id"], unique=False)
    op.create_index("ix_dlink_remote_targets_hostname", "dlink_remote_targets", ["hostname"], unique=False)

    # D-Link MAC Address Table Entries (FDB)
    op.create_table(
        "dlink_mac_entries",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("switch_id", sa.Integer(), nullable=False),
        sa.Column("mac_address", sa.String(length=17), nullable=False),
        sa.Column("vlan_id", sa.Integer(), nullable=False),
        sa.Column("port", sa.String(length=16), nullable=False),
        sa.Column("type", sa.String(length=16), nullable=False, server_default="dynamic"),
        sa.Column("first_seen", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("last_seen", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.ForeignKeyConstraint(["switch_id"], ["dlink_switches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("switch_id", "mac_address", "vlan_id", "port", name="uq_dlink_mac_switch_vlan_port"),
    )
    op.create_index("ix_dlink_mac_switch_port", "dlink_mac_entries", ["switch_id", "port"], unique=False)
    op.create_index("ix_dlink_mac_switch_vlan", "dlink_mac_entries", ["switch_id", "vlan_id"], unique=False)
    op.create_index("ix_dlink_mac_active", "dlink_mac_entries", ["is_active", "last_seen"], unique=False)
    op.create_index("ix_dlink_mac_address", "dlink_mac_entries", ["mac_address"], unique=False)

    # D-Link VLANs
    op.create_table(
        "dlink_vlans",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("switch_id", sa.Integer(), nullable=False),
        sa.Column("vlan_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=32), nullable=True),
        sa.Column("ports_tagged", sa.Text(), nullable=True),
        sa.Column("ports_untagged", sa.Text(), nullable=True),
        sa.Column("ports_forbidden", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["switch_id"], ["dlink_switches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("switch_id", "vlan_id", name="uq_dlink_vlan_switch_vlan"),
    )
    op.create_index("ix_dlink_vlan_switch", "dlink_vlans", ["switch_id"], unique=False)

    # D-Link Port VLAN Configuration
    op.create_table(
        "dlink_port_vlans",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("switch_id", sa.Integer(), nullable=False),
        sa.Column("port", sa.String(length=16), nullable=False),
        sa.Column("pvid", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("allowed_vlans", sa.Text(), nullable=True),
        sa.Column("mode", sa.String(length=16), nullable=False, server_default="access"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["switch_id"], ["dlink_switches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("switch_id", "port", name="uq_dlink_port_vlan_switch_port"),
    )
    op.create_index("ix_dlink_port_vlan_switch", "dlink_port_vlans", ["switch_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_dlink_port_vlan_switch", table_name="dlink_port_vlans")
    op.drop_table("dlink_port_vlans")
    op.drop_index("ix_dlink_vlan_switch", table_name="dlink_vlans")
    op.drop_table("dlink_vlans")
    op.drop_index("ix_dlink_mac_address", table_name="dlink_mac_entries")
    op.drop_index("ix_dlink_mac_active", table_name="dlink_mac_entries")
    op.drop_index("ix_dlink_mac_switch_vlan", table_name="dlink_mac_entries")
    op.drop_index("ix_dlink_mac_switch_port", table_name="dlink_mac_entries")
    op.drop_table("dlink_mac_entries")
    op.drop_index("ix_dlink_remote_targets_hostname", table_name="dlink_remote_targets")
    op.drop_index("ix_dlink_remote_targets_agent", table_name="dlink_remote_targets")
    op.drop_table("dlink_remote_targets")
    op.drop_index("ix_dlink_switches_status", table_name="dlink_switches")
    op.drop_index("ix_dlink_switches_remote_target", table_name="dlink_switches")
    op.drop_index("ix_dlink_switches_relay_agent", table_name="dlink_switches")
    op.drop_index("ix_dlink_switches_host", table_name="dlink_switches")
    op.drop_table("dlink_switches")