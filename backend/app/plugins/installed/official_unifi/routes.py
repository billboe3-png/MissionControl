"""
UniFi Plugin REST API Routes

FastAPI router exposed by the UniFi plugin.
All routes are prefixed with /api/v1/plugins/unifi.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.plugins.installed.official_unifi.cache import cache_manager

logger = logging.getLogger("plugin.unifi.routes")

router = APIRouter(prefix="/api/v1/plugins/unifi", tags=["unifi-plugin"])


@router.get("/controllers")
def list_controllers(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """List all registered UniFi controllers."""
    return cache_manager.get_controllers(db)


@router.get("/sites")
def list_sites(
    controller_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """List cached UniFi sites."""
    return cache_manager.get_sites(db, controller_id=controller_id)


@router.get("/devices")
def list_devices(
    controller_id: int | None = None,
    site_id: str | None = None,
    device_type: str | None = None,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """List cached UniFi devices."""
    return cache_manager.get_devices(
        db, controller_id=controller_id, site_id=site_id, device_type=device_type,
    )


@router.get("/clients")
def list_clients(
    controller_id: int | None = None,
    site_id: str | None = None,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """List cached UniFi clients."""
    return cache_manager.get_clients(db, controller_id=controller_id, site_id=site_id)


@router.get("/alerts")
def list_alerts(
    controller_id: int | None = None,
    site_id: str | None = None,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """List cached UniFi alerts."""
    return cache_manager.get_alerts(db, controller_id=controller_id, site_id=site_id)


@router.get("/wireless")
def list_wireless(
    controller_id: int | None = None,
    site_id: str | None = None,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """List cached wireless networks."""
    return cache_manager.get_wireless(db, controller_id=controller_id, site_id=site_id)


@router.get("/switches")
def list_switches(
    controller_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """List cached UniFi switches."""
    return cache_manager.get_switches(db, controller_id=controller_id)


@router.get("/gateways")
def list_gateways(
    controller_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """List cached UniFi gateways."""
    return cache_manager.get_gateways(db, controller_id=controller_id)


@router.get("/access-points")
def list_access_points(
    controller_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """List cached UniFi access points."""
    return cache_manager.get_access_points(db, controller_id=controller_id)


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Aggregated UniFi network summary from cache."""
    return cache_manager.get_summary(db)


@router.get("/devices-by-status")
def get_devices_by_status(db: Session = Depends(get_db)) -> dict[str, int]:
    """Device counts grouped by status."""
    return cache_manager.get_devices_by_status(db)


@router.get("/devices-by-type")
def get_devices_by_type(db: Session = Depends(get_db)) -> dict[str, int]:
    """Device counts grouped by type."""
    return cache_manager.get_devices_by_type(db)


@router.get("/health")
def get_health(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Plugin health endpoint for diagnostics."""
    controllers = cache_manager.get_controllers(db)
    device_count = len(cache_manager.get_devices(db))
    client_count = len(cache_manager.get_clients(db))
    last_sync = cache_manager.get_last_sync(db)

    errors = [
        c["last_error"] for c in controllers
        if c.get("last_error")
    ]
    healthy_count = sum(1 for c in controllers if c["status"] == "healthy")

    if not controllers:
        status = "no_controllers"
    elif healthy_count == len(controllers):
        status = "healthy"
    elif healthy_count > 0:
        status = "degraded"
    else:
        status = "error"

    return {
        "status": status,
        "controllers": len(controllers),
        "healthy_controllers": healthy_count,
        "devices": device_count,
        "clients": client_count,
        "last_sync": last_sync,
        "errors": errors,
    }
