"""
D-Link DGS-1210 Database Models
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class DLinkSwitch(Base):
    """D-Link DGS-1210 Switch managed by Mission Control."""
    __tablename__ = "dlink_switches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    host = Column(String(255), nullable=False)
    ssh_port = Column(Integer, default=22)
    telnet_port = Column(Integer, default=23)
    webui_port = Column(Integer, default=443)
    webui_use_https = Column(Boolean, default=True)
    relay_agent_id = Column(Integer, nullable=False)
    remote_target_id = Column(Integer, nullable=False)
    company_id = Column(Integer, nullable=True)
    site_id = Column(Integer, nullable=True)
    status = Column(String(32), default="unknown")
    firmware_version = Column(String(64), nullable=True)
    hardware_version = Column(String(64), nullable=True)
    serial_number = Column(String(64), nullable=True)
    model_name = Column(String(64), nullable=True)
    mac_address = Column(String(17), nullable=True)
    enabled = Column(Boolean, default=True)
    last_seen = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    mac_entries = relationship("DLinkMacEntry", back_populates="switch", cascade="all, delete-orphan")
    vlans = relationship("DLinkVlan", back_populates="switch", cascade="all, delete-orphan")
    port_vlans = relationship("DLinkPortVlan", back_populates="switch", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_dlink_switches_host", "host"),
        Index("ix_dlink_switches_relay_agent", "relay_agent_id"),
        Index("ix_dlink_switches_remote_target", "remote_target_id"),
        Index("ix_dlink_switches_status", "status"),
    )


class DLinkRemoteTarget(Base):
    """Remote target configuration for D-Link switch SSH/Telnet access."""
    __tablename__ = "dlink_remote_targets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, nullable=False)
    name = Column(String(128), nullable=False)
    hostname = Column(String(255), nullable=False)
    protocol = Column(String(16), default="ssh")
    port = Column(Integer, default=22)
    username = Column(String(64), default="admin")
    password_encrypted = Column(Text, nullable=False)
    ssh_key_encrypted = Column(Text, nullable=True)
    enabled = Column(Boolean, default=True)
    tags = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    target_plugins = Column(String(128), default="dlink")
    last_collected_at = Column(DateTime, nullable=True)
    last_status = Column(String(32), default="unknown")
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_dlink_remote_targets_agent", "agent_id"),
        Index("ix_dlink_remote_targets_hostname", "hostname"),
    )


class DLinkMacEntry(Base):
    """MAC Address Table (FDB) entries for device location tracking."""
    __tablename__ = "dlink_mac_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    switch_id = Column(Integer, ForeignKey("dlink_switches.id", ondelete="CASCADE"), nullable=False)
    mac_address = Column(String(17), nullable=False, index=True)
    vlan_id = Column(Integer, nullable=False, index=True)
    port = Column(String(16), nullable=False, index=True)
    type = Column(String(16), default="dynamic")
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationship
    switch = relationship("DLinkSwitch", back_populates="mac_entries")

    __table_args__ = (
        UniqueConstraint("switch_id", "mac_address", "vlan_id", "port", name="uq_dlink_mac_switch_vlan_port"),
        Index("ix_dlink_mac_switch_port", "switch_id", "port"),
        Index("ix_dlink_mac_switch_vlan", "switch_id", "vlan_id"),
        Index("ix_dlink_mac_active", "is_active", "last_seen"),
    )


class DLinkVlan(Base):
    """VLAN configuration on D-Link switch."""
    __tablename__ = "dlink_vlans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    switch_id = Column(Integer, ForeignKey("dlink_switches.id", ondelete="CASCADE"), nullable=False)
    vlan_id = Column(Integer, nullable=False, index=True)
    name = Column(String(32), nullable=True)
    ports_tagged = Column(Text, nullable=True)
    ports_untagged = Column(Text, nullable=True)
    ports_forbidden = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    switch = relationship("DLinkSwitch", back_populates="vlans")

    __table_args__ = (
        UniqueConstraint("switch_id", "vlan_id", name="uq_dlink_vlan_switch_vlan"),
        Index("ix_dlink_vlan_switch", "switch_id"),
    )


class DLinkPortVlan(Base):
    """Per-port VLAN configuration (PVID, allowed VLANs, mode)."""
    __tablename__ = "dlink_port_vlans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    switch_id = Column(Integer, ForeignKey("dlink_switches.id", ondelete="CASCADE"), nullable=False)
    port = Column(String(16), nullable=False, index=True)
    pvid = Column(Integer, default=1)
    allowed_vlans = Column(Text, nullable=True)
    mode = Column(String(16), default="access")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    switch = relationship("DLinkSwitch", back_populates="port_vlans")

    __table_args__ = (
        UniqueConstraint("switch_id", "port", name="uq_dlink_port_vlan_switch_port"),
        Index("ix_dlink_port_vlan_switch", "switch_id"),
    )