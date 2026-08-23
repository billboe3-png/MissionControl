"""
Hyper-V Plugin REST API Routes

FastAPI router exposed by the Hyper-V plugin.
All routes are prefixed with /api/v1/plugins/hyperv.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.plugins.installed.hyperv.models import (
    HyperVCheckpoint,
    HyperVHost,
    HyperVNetwork,
    HyperVVM,
    HyperVVolume,
)

logger = logging.getLogger("plugin.hyperv.routes")

router = APIRouter(prefix="/api/v1/plugins/hyperv", tags=["hyperv-plugin"])


@router.get("/hosts")
def list_hosts(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """List all registered Hyper-V hosts."""
    result = db.execute(select(HyperVHost).order_by(HyperVHost.name))
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
            "last_error": h.last_error,
        }
        for h in hosts
    ]


@router.get("/vms")
def list_vms(
    host_id: int | None = Query(None),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """List cached Hyper-V VMs."""
    stmt = select(HyperVVM)
    if host_id:
        stmt = stmt.where(HyperVVM.host_id == host_id)
    stmt = stmt.order_by(HyperVVM.name)
    result = db.execute(stmt)
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
            "last_seen_at": v.last_seen_at.isoformat() if v.last_seen_at else None,
        }
        for v in vms
    ]


@router.get("/networks")
def list_networks(
    host_id: int | None = Query(None),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """List cached Hyper-V virtual switches."""
    stmt = select(HyperVNetwork)
    if host_id:
        stmt = stmt.where(HyperVNetwork.host_id == host_id)
    stmt = stmt.order_by(HyperVNetwork.name)
    result = db.execute(stmt)
    networks = result.scalars().all()
    return [
        {
            "id": n.id,
            "host_id": n.host_id,
            "switch_id": n.switch_id,
            "name": n.name,
            "switch_type": n.switch_type,
            "allow_management_os": n.allow_management_os,
            "status": n.status,
            "connected_vms": n.connected_vms,
        }
        for n in networks
    ]


@router.get("/volumes")
def list_volumes(
    host_id: int | None = Query(None),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """List cached Hyper-V virtual hard disks."""
    stmt = select(HyperVVolume)
    if host_id:
        stmt = stmt.where(HyperVVolume.host_id == host_id)
    stmt = stmt.order_by(HyperVVolume.name)
    result = db.execute(stmt)
    volumes = result.scalars().all()
    return [
        {
            "id": v.id,
            "host_id": v.host_id,
            "disk_id": v.disk_id,
            "name": v.name,
            "path": v.path,
            "size_bytes": v.size_bytes,
            "used_bytes": v.used_bytes,
            "type": v.type,
            "vm_name": v.vm_name,
            "attached": v.attached,
        }
        for v in volumes
    ]


@router.get("/checkpoints")
def list_checkpoints(
    host_id: int | None = Query(None),
    vm_id: str | None = Query(None),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """List cached Hyper-V checkpoints."""
    stmt = select(HyperVCheckpoint)
    if host_id:
        stmt = stmt.where(HyperVCheckpoint.host_id == host_id)
    if vm_id:
        stmt = stmt.where(HyperVCheckpoint.vm_id == vm_id)
    stmt = stmt.order_by(HyperVCheckpoint.name)
    result = db.execute(stmt)
    checkpoints = result.scalars().all()
    return [
        {
            "id": c.id,
            "host_id": c.host_id,
            "checkpoint_id": c.checkpoint_id,
            "vm_id": c.vm_id,
            "vm_name": c.vm_name,
            "name": c.name,
            "checkpoint_type": c.checkpoint_type,
            "creation_time": c.creation_time,
            "size_bytes": c.size_bytes,
        }
        for c in checkpoints
    ]


@router.get("/summary")
def get_summary(
    host_id: int | None = Query(None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Aggregated Hyper-V monitoring summary."""
    host_filter = [HyperVVM.host_id == host_id] if host_id else []

    vm_q = select(func.count(HyperVVM.id))
    if host_filter:
        vm_q = vm_q.where(*host_filter)
    vm_count = (db.execute(vm_q)).scalar() or 0

    running_q = select(func.count(HyperVVM.id)).where(HyperVVM.state == "running")
    if host_filter:
        running_q = running_q.where(*host_filter)
    running_count = (db.execute(running_q)).scalar() or 0

    stopped_q = select(func.count(HyperVVM.id)).where(HyperVVM.state == "stopped")
    if host_filter:
        stopped_q = stopped_q.where(*host_filter)
    stopped_count = (db.execute(stopped_q)).scalar() or 0

    paused_q = select(func.count(HyperVVM.id)).where(HyperVVM.state == "paused")
    if host_filter:
        paused_q = paused_q.where(*host_filter)
    paused_count = (db.execute(paused_q)).scalar() or 0

    checkpoint_q = select(func.count(HyperVCheckpoint.id))
    if host_filter:
        checkpoint_q = checkpoint_q.where(*host_filter)
    checkpoint_count = (db.execute(checkpoint_q)).scalar() or 0

    state_q = (
        select(HyperVVM.state, func.count(HyperVVM.id))
    )
    if host_filter:
        state_q = state_q.where(*host_filter)
    state_q = state_q.group_by(HyperVVM.state)
    state_rows = (db.execute(state_q)).all()
    state_counts = {row[0]: row[1] for row in state_rows}

    return {
        "vm_count": vm_count,
        "running_count": running_count,
        "stopped_count": stopped_count,
        "paused_count": paused_count,
        "checkpoint_count": checkpoint_count,
        "state_counts": state_counts,
    }


@router.get("/health")
def get_health(
    host_id: int | None = Query(None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Health status of cached Hyper-V hosts."""
    stmt = select(HyperVHost)
    if host_id:
        stmt = stmt.where(HyperVHost.id == host_id)
    result = db.execute(stmt)
    hosts = result.scalars().all()
    return {
        "hosts": [
            {
                "id": h.id,
                "name": h.name,
                "status": h.status,
                "last_sync_at": h.last_sync_at.isoformat() if h.last_sync_at else None,
                "last_error": h.last_error,
            }
            for h in hosts
        ],
        "total": len(hosts),
        "healthy": sum(1 for h in hosts if h.status == "healthy"),
    }
