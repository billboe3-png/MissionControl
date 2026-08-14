"""
Veeam Plugin REST API Routes

FastAPI router exposed by the Veeam plugin.
All routes are prefixed with /api/v1/plugins/veeam.
Live-data routes delegate to a VeeamServerProvider built from the first
enabled server row, preserving the legacy provider response shapes.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.plugins.installed.official_veeam.cache import cache_manager
from app.plugins.installed.official_veeam.diagnostics import run_connection_diagnostics
from app.plugins.installed.official_veeam.models import VeeamBackupServer
from app.plugins.installed.official_veeam.provider import build_server_provider

logger = logging.getLogger("plugin.veeam.routes")

router = APIRouter(prefix="/api/v1/plugins/veeam", tags=["veeam-plugin"])

_NO_SERVER = "No Veeam server configured"


def _first_server(db: Session) -> VeeamBackupServer | None:
    return (
        db.query(VeeamBackupServer)
        .filter(VeeamBackupServer.enabled.is_(True))
        .order_by(VeeamBackupServer.id)
        .first()
    )


def _provider_for(db: Session, server: VeeamBackupServer) -> Any:
    return build_server_provider(db, server)


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


@router.get("/overview")
async def get_overview(db: Session = Depends(get_db)) -> dict[str, Any]:
    server = _first_server(db)
    if server is None:
        return _failed("overview", _NO_SERVER)
    try:
        return await _provider_for(db, server).get_summary()
    except Exception as exc:
        return _failed("overview", str(exc))


@router.get("/health")
async def get_health(db: Session = Depends(get_db)) -> dict[str, Any]:
    server = _first_server(db)
    if server is None:
        return _failed("health", _NO_SERVER)
    try:
        return await _provider_for(db, server).get_health()
    except Exception as exc:
        return _failed("health", str(exc))


@router.get("/test")
async def test_connection(db: Session = Depends(get_db)) -> dict[str, Any]:
    server = _first_server(db)
    if server is None:
        return _failed("test", _NO_SERVER)
    try:
        provider = _provider_for(db, server)
        diag = await run_connection_diagnostics(provider)
    except Exception as exc:
        return _failed("test", str(exc))
    version = (
        (diag.get("rest") or {}).get("version")
        or (diag.get("ssh") or {}).get("version")
        or server.version
    )
    return {
        "connected": diag.get("success", False),
        "version": version,
        "name": server.name,
        "server_id": server.id,
        "error": diag.get("error"),
    }


@router.get("/jobs")
async def list_jobs(db: Session = Depends(get_db)) -> dict[str, Any]:
    server = _first_server(db)
    if server is None:
        return _failed("jobs", _NO_SERVER)
    try:
        return await _provider_for(db, server).get_jobs()
    except Exception as exc:
        return _failed("jobs", str(exc))


@router.get("/jobs/stats")
async def get_job_stats(db: Session = Depends(get_db)) -> dict[str, Any]:
    server = _first_server(db)
    if server is None:
        return _failed("job_stats", _NO_SERVER)
    try:
        return await _provider_for(db, server).get_job_stats()
    except Exception as exc:
        return _failed("job_stats", str(exc))


@router.get("/jobs/stats/daily")
async def get_job_stats_daily(
    days: int = 7,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    server = _first_server(db)
    if server is None:
        return _failed("job_stats_daily", _NO_SERVER)
    try:
        return await _provider_for(db, server).get_job_stats_daily(days)
    except Exception as exc:
        return _failed("job_stats_daily", str(exc))


@router.get("/jobs/{job_id}")
async def get_job_detail(
    job_id: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    server = _first_server(db)
    if server is None:
        return _failed("job_detail", _NO_SERVER)
    try:
        return await _provider_for(db, server).get_job_detail(job_id)
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
        return await _provider_for(db, server).start_job(job_id)
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
        return await _provider_for(db, server).stop_job(job_id)
    except Exception as exc:
        return _failed("job_control", str(exc))


@router.get("/sessions")
async def list_sessions(db: Session = Depends(get_db)) -> dict[str, Any]:
    server = _first_server(db)
    if server is None:
        return _failed("sessions", _NO_SERVER)
    try:
        return await _provider_for(db, server).get_sessions()
    except Exception as exc:
        return _failed("sessions", str(exc))


@router.get("/sessions/stats")
async def get_session_stats(db: Session = Depends(get_db)) -> dict[str, Any]:
    server = _first_server(db)
    if server is None:
        return _failed("session_stats", _NO_SERVER)
    try:
        return await _provider_for(db, server).get_session_stats()
    except Exception as exc:
        return _failed("session_stats", str(exc))


@router.get("/repositories")
async def list_repositories(db: Session = Depends(get_db)) -> dict[str, Any]:
    server = _first_server(db)
    if server is None:
        return _failed("repositories", _NO_SERVER)
    try:
        return await _provider_for(db, server).get_repositories()
    except Exception as exc:
        return _failed("repositories", str(exc))


@router.get("/servers")
async def list_servers(db: Session = Depends(get_db)) -> dict[str, Any]:
    server = _first_server(db)
    if server is None:
        return _failed("servers", _NO_SERVER)
    try:
        return await _provider_for(db, server).get_managed_servers()
    except Exception as exc:
        return _failed("servers", str(exc))


@router.get("/restore-points")
async def list_restore_points(
    vm_id: str | None = None,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    server = _first_server(db)
    if server is None:
        return _failed("restore_points", _NO_SERVER)
    try:
        return await _provider_for(db, server).get_restore_points(vm_id)
    except Exception as exc:
        return _failed("restore_points", str(exc))


@router.get("/license")
async def get_license(db: Session = Depends(get_db)) -> dict[str, Any]:
    server = _first_server(db)
    if server is None:
        return _failed("license", _NO_SERVER)
    try:
        return await _provider_for(db, server).get_license()
    except Exception as exc:
        return _failed("license", str(exc))


@router.get("/capacity-tier")
async def get_capacity_tier(db: Session = Depends(get_db)) -> dict[str, Any]:
    server = _first_server(db)
    if server is None:
        return _failed("capacity_tier", _NO_SERVER)
    try:
        return await _provider_for(db, server).get_capacity_tier()
    except Exception as exc:
        return _failed("capacity_tier", str(exc))


@router.get("/licenses")
def list_licenses(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """List cached license information."""
    return cache_manager.get_license(db)


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Aggregated Veeam backup summary from cache."""
    return cache_manager.get_summary(db)


@router.get("/repo-health")
def get_repo_health(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Repository health data with capacity percentages."""
    return cache_manager.get_repo_health(db)


@router.get("/jobs-by-status")
def get_jobs_by_status(db: Session = Depends(get_db)) -> dict[str, int]:
    """Job counts grouped by status."""
    return cache_manager.get_jobs_by_status(db)


@router.get("/jobs-by-type")
def get_jobs_by_type(db: Session = Depends(get_db)) -> dict[str, int]:
    """Job counts grouped by type."""
    return cache_manager.get_jobs_by_type(db)
