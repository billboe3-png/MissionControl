"""
Marketplace API Router

Endpoints:
- GET  /marketplace/plugins           - List all plugins from all repositories
- GET  /marketplace/search            - Search plugins by query
- GET  /marketplace/plugin/{plugin_id} - Get plugin details
- POST /marketplace/install           - Install a plugin
- GET  /marketplace/updates           - List available updates
- POST /marketplace/update            - Update a plugin
- POST /marketplace/rollback          - Rollback a plugin
- GET  /marketplace/health            - Marketplace health dashboard
- GET  /marketplace/installed         - List installed plugins
- POST /marketplace/enable            - Enable a plugin
- POST /marketplace/disable           - Disable a plugin
- POST /marketplace/remove            - Remove a plugin
- GET  /marketplace/repositories      - List repositories
- POST /marketplace/repositories      - Add/update a repository
- DELETE /marketplace/repositories/{name} - Remove a repository

Sprint 3.10.4 - Plugin Marketplace.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth_dependency import get_current_user
from app.db import get_db
from app.marketplace.compatibility import compatibility_engine
from app.marketplace.installer import plugin_installer
from app.marketplace.registry import marketplace_registry
from app.marketplace.repository import Repository, TrustLevel, repository_manager
from app.marketplace.updater import plugin_updater
from app.models.db.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/marketplace", tags=["Marketplace"])


# ── Request/Response Models ──────────────────────────────────────────────

class InstallRequest(BaseModel):
    plugin_id: str
    version: str = ""
    repo_name: str = ""


class UpdateRequest(BaseModel):
    plugin_id: str


class RepositoryRequest(BaseModel):
    name: str
    url: str
    priority: int = 100
    enabled: bool = True
    trust_level: str = "community"


class EnableDisableRequest(BaseModel):
    plugin_id: str


# ── Plugin Discovery ─────────────────────────────────────────────────────

@router.get("/plugins")
async def list_plugins(
    repo: str = "",
    status: str = "",
    _user: User = Depends(get_current_user),
    _db: Session = Depends(get_db),
) -> dict[str, Any]:
    """List plugins from repositories or installed state."""
    plugins = marketplace_registry.get_all()

    if status:
        plugins = [p for p in plugins if p.status == status]

    return {
        "plugins": [p.to_dict() for p in plugins],
        "total": len(plugins),
    }


@router.get("/search")
async def search_plugins(
    q: str = "",
    _user: User = Depends(get_current_user),
    _db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Search installed plugins by name or ID."""
    plugins = marketplace_registry.get_all()
    if q:
        q_lower = q.lower()
        plugins = [p for p in plugins if q_lower in p.name.lower() or q_lower in p.plugin_id.lower()]

    return {
        "query": q,
        "results": [p.to_dict() for p in plugins],
        "total": len(plugins),
    }


@router.get("/plugin/{plugin_id}")
async def get_plugin_details(
    plugin_id: str,
    _user: User = Depends(get_current_user),
    _db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Get detailed plugin information."""
    plugin = marketplace_registry.get(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin {plugin_id} not found")

    result = plugin.to_dict()
    # Add compatibility info
    compat = compatibility_engine.check_all({"sdk_version": "3.10"})
    result["compatibility"] = compat
    return result


# ── Installation ─────────────────────────────────────────────────────────

@router.post("/install")
async def install_plugin(
    req: InstallRequest,
    _user: User = Depends(get_current_user),
    _db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Install a plugin (triggers download + verification + extract + register)."""
    meta = {
        "id": req.plugin_id,
        "name": req.plugin_id,
        "version": req.version or "1.0.0",
        "sdk_version": "3.10",
    }
    # In production, download from repository first
    result = plugin_installer.install(meta, "", req.repo_name)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/enable")
async def enable_plugin(
    req: EnableDisableRequest,
    _user: User = Depends(get_current_user),
    _db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Enable a plugin."""
    ok = plugin_installer.enable(req.plugin_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return {"success": True, "plugin_id": req.plugin_id, "enabled": True}


@router.post("/disable")
async def disable_plugin(
    req: EnableDisableRequest,
    _user: User = Depends(get_current_user),
    _db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Disable a plugin."""
    ok = plugin_installer.disable(req.plugin_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return {"success": True, "plugin_id": req.plugin_id, "enabled": False}


@router.post("/remove")
async def remove_plugin(
    req: EnableDisableRequest,
    _user: User = Depends(get_current_user),
    _db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Remove an installed plugin."""
    result = plugin_installer.uninstall(req.plugin_id)
    return result


# ── Updates ──────────────────────────────────────────────────────────────

@router.get("/updates")
async def check_updates(
    _user: User = Depends(get_current_user),
    _db: Session = Depends(get_db),
) -> dict[str, Any]:
    """List available plugin updates."""
    updates = plugin_updater.check_updates()
    return {"updates": updates, "total": len(updates)}


@router.post("/update")
async def update_plugin(
    req: UpdateRequest,
    _user: User = Depends(get_current_user),
    _db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Update a single plugin."""
    result = plugin_updater.update_plugin(req.plugin_id, "")
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/rollback")
async def rollback_plugin(
    req: UpdateRequest,
    _user: User = Depends(get_current_user),
    _db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Rollback a plugin to its previous version."""
    result = plugin_updater.rollback(req.plugin_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ── Health Dashboard ─────────────────────────────────────────────────────

@router.get("/health")
async def marketplace_health(
    _user: User = Depends(get_current_user),
    _db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Marketplace health dashboard."""
    return marketplace_registry.summary()


@router.get("/installed")
async def list_installed(
    _user: User = Depends(get_current_user),
    _db: Session = Depends(get_db),
) -> dict[str, Any]:
    """List installed plugins with full details."""
    plugins = marketplace_registry.get_all()
    return {
        "plugins": [p.to_dict() for p in plugins],
        "total": len(plugins),
    }


# ── Repositories ─────────────────────────────────────────────────────────

@router.get("/repositories")
async def list_repositories(
    _user: User = Depends(get_current_user),
    _db: Session = Depends(get_db),
) -> dict[str, Any]:
    """List all configured repositories."""
    return {"repositories": repository_manager.to_dicts()}


@router.post("/repositories")
async def add_repository(
    req: RepositoryRequest,
    _user: User = Depends(get_current_user),
    _db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Add or update a repository."""
    repo = Repository(
        name=req.name,
        url=req.url,
        priority=req.priority,
        enabled=req.enabled,
        trust_level=TrustLevel(req.trust_level),
    )
    repository_manager.add(repo)
    return {"success": True, "repository": repo.to_dict()}


@router.delete("/repositories/{name}")
async def remove_repository(
    name: str,
    _user: User = Depends(get_current_user),
    _db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Remove a repository."""
    ok = repository_manager.remove(name)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Repository {name} not found")
    return {"success": True, "removed": name}
