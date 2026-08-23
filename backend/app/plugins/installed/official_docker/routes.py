"""
Docker Plugin REST API Routes

FastAPI router exposed by the Docker plugin.
All routes are prefixed with /api/v1/plugins/docker.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.plugins.installed.official_docker.cache import cache_manager

logger = logging.getLogger("plugin.docker.routes")

router = APIRouter(prefix="/api/v1/plugins/docker", tags=["docker-plugin"])


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Aggregated Docker host summary from cache."""
    return cache_manager.get_summary(db)


@router.get("/hosts")
def list_hosts(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """List all registered Docker hosts."""
    return cache_manager.get_hosts(db)


@router.get("/containers")
def list_containers(
    host_id: int | None = None,
    state: str | None = None,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """List cached containers."""
    return cache_manager.get_containers(db, host_id=host_id, state=state)


@router.get("/images")
def list_images(
    host_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """List cached images."""
    return cache_manager.get_images(db, host_id=host_id)


@router.get("/volumes")
def list_volumes(
    host_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """List cached volumes."""
    return cache_manager.get_volumes(db, host_id=host_id)


@router.get("/networks")
def list_networks(
    host_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """List cached networks."""
    return cache_manager.get_networks(db, host_id=host_id)


@router.get("/compose")
def list_compose(
    host_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """List cached Compose stacks."""
    return cache_manager.get_compose(db, host_id=host_id)


@router.get("/resource-usage")
def get_resource_usage(
    host_id: int | None = None,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Aggregated resource usage from running containers."""
    return cache_manager.get_resource_usage(db, host_id=host_id)


@router.get("/container-health")
def get_container_health(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Container health breakdown by state and health status."""
    return cache_manager.get_container_health(db)


@router.get("/health")
def get_health(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Plugin health endpoint for diagnostics."""
    hosts = cache_manager.get_hosts(db)
    container_count = len(cache_manager.get_containers(db))
    image_count = len(cache_manager.get_images(db))
    last_sync = cache_manager.get_last_sync(db)

    errors = [
        h["last_error"] for h in hosts
        if h.get("last_error")
    ]
    healthy_count = sum(1 for h in hosts if h.get("online"))

    if not hosts:
        status = "no_hosts"
    elif healthy_count == len(hosts):
        status = "healthy"
    elif healthy_count > 0:
        status = "degraded"
    else:
        status = "error"

    return {
        "status": status,
        "hosts": len(hosts),
        "healthy_hosts": healthy_count,
        "containers": container_count,
        "images": image_count,
        "last_sync": last_sync,
        "errors": errors,
    }
