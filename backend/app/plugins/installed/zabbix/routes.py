"""
Zabbix Plugin REST API Routes

FastAPI router exposed by the Zabbix plugin.
All routes are prefixed with /api/v1/plugins/zabbix.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.plugins.installed.zabbix.models import (
    ZabbixEvent,
    ZabbixHost,
    ZabbixProblem,
    ZabbixServer,
)

logger = logging.getLogger("plugin.zabbix.routes")

router = APIRouter(prefix="/api/v1/plugins/zabbix", tags=["zabbix-plugin"])


@router.get("/servers")
def list_servers(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """List all registered Zabbix servers."""
    result = db.execute(select(ZabbixServer).order_by(ZabbixServer.name))
    servers = result.scalars().all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "url": s.url,
            "enabled": s.enabled,
            "status": s.status,
            "version": s.version,
            "last_sync_at": s.last_sync_at.isoformat() if s.last_sync_at else None,
            "last_error": s.last_error,
        }
        for s in servers
    ]


@router.get("/hosts")
def list_hosts(
    server_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """List cached Zabbix hosts."""
    stmt = select(ZabbixHost)
    if server_id:
        stmt = stmt.where(ZabbixHost.server_id == server_id)
    stmt = stmt.order_by(ZabbixHost.host)
    result = db.execute(stmt)
    hosts = result.scalars().all()
    return [
        {
            "id": h.id,
            "server_id": h.server_id,
            "zabbix_hostid": h.zabbix_hostid,
            "host": h.host,
            "name": h.name,
            "status": h.status,
            "available": h.available,
            "interface_ip": h.interface_ip,
            "last_seen_at": h.last_seen_at.isoformat() if h.last_seen_at else None,
        }
        for h in hosts
    ]


@router.get("/problems")
def list_problems(
    server_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """List cached Zabbix problems."""
    stmt = select(ZabbixProblem).where(ZabbixProblem.resolved_at.is_(None))
    if server_id:
        stmt = stmt.where(ZabbixProblem.server_id == server_id)
    stmt = stmt.order_by(ZabbixProblem.id.desc())
    result = db.execute(stmt)
    problems = result.scalars().all()
    return [
        {
            "id": p.id,
            "server_id": p.server_id,
            "zabbix_eventid": p.zabbix_eventid,
            "name": p.name,
            "severity": p.severity,
            "acknowledged": p.acknowledged,
            "host": p.host,
            "timestamp": p.timestamp,
        }
        for p in problems
    ]


@router.get("/events")
def list_events(
    server_id: int | None = None,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """List cached Zabbix events."""
    stmt = select(ZabbixEvent)
    if server_id:
        stmt = stmt.where(ZabbixEvent.server_id == server_id)
    stmt = stmt.order_by(ZabbixEvent.id.desc()).limit(limit)
    result = db.execute(stmt)
    events = result.scalars().all()
    return [
        {
            "id": e.id,
            "server_id": e.server_id,
            "zabbix_eventid": e.zabbix_eventid,
            "name": e.name,
            "severity": e.severity,
            "status": e.status,
            "host": e.host,
            "timestamp": e.timestamp,
        }
        for e in events
    ]


@router.get("/summary")
def get_summary(
    server_id: int | None = None,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Aggregated Zabbix monitoring summary."""
    server_filter = [ZabbixHost.server_id == server_id] if server_id else []

    host_q = select(func.count(ZabbixHost.id))
    if server_filter:
        host_q = host_q.where(*server_filter)
    host_count = (db.execute(host_q)).scalar() or 0

    avail_q = select(func.count(ZabbixHost.id)).where(ZabbixHost.available == "available")
    if server_filter:
        avail_q = avail_q.where(*server_filter)
    available_count = (db.execute(avail_q)).scalar() or 0

    problem_q = select(func.count(ZabbixProblem.id)).where(ZabbixProblem.resolved_at.is_(None))
    if server_filter:
        problem_q = problem_q.where(*server_filter)
    problem_count = (db.execute(problem_q)).scalar() or 0

    severity_q = (
        select(ZabbixProblem.severity, func.count(ZabbixProblem.id))
        .where(ZabbixProblem.resolved_at.is_(None))
    )
    if server_filter:
        severity_q = severity_q.where(*server_filter)
    severity_q = severity_q.group_by(ZabbixProblem.severity)
    severity_rows = (db.execute(severity_q)).all()
    severity_counts = {row[0]: row[1] for row in severity_rows}

    return {
        "host_count": host_count,
        "available_count": available_count,
        "unavailable_count": host_count - available_count,
        "problem_count": problem_count,
        "severity_counts": severity_counts,
    }
