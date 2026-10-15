"""
Veeam Plugin REST API Routes

FastAPI router exposed by the Veeam plugin.
Cache routes serve widget data from cache_manager.
Live routes serve DB snapshots, re-collected when older than
SNAPSHOT_TTL_SECONDS; ?refresh=1 forces live collection.
"""

import json
import logging
import os
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth_dependency import get_current_user
from app.core.config import get_settings
from app.core.security import CredentialCipher
from app.db.database import get_db
from app.models.db.agent import Agent
from app.plugins.installed.official_veeam.cache import cache_manager
from app.plugins.installed.official_veeam.collector import _upsert_snapshot
from app.plugins.installed.official_veeam.models import (
    VeeamBackupServer,
    VeeamSnapshot,
)
from app.plugins.installed.official_veeam.provider import build_server_provider

logger = logging.getLogger("plugin.veeam.routes")

router = APIRouter(
    prefix="/api/v1/plugins/veeam",
    tags=["veeam-plugin"],
    dependencies=[Depends(get_current_user)],
)

_NO_SERVER = "No Veeam server configured"

SNAPSHOT_TTL_SECONDS = int(os.environ.get("VEEAM_SNAPSHOT_TTL_SECONDS", "900"))


def _snapshot_age(row: VeeamSnapshot) -> float:
    collected = row.collected_at
    if collected.tzinfo is None:
        collected = collected.replace(tzinfo=UTC)
    return (datetime.now(UTC) - collected).total_seconds()


# Pydantic models for server config API
class VeeamServerConfigBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    url: str = Field("", min_length=0, max_length=500)
    username: str = Field("", min_length=0, max_length=200)
    password: str = Field("", max_length=500)
    verify_ssl: bool = True
    timeout: int = Field(30, ge=5, le=300)
    enabled: bool = True
    ssh_host: str = Field("", max_length=200)
    ssh_port: int = Field(22, ge=1, le=65535)
    ssh_username: str = Field("", max_length=200)
    ssh_password: str = Field("", max_length=500)
    data_source: str = Field("both", pattern="^(both|rest|ssh)$")
    db_type: str = Field("postgresql", pattern="^(auto|postgresql|mssql)$")
    column_case: str = Field("pascal", pattern="^(auto|pascal|snake)$")


class VeeamServerConfigCreate(VeeamServerConfigBase):
    pass


class VeeamServerConfigUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    url: str | None = Field(None, max_length=500)
    username: str | None = Field(None, max_length=200)
    password: str | None = Field(None, max_length=500)
    verify_ssl: bool | None = None
    timeout: int | None = Field(None, ge=5, le=300)
    enabled: bool | None = None
    ssh_host: str | None = Field(None, max_length=200)
    ssh_port: int | None = Field(None, ge=1, le=65535)
    ssh_username: str | None = Field(None, max_length=200)
    ssh_password: str | None = Field(None, max_length=500)
    data_source: str | None = Field(None, pattern="^(both|rest|ssh)$")
    db_type: str | None = Field(None, pattern="^(auto|postgresql|mssql)$")
    column_case: str | None = Field(None, pattern="^(auto|pascal|snake)$")


class VeeamServerConfigResponse(VeeamServerConfigBase):
    id: int
    # True when at least one cached snapshot for this server was collected
    # successfully. Lets clients pick a server that actually returns data
    # instead of defaulting to an unreachable/lowest-id one.
    has_data: bool = False

    url: str | None = None
    username: str | None = None
    ssh_host: str | None = None
    ssh_username: str | None = None
    password: str | None = None
    ssh_password: str | None = None

    class Config:
        from_attributes = True


# ------------------------------------------------------------------ #
# Cache routes (unchanged — back widget cache)                        #
# ------------------------------------------------------------------ #


@router.get("/licenses")
def list_licenses(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    return cache_manager.get_license(db)


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)) -> dict[str, Any]:
    return cache_manager.get_summary(db)


