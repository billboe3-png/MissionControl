"""
Mission Control Plugin Router

REST API for plugin management, lifecycle control, and marketplace.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.plugin import (
    PluginActionResponse,
    PluginCreate,
    PluginListResponse,
    PluginResponse,
    PluginUpdate,
)
from app.services.plugin_service import plugin_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/plugins", tags=["plugins"])


# ------------------------------------------------------------------ #
# List / Get                                                          #
# ------------------------------------------------------------------ #


@router.get("", response_model=PluginListResponse)
async def list_plugins(
    execution_target: str | None = Query(None, description="Filter by execution_target"),
    category: str | None = Query(None, description="Filter by category"),
    enabled_only: bool = Query(False, description="Only enabled plugins"),
    db: Session = Depends(get_db),
) -> PluginListResponse:
    plugins = plugin_service.list_plugins(
        db,
        execution_target=execution_target,
        category=category,
        enabled_only=enabled_only,
    )
    return PluginListResponse(
        count=len(plugins),
        items=[plugin_service.to_response(p) for p in plugins],
    )


@router.get("/stats")
async def get_plugin_stats(db: Session = Depends(get_db)) -> dict:
    return plugin_service.get_stats(db)


@router.get("/{plugin_id}", response_model=PluginResponse)
async def get_plugin(
    plugin_id: int,
    db: Session = Depends(get_db),
) -> PluginResponse:
    plugin = plugin_service.get_plugin(db, plugin_id)
    if plugin is None:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return plugin_service.to_response(plugin)


@router.get("/by-slug/{slug}", response_model=PluginResponse)
async def get_plugin_by_slug(
    slug: str,
    db: Session = Depends(get_db),
) -> PluginResponse:
    plugin = plugin_service.get_plugin_by_slug(db, slug)
    if plugin is None:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return plugin_service.to_response(plugin)


# ------------------------------------------------------------------ #
# Create / Update / Delete                                            #
# ------------------------------------------------------------------ #


@router.post(
    "",
    response_model=PluginResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_plugin(
    data: PluginCreate,
    db: Session = Depends(get_db),
) -> PluginResponse:
    try:
        plugin = plugin_service.register_plugin(db, data)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return plugin_service.to_response(plugin)


@router.put("/{plugin_id}", response_model=PluginResponse)
async def update_plugin(
    plugin_id: int,
    data: PluginUpdate,
    db: Session = Depends(get_db),
) -> PluginResponse:
    plugin = plugin_service.update_plugin(db, plugin_id, data)
    if plugin is None:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return plugin_service.to_response(plugin)


@router.delete("/{plugin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unregister_plugin(
    plugin_id: int,
    db: Session = Depends(get_db),
) -> None:
    if not plugin_service.unregister_plugin(db, plugin_id):
        raise HTTPException(status_code=404, detail="Plugin not found")


# ------------------------------------------------------------------ #
# Lifecycle                                                           #
# ------------------------------------------------------------------ #


@router.post("/{plugin_id}/enable", response_model=PluginResponse)
async def enable_plugin(
    plugin_id: int,
    db: Session = Depends(get_db),
) -> PluginResponse:
    plugin = plugin_service.enable_plugin(db, plugin_id)
    if plugin is None:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return plugin_service.to_response(plugin)


@router.post("/{plugin_id}/disable", response_model=PluginResponse)
async def disable_plugin(
    plugin_id: int,
    db: Session = Depends(get_db),
) -> PluginResponse:
    plugin = plugin_service.disable_plugin(db, plugin_id)
    if plugin is None:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return plugin_service.to_response(plugin)


@router.post("/{plugin_id}/start", response_model=PluginActionResponse)
async def start_plugin(
    plugin_id: int,
    db: Session = Depends(get_db),
) -> PluginActionResponse:
    return plugin_service.start_plugin(db, plugin_id)


@router.post("/{plugin_id}/stop", response_model=PluginActionResponse)
async def stop_plugin(
    plugin_id: int,
    db: Session = Depends(get_db),
) -> PluginActionResponse:
    return plugin_service.stop_plugin(db, plugin_id)


# ------------------------------------------------------------------ #
# Marketplace                                                         #
# ------------------------------------------------------------------ #


@router.get("/marketplace/catalog")
async def get_marketplace_catalog(
    execution_target: str | None = Query(None),
    category: str | None = Query(None),
    db: Session = Depends(get_db),
) -> dict:
    from app.services.plugin_marketplace_service import plugin_marketplace_service

    catalog = plugin_marketplace_service.list_catalog(
        execution_target=execution_target,
        category=category,
    )
    installed = {p.slug for p in plugin_service.list_plugins(db=db)}
    enriched = plugin_marketplace_service.merge_with_installed(catalog, installed)
    return {"count": len(enriched), "items": enriched}


@router.get("/marketplace/categories")
async def get_marketplace_categories() -> dict:
    from app.services.plugin_marketplace_service import plugin_marketplace_service

    return {"categories": plugin_marketplace_service.get_categories()}


@router.get("/marketplace/{slug}")
async def get_marketplace_plugin(
    slug: str,
) -> dict:
    from app.services.plugin_marketplace_service import plugin_marketplace_service

    info = plugin_marketplace_service.get_plugin_info(slug)
    if info is None:
        raise HTTPException(status_code=404, detail="Plugin not found in marketplace")
    return info


# ------------------------------------------------------------------ #
# Health                                                              #
# ------------------------------------------------------------------ #


@router.post("/{plugin_id}/heartbeat")
async def plugin_heartbeat(
    plugin_id: int,
    db: Session = Depends(get_db),
) -> dict:
    plugin = plugin_service.get_plugin(db, plugin_id)
    if plugin is None:
        raise HTTPException(status_code=404, detail="Plugin not found")
    plugin_service.record_heartbeat(db, plugin_id)
    return {"status": "ok"}
