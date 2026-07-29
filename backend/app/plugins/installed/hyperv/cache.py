"""
Hyper-V Plugin Cache

Provides convenient read access to cached Hyper-V data.
All queries use synchronous SQLAlchemy sessions.
"""

import logging
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.plugins.installed.hyperv.models import (
    HyperVCheckpoint,
    HyperVHost,
    HyperVNetwork,
    HyperVVM,
    HyperVVolume,
)

logger = logging.getLogger("plugin.hyperv.cache")


def get_summary(session: Session, host_id: int | None = None) -> dict[str, Any]:
    """Return aggregated summary from cached data."""
    host_filter = [HyperVVM.host_id == host_id] if host_id else []

    vm_count = (
        session.execute(
            select(func.count(HyperVVM.id)).where(*host_filter) if host_filter
            else select(func.count(HyperVVM.id))
        )
    ).scalar() or 0

    running_count = (
        session.execute(
            select(func.count(HyperVVM.id))
            .where(HyperVVM.state == "running")
            .where(*host_filter) if host_filter
            else select(func.count(HyperVVM.id)).where(HyperVVM.state == "running")
        )
    ).scalar() or 0

    stopped_count = (
        session.execute(
            select(func.count(HyperVVM.id))
            .where(HyperVVM.state == "stopped")
            .where(*host_filter) if host_filter
            else select(func.count(HyperVVM.id)).where(HyperVVM.state == "stopped")
        )
    ).scalar() or 0

    paused_count = (
        session.execute(
            select(func.count(HyperVVM.id))
            .where(HyperVVM.state == "paused")
            .where(*host_filter) if host_filter
            else select(func.count(HyperVVM.id)).where(HyperVVM.state == "paused")
        )
    ).scalar() or 0

    checkpoint_count = (
        session.execute(
            select(func.count(HyperVCheckpoint.id)).where(*host_filter) if host_filter
            else select(func.count(HyperVCheckpoint.id))
        )
    ).scalar() or 0

    host_count = (
        session.execute(
            select(func.count(HyperVHost.id)).where(HyperVHost.id == host_id) if host_id
            else select(func.count(HyperVHost.id))
        )
    ).scalar() or 0

    return {
        "vm_count": vm_count,
        "running_count": running_count,
        "stopped_count": stopped_count,
        "paused_count": paused_count,
        "checkpoint_count": checkpoint_count,
        "host_count": host_count,
    }


def get_hosts(session: Session) -> list[dict[str, Any]]:
    """Return all cached hosts."""
    result = session.execute(select(HyperVHost).order_by(HyperVHost.name))
    hosts = result.scalars().all()
    return [
        {
            "id": h.id,
            "name": h.name,
            "hostname": h.hostname,
            "transport": h.transport,
            "port": h.port,
            "enabled": h.enabled,
            "status": h.status,
            "version": h.version,
            "last_sync_at": h.last_sync_at.isoformat() if h.last_sync_at else None,
        }
        for h in hosts
    ]


def get_vms(session: Session, state: str | None = None, host_id: int | None = None) -> list[dict[str, Any]]:
    """Return cached VMs, optionally filtered by state."""
    stmt = select(HyperVVM)
    if state:
        stmt = stmt.where(HyperVVM.state == state)
    if host_id:
        stmt = stmt.where(HyperVVM.host_id == host_id)
    stmt = stmt.order_by(HyperVVM.name)
    result = session.execute(stmt)
    vms = result.scalars().all()
    return [
        {
            "id": v.id,
            "host_id": v.host_id,
            "vm_id": v.vm_id,
            "name": v.name,
            "state": v.state,
            "cpu_count": v.cpu_count,
            "memory_assigned_mb": v.memory_assigned_mb,
            "uptime_seconds": v.uptime_seconds,
            "host_server": v.host_server,
            "guest_os": v.guest_os,
            "cpu_usage_percent": v.cpu_usage_percent,
        }
        for v in vms
    ]


def get_networks(session: Session, host_id: int | None = None) -> list[dict[str, Any]]:
    """Return cached virtual switches."""
    stmt = select(HyperVNetwork)
    if host_id:
        stmt = stmt.where(HyperVNetwork.host_id == host_id)
    stmt = stmt.order_by(HyperVNetwork.name)
    result = session.execute(stmt)
    networks = result.scalars().all()
    return [
        {
            "id": n.id,
            "name": n.name,
            "switch_type": n.switch_type,
            "allow_management_os": n.allow_management_os,
            "status": n.status,
            "connected_vms": n.connected_vms,
        }
        for n in networks
    ]


def get_volumes(session: Session, host_id: int | None = None) -> list[dict[str, Any]]:
    """Return cached virtual hard disks."""
    stmt = select(HyperVVolume)
    if host_id:
        stmt = stmt.where(HyperVVolume.host_id == host_id)
    stmt = stmt.order_by(HyperVVolume.name)
    result = session.execute(stmt)
    volumes = result.scalars().all()
    return [
        {
            "id": v.id,
            "name": v.name,
            "path": v.path,
            "size_bytes": v.size_bytes,
            "used_bytes": v.used_bytes,
            "type": v.type,
            "vm_name": v.vm_name,
        }
        for v in volumes
    ]


def get_checkpoints(session: Session, host_id: int | None = None) -> list[dict[str, Any]]:
    """Return cached checkpoints."""
    stmt = select(HyperVCheckpoint)
    if host_id:
        stmt = stmt.where(HyperVCheckpoint.host_id == host_id)
    stmt = stmt.order_by(HyperVCheckpoint.name)
    result = session.execute(stmt)
    checkpoints = result.scalars().all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "vm_name": c.vm_name,
            "checkpoint_type": c.checkpoint_type,
            "creation_time": c.creation_time,
            "size_bytes": c.size_bytes,
        }
        for c in checkpoints
    ]


class CacheManager:
    """Wrapper providing method-style access to cache functions."""

    def get_summary(self, session: Session, host_id: int | None = None) -> dict[str, Any]:
        return get_summary(session, host_id)

    def get_hosts(self, session: Session) -> list[dict[str, Any]]:
        return get_hosts(session)

    def get_vms(self, session: Session, state: str | None = None, host_id: int | None = None) -> list[dict[str, Any]]:
        return get_vms(session, state, host_id)

    def get_networks(self, session: Session, host_id: int | None = None) -> list[dict[str, Any]]:
        return get_networks(session, host_id)

    def get_volumes(self, session: Session, host_id: int | None = None) -> list[dict[str, Any]]:
        return get_volumes(session, host_id)

    def get_checkpoints(self, session: Session, host_id: int | None = None) -> list[dict[str, Any]]:
        return get_checkpoints(session, host_id)


cache_manager = CacheManager()