@router.get("/repo-health")
def get_repo_health(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    return cache_manager.get_repo_health(db)


@router.get("/jobs-by-status")
def get_jobs_by_status(db: Session = Depends(get_db)) -> dict[str, int]:
    return cache_manager.get_jobs_by_status(db)


@router.get("/jobs-by-type")
def get_jobs_by_type(db: Session = Depends(get_db)) -> dict[str, int]:
    return cache_manager.get_jobs_by_type(db)


# ------------------------------------------------------------------ #
# Live snapshot routes                                                #
# ------------------------------------------------------------------ #


def _first_server(db: Session) -> VeeamBackupServer | None:
    return (
        db.query(VeeamBackupServer)
        .filter(VeeamBackupServer.enabled.is_(True))
        .order_by(VeeamBackupServer.edition.desc(), VeeamBackupServer.id)
        .first()
    )



def _resolve_server(db: Session, server_id: int | None) -> VeeamBackupServer | None:
    if server_id is not None:
        server = db.query(VeeamBackupServer).filter(
            VeeamBackupServer.id == server_id,
            VeeamBackupServer.enabled.is_(True),
        ).first()
        if server is None:
            raise HTTPException(status_code=404, detail="Veeam server not found")
        return server
    return _first_server(db)


def _failed(kind: str, error: str) -> dict[str, Any]:
    if kind == "overview":
        return {
            "success": False, "version": "", "name": "",
            "total_jobs": 0, "running_jobs": 0, "total_repositories": 0,
            "total_space_bytes": 0, "used_space_bytes": 0, "recent_sessions": 0,
            "sessions_success": 0, "sessions_warning": 0, "sessions_failed": 0,
            "error": error,
        }
    if kind == "health":
        return {"healthy": False, "version": "", "name": "", "error": error}
    if kind == "test":
        return {
            "connected": False, "version": "", "name": "",
            "server_id": None, "error": error,
        }
    if kind == "jobs":
        return {"success": False, "jobs": [], "count": 0, "server_names": [], "error": error}
    if kind == "job_stats":
        return {
            "success": False, "jobs": [], "ssh_available": False,
            "count": 0, "message": None, "error": error,
        }
    if kind == "job_stats_daily":
        return {
            "success": False, "jobs": [], "dates": [], "ssh_available": False,
            "count": 0, "server_names": [], "message": None, "error": error,
        }
    if kind == "job_detail":
        return {"success": False, "job": None, "error": error}
    if kind == "job_control":
        return {"success": False, "message": None, "error": error}
    if kind == "sessions":
        return {"success": False, "sessions": [], "count": 0, "server_names": [], "error": error}
    if kind == "session_stats":
        return {
            "success": False, "stats": [], "ssh_available": False,
            "count": 0, "message": None, "error": error,
        }
    if kind == "repositories":
        return {"success": False, "repositories": [], "count": 0, "error": error}
    if kind == "servers":
        return {"success": False, "servers": [], "count": 0, "error": error}
    if kind == "restore_points":
        return {"success": False, "restore_points": [], "count": 0, "error": error}
    if kind == "license":
        return {"success": False, "license": None, "error": error}
    if kind == "capacity_tier":
        return {"success": False, "object_storages": [], "count": 0, "error": error}
    return {"success": False, "error": error}


def _cached_success(row: VeeamSnapshot) -> dict[str, Any] | None:
    """Return the cached payload only when it is a *successful* collection.

    A cached failure is not data: re-serving it (as "stale") would hide the
    live error behind a misleading timestamp and let one transient outage
    poison the cache for a server that never actually returned anything.
    """
    try:
        payload = json.loads(row.payload)
    except (ValueError, TypeError):
        return None
    return payload if payload.get("success") else None


def _server_agent_offline(db: Session, server: VeeamBackupServer) -> str | None:
    """Name of the linked agent when it exists but is not online.

    Returns None when the server has no linked agent (API/direct data source)
    or the agent is online, so callers only surface an offline banner when the
    relay that actually feeds this server cannot be reached.
    """
    agent_id = getattr(server, "agent_id", None)
    if agent_id is None:
        return None
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if agent is None:
        return None
    if (getattr(agent, "status", None) or "").lower() == "online":
        return None
    return agent.name


def _stale_payload(
    cached: dict[str, Any], row: VeeamSnapshot, offline_name: str | None
) -> dict[str, Any]:
    """Serve cached data with a timestamp banner and, when known, offline note."""
    stale = dict(cached)
    collected_at = row.collected_at.isoformat() if row.collected_at else None
    stale["stale"] = True
    stale["collected_at"] = collected_at
    if offline_name:
        stale["offline"] = True
        stale["agent_name"] = offline_name
        stale["error"] = (
            f"Agent '{offline_name}' is offline — showing last data received"
            + (f" {collected_at}" if collected_at else "")
            + ". Data may be outdated."
        )
    else:
        stale["error"] = (
            f"Data may be stale — last collected {collected_at}"
            if collected_at
            else "Data may be stale"
        )
    return stale


def _offline_payload(payload: dict[str, Any], offline_name: str | None) -> dict[str, Any]:
    """Annotate a live failure with the offline agent so the UI can say so."""
    if not offline_name:
        return payload
    out = dict(payload)
    out["offline"] = True
    out["agent_name"] = offline_name
    out.setdefault("collected_at", None)
    return out


def _fallback_daily_snapshot(db: Session, server_id: int) -> VeeamSnapshot | None:
    """Most recent successful job_stats_daily snapshot for any window.

    The daily dataset key embeds the requested window (days + system flag), so
    a request for a window the hourly collector never wrote (e.g. the UI's 8
    days vs the collector's 7) finds no exact cache. Falling back to the newest
    successful daily snapshot lets the page still show the last data received
    instead of only the live failure.
    """
    rows = db.execute(
        select(VeeamSnapshot)
        .where(
            VeeamSnapshot.server_id == server_id,
            VeeamSnapshot.dataset.like("job_stats_daily:%"),
        )
        .order_by(VeeamSnapshot.collected_at.desc())
    ).scalars().all()
    for candidate in rows:
        if _cached_success(candidate) is not None:
            return candidate
    return None


async def _serve(
    db: Session,
    provider: Any,
    server: VeeamBackupServer,
    dataset: str,
    method: Any,
    refresh: bool = False,
    **params: Any,
) -> dict[str, Any]:
    dataset_key = dataset
    if dataset == "job_stats_daily":
        days = params.get("days", 7)
        include_system = params.get("include_system", False)
        dataset_key = f"job_stats_daily:{int(days)}:{'sys' if include_system else 'jobs'}"

    row = db.execute(
        select(VeeamSnapshot).where(
            VeeamSnapshot.server_id == server.id,
            VeeamSnapshot.dataset == dataset_key,
        )
    ).scalar_one_or_none()
    cached = _cached_success(row) if row is not None else None

    offline_name = _server_agent_offline(db, server)

    if refresh:
        payload = await method(**params)
        if payload.get("success", False):
            _upsert_snapshot(db, server.id, dataset_key, payload)
            db.commit()
            return payload
        if cached is None and dataset == "job_stats_daily":
            fallback = _fallback_daily_snapshot(db, server.id)
            if fallback is not None:
                cached = _cached_success(fallback)
                row = fallback
        if cached is not None:
            return _stale_payload(cached, row, offline_name)
        # No good cache to fall back to: surface the live failure. Failed
        # payloads are never persisted, so a broken server keeps reporting its
        # real error instead of a phantom snapshot.
        return _offline_payload(payload, offline_name)

    if cached is not None and _snapshot_age(row) < SNAPSHOT_TTL_SECONDS:
        return cached

    payload = await method(**params)
    if payload.get("success", False):
        _upsert_snapshot(db, server.id, dataset_key, payload)
        db.commit()
        return payload
    if cached is None and dataset == "job_stats_daily":
        fallback = _fallback_daily_snapshot(db, server.id)
        if fallback is not None:
            cached = _cached_success(fallback)
            row = fallback
    if cached is not None:
        return _stale_payload(cached, row, offline_name)
    return _offline_payload(payload, offline_name)


@router.get("/overview")
async def get_overview(
    refresh: bool = Query(False),
    server_id: int | None = Query(None, description="Veeam server config id"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    server = _resolve_server(db, server_id)
    if server is None:
        return _failed("overview", _NO_SERVER)
    try:
        provider = build_server_provider(db, server)
        return await _serve(db, provider, server, "summary", provider.get_summary, refresh)
    except Exception as exc:
        return _failed("overview", str(exc))


@router.get("/health")
async def get_health(
    server_id: int | None = Query(None, description="Veeam server config id"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    server = _resolve_server(db, server_id)
    if server is None:
        return _failed("health", _NO_SERVER)
    try:
        provider = build_server_provider(db, server)
        return await provider.get_health()
    except Exception as exc:
        return _failed("health", str(exc))


@router.get("/test")
async def test_connection(
    server_id: int | None = Query(None, description="Veeam server config id"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    server = _resolve_server(db, server_id)
    if server is None:
        return _failed("test", _NO_SERVER)
    try:
        provider = build_server_provider(db, server)
        return await provider.test_connection()
    except Exception as exc:
        return _failed("test", str(exc))


@router.get("/jobs")
async def list_jobs(
    refresh: bool = Query(False),
    server_id: int | None = Query(None, description="Veeam server config id"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    server = _resolve_server(db, server_id)
    if server is None:
        return _failed("jobs", _NO_SERVER)
    try:
        provider = build_server_provider(db, server)
        return await _serve(db, provider, server, "jobs", provider.get_jobs, refresh)
    except Exception as exc:
        return _failed("jobs", str(exc))


@router.get("/jobs/stats")
async def get_job_stats(
    refresh: bool = Query(False),
    server_id: int | None = Query(None, description="Veeam server config id"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    server = _resolve_server(db, server_id)
    if server is None:
        return _failed("job_stats", _NO_SERVER)
    try:
        provider = build_server_provider(db, server)
        return await _serve(db, provider, server, "job_stats", provider.get_job_stats, refresh)
    except Exception as exc:
        return _failed("job_stats", str(exc))


@router.get("/jobs/stats/daily")
async def get_job_stats_daily(
    days: int = Query(default=7, ge=1, le=90),
    include_system: bool = Query(False, description="Include Veeam system/internal jobs"),
    refresh: bool = Query(False),
    server_id: int | None = Query(None, description="Veeam server config id"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    server = _resolve_server(db, server_id)
    if server is None:
        return _failed("job_stats_daily", _NO_SERVER)
    try:
        provider = build_server_provider(db, server)
        return await _serve(
            db, provider, server, "job_stats_daily",
            provider.get_job_stats_daily, refresh, days=days, include_system=include_system,
        )
    except Exception as exc:
        return _failed("job_stats_daily", str(exc))


def _classify_host(server: VeeamBackupServer, payload: Any, days: int) -> dict[str, Any]:
    """Summarise one host's backup outcome over the last ``days`` days.

    A host "passes" when every job that ran in the window succeeded, "fails"
    when at least one job failed and "warns" when a job only produced warnings.
    Failure reasons come from the ``runs`` the agent relay attaches to each
    daily cell; direct-DB servers only expose counts, so their reasons are
    empty.
    """
    summary: dict[str, Any] = {
        "server_id": server.id,
        "name": server.name,
        "enabled": bool(server.enabled),
        "days": days,
        "status": "no_data",
        "jobs_total": 0,
        "jobs_failed": 0,
        "jobs_warning": 0,
        "failures": [],
        "last_run": None,
        "error": None,
    }

    if not isinstance(payload, dict) or not payload.get("success"):
        error = payload.get("error") if isinstance(payload, dict) else None
        summary["status"] = "error" if error else "no_data"
        summary["error"] = error
        return summary

    jobs = payload.get("jobs") or []
    dates = [d for d in (payload.get("dates") or []) if d]
    window = set(dates[-days:]) if dates else set()
    summary["jobs_total"] = len(jobs)

    has_activity = False
    failed_jobs = 0
    warning_jobs = 0
    failures: list[dict[str, Any]] = []
    last_run: str | None = None

    for job in jobs:
        job_failed = False
        job_warning = False
        for day, cell in (job.get("daily") or {}).items():
            if window and day not in window:
                continue
            has_activity = True
            if int(cell.get("failed_count") or 0) > 0:
                job_failed = True
            elif int(cell.get("warning_count") or 0) > 0:
                job_warning = True
            for run in cell.get("runs") or []:
                when = run.get("end_time") or run.get("creation_time")
                if when and (last_run is None or str(when) > last_run):
                    last_run = str(when)
                if str(run.get("result")) == "Failed":
                    reason = str(run.get("reason") or "").strip() or None
                    failures.append({
                        "job_name": job.get("job_name"),
                        "date": day,
                        "reason": reason,
                    })
        if job_failed:
            failed_jobs += 1
        elif job_warning:
            warning_jobs += 1

    seen: set[tuple[Any, Any, Any]] = set()
    deduped: list[dict[str, Any]] = []
    for failure in failures:
        key = (failure["job_name"], failure["date"], failure["reason"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(failure)

    summary["jobs_failed"] = failed_jobs
    summary["jobs_warning"] = warning_jobs
    summary["failures"] = deduped[:10]
    summary["last_run"] = last_run

    if not has_activity:
        summary["status"] = "no_data"
    elif failed_jobs > 0:
        summary["status"] = "failed"
    elif warning_jobs > 0:
        summary["status"] = "warning"
    else:
        summary["status"] = "passed"
    return summary


@router.get("/hosts/status")
async def hosts_status(
    days: int = Query(default=3, ge=1, le=30),
    refresh: bool = Query(False),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Per-host backup health for every Veeam-enabled remote target.

    Returns one entry per enabled server summarising whether the jobs that ran
    over the last ``days`` days passed, failed or warned, including failure
    reasons. Served from each server's snapshot cache when fresh, collected
    live otherwise.
    """
    servers = db.execute(
        select(VeeamBackupServer)
        .where(VeeamBackupServer.enabled.is_(True))
        .order_by(VeeamBackupServer.name)
    ).scalars().all()

    hosts: list[dict[str, Any]] = []
    for server in servers:
        try:
            provider = build_server_provider(db, server)
            payload = await _serve(
                db, provider, server, "job_stats_daily",
                provider.get_job_stats_daily, refresh,
                days=days, include_system=False,
            )
        except Exception as exc:  # pragma: no cover - defensive
            payload = {"success": False, "error": str(exc)}
        hosts.append(_classify_host(server, payload, days))

    return {"success": True, "days": days, "count": len(hosts), "hosts": hosts}


@router.get("/jobs/{job_id}")
async def get_job_detail(
    job_id: str,
    server_id: int | None = Query(None, description="Veeam server config id"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    server = _resolve_server(db, server_id)
    if server is None:
        return _failed("job_detail", _NO_SERVER)
    try:
        provider = build_server_provider(db, server)
        return await provider.get_job_detail(job_id)
    except Exception as exc:
        return _failed("job_detail", str(exc))


@router.post("/jobs/{job_id}/start")
async def start_job(
    job_id: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    server = _first_server(db)
    if server is None:
        return _failed("job_control", _NO_SERVER)
    try:
        provider = build_server_provider(db, server)
        return await provider.start_job(job_id)
    except Exception as exc:
        return _failed("job_control", str(exc))


@router.post("/jobs/{job_id}/stop")
async def stop_job(
    job_id: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    server = _first_server(db)
    if server is None:
        return _failed("job_control", _NO_SERVER)
    try:
        provider = build_server_provider(db, server)
        return await provider.stop_job(job_id)
    except Exception as exc:
        return _failed("job_control", str(exc))


@router.get("/sessions")
async def list_sessions(
    refresh: bool = Query(False),
    server_id: int | None = Query(None, description="Veeam server config id"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    server = _resolve_server(db, server_id)
    if server is None:
        return _failed("sessions", _NO_SERVER)
    try:
        provider = build_server_provider(db, server)
        return await _serve(db, provider, server, "sessions", provider.get_sessions, refresh)
    except Exception as exc:
        return _failed("sessions", str(exc))


@router.get("/sessions/stats")
async def get_session_stats(
    refresh: bool = Query(False),
    server_id: int | None = Query(None, description="Veeam server config id"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    server = _resolve_server(db, server_id)
    if server is None:
        return _failed("session_stats", _NO_SERVER)
    try:
        provider = build_server_provider(db, server)
        return await _serve(db, provider, server, "session_stats", provider.get_session_stats, refresh)
    except Exception as exc:
        return _failed("session_stats", str(exc))


@router.get("/repositories")
async def list_repositories(
    refresh: bool = Query(False),
    server_id: int | None = Query(None, description="Veeam server config id"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    server = _resolve_server(db, server_id)
    if server is None:
        return _failed("repositories", _NO_SERVER)
    try:
        provider = build_server_provider(db, server)
        return await _serve(db, provider, server, "repositories", provider.get_repositories, refresh)
    except Exception as exc:
        return _failed("repositories", str(exc))


@router.get("/servers")
async def list_managed_servers(
    server_id: int | None = Query(None, description="Veeam server config id"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    server = _resolve_server(db, server_id)
    if server is None:
        return _failed("servers", _NO_SERVER)
    try:
        provider = build_server_provider(db, server)
        return await provider.get_managed_servers()
    except Exception as exc:
        return _failed("servers", str(exc))


@router.get("/restore-points")
async def list_restore_points(
    vm_id: str | None = Query(None),
    server_id: int | None = Query(None, description="Veeam server config id"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    server = _resolve_server(db, server_id)
    if server is None:
        return _failed("restore_points", _NO_SERVER)
    try:
        provider = build_server_provider(db, server)
        return await provider.get_restore_points(vm_id)
    except Exception as exc:
        return _failed("restore_points", str(exc))


@router.get("/license")
async def get_license(
    refresh: bool = Query(False),
    server_id: int | None = Query(None, description="Veeam server config id"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    server = _resolve_server(db, server_id)
    if server is None:
        return _failed("license", _NO_SERVER)
    try:
        provider = build_server_provider(db, server)
        return await _serve(db, provider, server, "license", provider.get_license, refresh)
    except Exception as exc:
        return _failed("license", str(exc))


@router.get("/capacity-tier")
async def get_capacity_tier(
    refresh: bool = Query(False),
    server_id: int | None = Query(None, description="Veeam server config id"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    server = _resolve_server(db, server_id)
    if server is None:
        return _failed("capacity_tier", _NO_SERVER)
    try:
        provider = build_server_provider(db, server)
        return await _serve(db, provider, server, "capacity_tier", provider.get_capacity_tier, refresh)
    except Exception as exc:
        return _failed("capacity_tier", str(exc))


# ------------------------------------------------------------------ #
# Server Configuration CRUD                                          #
# ------------------------------------------------------------------ #


def _servers_with_data(db: Session) -> set[int]:
    """Server ids that have at least one successfully collected snapshot."""
    ids: set[int] = set()
    for server_id, payload in db.execute(
        select(VeeamSnapshot.server_id, VeeamSnapshot.payload)
    ).all():
        try:
            if json.loads(payload).get("success"):
                ids.add(server_id)
        except (ValueError, TypeError):
            continue
    return ids


@router.get("/servers/config", response_model=list[VeeamServerConfigResponse])
async def list_server_configs(db: Session = Depends(get_db)) -> list[VeeamBackupServer]:
    """List all Veeam server configurations."""
    servers = db.query(VeeamBackupServer).order_by(VeeamBackupServer.id).all()
    with_data = _servers_with_data(db)
    for server in servers:
        server.has_data = server.id in with_data
    return servers


@router.get("/servers/config/{server_id}", response_model=VeeamServerConfigResponse)
async def get_server_config(server_id: int, db: Session = Depends(get_db)) -> VeeamBackupServer:
    """Get a specific Veeam server configuration."""
    server = db.query(VeeamBackupServer).filter(VeeamBackupServer.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return server


@router.get("/servers/config/{server_id}/diagnostics")
async def server_diagnostics(server_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Run staged diagnostics for a Veeam server's data bridge.

    Never raises: each stage (agent probe, DB client detection, live SELECT 1)
    is captured and surfaced with derived recommendations.
    """
    server = db.query(VeeamBackupServer).filter(VeeamBackupServer.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    from app.plugins.installed.official_veeam.diagnostics import run_server_diagnostics

    return await run_server_diagnostics(db, server)


@router.post("/servers/config", response_model=VeeamServerConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_server_config(
    config: VeeamServerConfigCreate,
    db: Session = Depends(get_db),
) -> VeeamBackupServer:
    """Create a new Veeam server configuration."""
    # Check for duplicate name
    existing = db.query(VeeamBackupServer).filter(VeeamBackupServer.name == config.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="A server with this name already exists")

    # Encrypt passwords
    cipher = CredentialCipher(get_settings().missioncontrol_secret_key)
    encrypted_password = cipher.encrypt(config.password) if config.password else None
    encrypted_ssh_password = cipher.encrypt(config.ssh_password) if config.ssh_password else None

    server = VeeamBackupServer(
        name=config.name,
        url=config.url,
        username=config.username,
        encrypted_password=encrypted_password,
        verify_ssl=config.verify_ssl,
        timeout=config.timeout,
        enabled=config.enabled,
        ssh_host=config.ssh_host,
        ssh_port=config.ssh_port,
        ssh_username=config.ssh_username,
        encrypted_ssh_password=encrypted_ssh_password,
        data_source=config.data_source,
        db_type=config.db_type,
        column_case=config.column_case,
    )
    db.add(server)
    db.commit()
    db.refresh(server)
    logger.info("Veeam server config created: %s", server.name)
    return server


@router.put("/servers/config/{server_id}", response_model=VeeamServerConfigResponse)
async def update_server_config(
    server_id: int,
    config: VeeamServerConfigUpdate,
    db: Session = Depends(get_db),
) -> VeeamBackupServer:
    """Update a Veeam server configuration."""
    server = db.query(VeeamBackupServer).filter(VeeamBackupServer.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    # Check for duplicate name if changing
    if config.name and config.name != server.name:
        existing = db.query(VeeamBackupServer).filter(VeeamBackupServer.name == config.name).first()
        if existing:
            raise HTTPException(status_code=409, detail="A server with this name already exists")

    # Update fields
    update_data = config.model_dump(exclude_unset=True)
    cipher = CredentialCipher(get_settings().missioncontrol_secret_key)

    for field, value in update_data.items():
        if field == "password" and value is not None:
            server.encrypted_password = cipher.encrypt(value)
        elif field == "ssh_password" and value is not None:
            server.encrypted_ssh_password = cipher.encrypt(value)
        elif field != "password" and field != "ssh_password":
            setattr(server, field, value)

    db.commit()
    db.refresh(server)
    logger.info("Veeam server config updated: %s", server.name)
    return server


@router.delete("/servers/config/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_server_config(server_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a Veeam server configuration."""
    server = db.query(VeeamBackupServer).filter(VeeamBackupServer.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    db.delete(server)
    db.commit()
    logger.info("Veeam server config deleted: %s", server.name)


@router.post("/servers/config/test")
async def test_server_connection(config: VeeamServerConfigCreate) -> dict[str, Any]:
    """Test connection to a Veeam server without saving."""
    from app.plugins.installed.official_veeam.api import VeeamApiClient

    cipher = CredentialCipher(get_settings().missioncontrol_secret_key)
    encrypted_password = cipher.encrypt(config.password) if config.password else None
    encrypted_ssh_password = cipher.encrypt(config.ssh_password) if config.ssh_password else None

    # Build temporary server object for testing
    temp_server = VeeamBackupServer(
        id=0,
        name=config.name,
        url=config.url,
        username=config.username,
        encrypted_password=encrypted_password,
        verify_ssl=config.verify_ssl,
        timeout=config.timeout,
        enabled=config.enabled,
        ssh_host=config.ssh_host,
        ssh_port=config.ssh_port,
        ssh_username=config.ssh_username,
        encrypted_ssh_password=encrypted_ssh_password,
        data_source=config.data_source,
        db_type=config.db_type,
        column_case=config.column_case,
    )

    try:
        client = VeeamApiClient(
            base_url=temp_server.url,
            username=temp_server.username,
            password=config.password or "",
            verify_ssl=temp_server.verify_ssl,
            timeout=temp_server.timeout,
            ssh_host=temp_server.ssh_host,
            ssh_port=temp_server.ssh_port,
            ssh_username=temp_server.ssh_username,
            ssh_password=config.ssh_password or "",
            data_source=temp_server.data_source,
            db_type=temp_server.db_type,
            column_case=temp_server.column_case,
        )
        result = await client.test_connection()
        return {"connected": result.get("connected", False), "error": result.get("error")}
    except Exception as exc:
        return {"connected": False, "error": str(exc)}
