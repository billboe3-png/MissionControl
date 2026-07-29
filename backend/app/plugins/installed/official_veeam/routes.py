"""
Veeam Plugin REST API Routes

FastAPI router exposed by the Veeam plugin.
All routes are prefixed with /api/v1/plugins/veeam.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.plugins.installed.official_veeam.cache import cache_manager

logger = logging.getLogger("plugin.veeam.routes")

router = APIRouter(prefix="/api/v1/plugins/veeam", tags=["veeam-plugin"])


@router.get("/servers")
def list_servers(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """List all registered Veeam backup servers."""
    return cache_manager.get_servers(db)


@router.get("/repositories")
def list_repositories(
    server_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """List cached backup repositories."""
    return cache_manager.get_repositories(db, server_id=server_id)


@router.get("/jobs")
def list_jobs(
    server_id: int | None = None,
    job_type: str | None = None,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """List cached backup jobs."""
    return cache_manager.get_jobs(db, server_id=server_id, job_type=job_type)


@router.get("/restore-points")
def list_restore_points(
    server_id: int | None = None,
    vm_name: str | None = None,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """List cached restore points."""
    return cache_manager.get_restore_points(
        db, server_id=server_id, vm_name=vm_name,
    )


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


@router.get("/health")
def get_health(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Plugin health endpoint for diagnostics."""
    servers = cache_manager.get_servers(db)
    repo_count = len(cache_manager.get_repositories(db))
    job_count = len(cache_manager.get_jobs(db))
    last_sync = cache_manager.get_last_sync(db)

    errors = [
        s["last_error"] for s in servers
        if s.get("last_error")
    ]
    healthy_count = sum(1 for s in servers if s["status"] == "healthy")

    if not servers:
        status = "no_servers"
    elif healthy_count == len(servers):
        status = "healthy"
    elif healthy_count > 0:
        status = "degraded"
    else:
        status = "error"

    return {
        "status": status,
        "servers": len(servers),
        "healthy_servers": healthy_count,
        "repositories": repo_count,
        "jobs": job_count,
        "last_sync": last_sync,
        "errors": errors,
    }
