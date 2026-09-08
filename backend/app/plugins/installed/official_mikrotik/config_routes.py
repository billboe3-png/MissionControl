"""MikroTik REST API Routes for configuration operations."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.auth_dependency import get_current_user
from app.db.database import get_db
from app.models.db.user import User
from app.plugins.installed.official_mikrotik.models import MikroTikServer
from app.plugins.installed.official_mikrotik.proxy import proxy as webfig_proxy
from app.plugins.installed.official_mikrotik.relay import (
    delete_remote_target,
    provision_remote_target,
)
from app.plugins.installed.official_mikrotik.repository import MikroTikRepository
from app.plugins.installed.official_mikrotik.service import (
    CONNECTOR_TYPES,
    encrypt_password,
    mikrotik_service,
)
from app.plugins.installed.official_mikrotik.config_service import (
    MikroTikConfigService,
)
from app.plugins.installed.official_mikrotik.cache import MikroTikCacheManager

logger = logging.getLogger("plugin.mikrotik.routes")

router = APIRouter(
    prefix="/api/v1/plugins/mikrotik",
    tags=["mikrotik-plugin"],
    dependencies=[Depends(get_current_user)],
)

ADMIN_ROLES = {"global_admin", "company_admin", "site_admin"}
OPERATOR_ROLES = ADMIN_ROLES | {"operator"}

_config_service = MikroTikConfigService()
_repository = MikroTikRepository()
_cache_manager = MikroTikCacheManager()


# ---------------------------------------------------------------------- #
# Helpers                                                                 #
# ---------------------------------------------------------------------- #


def _require_role(user: User, allowed: set[str]) -> None:
    if user.role not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient role for this operation",
        )


def _get_server_or_404(db: Session, server_id: int) -> MikroTikServer:
    server = _repository.get_server(db, server_id)
    if server is None:
        raise HTTPException(status_code=404, detail="Server not found")
    return server


# ---------------------------------------------------------------------- #
# WebSocket proxy for live WebFig updates                                 #
# ---------------------------------------------------------------------- #


@router.get("/servers/{server_id}/webfig/ws")
async def proxy_webfig_ws(
    server_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """WebSocket proxy for RouterOS live UI updates."""
    _require_role(user, OPERATOR_ROLES)
    return await webfig_proxy.ws_proxy.handle_request(server_id, request, db)


# ---------------------------------------------------------------------- #
# Configuration operations                                                #
# ---------------------------------------------------------------------- #


@router.get("/servers/{server_id}/config/interfaces")
async def list_interfaces_config(
    server_id: int,
    db: Session = Depends(get_db),
    refresh: bool = Query(default=False, description="Bypass cache and fetch live data"),
) -> dict[str, Any]:
    """List interfaces with editable configuration."""
    server = _get_server_or_404(db, server_id)

    if not refresh:
        cached = _cache_manager.get_interfaces(db, server_id)
        if cached:
            return {"success": True, "interfaces": cached, "cached": True}

    try:
        interfaces = await _config_service.list_interfaces(db, server)
        _cache_manager.replace_interfaces(db, server_id, interfaces)
        db.commit()
        return {"success": True, "interfaces": interfaces, "cached": False}
    except Exception as exc:
        logger.exception("Failed to list interfaces for server %s", server_id)
        raise HTTPException(status_code=500, detail=str(exc))


@router.patch("/servers/{server_id}/config/interfaces/{interface_name}")
async def update_interface(
    server_id: int,
    interface_name: str,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Update interface configuration."""
    _require_role(user, OPERATOR_ROLES)
    server = _get_server_or_404(db, server_id)

    allowed_fields = {"disabled", "comment", "name", "mac_address"}
    update_data = {k: v for k, v in payload.items() if k in allowed_fields}

    try:
        result = await _config_service.update_interface(db, server, interface_name, update_data)
        _cache_manager.replace_interfaces(db, server_id, result.get("interface", {}))
        db.commit()
        return {"success": True, "interface": result}
    except Exception as exc:
        logger.exception("Failed to update interface %s on server %s", interface_name, server_id)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/servers/{server_id}/config/ip-addresses")
async def list_ip_addresses(
    server_id: int,
    db: Session = Depends(get_db),
    refresh: bool = Query(default=False, description="Bypass cache and fetch live data"),
) -> dict[str, Any]:
    """List IP addresses."""
    server = _get_server_or_404(db, server_id)
    try:
        addresses = await _config_service.list_ip_addresses(db, server)
        return {"success": True, "addresses": addresses, "cached": False}
    except Exception as exc:
        logger.exception("Failed to list IP addresses for server %s", server_id)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/servers/{server_id}/config/ip-addresses")
async def create_ip_address(
    server_id: int,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Add an IP address to an interface."""
    _require_role(user, OPERATOR_ROLES)
    server = _get_server_or_404(db, server_id)

    required_fields = {"address", "interface"}
    if not required_fields.issubset(payload.keys()):
        raise HTTPException(status_code=422, detail="Missing required fields: address, interface")

    try:
        result = await _config_service.create_ip_address(db, server, payload)
        return {"success": True, "address": result}
    except Exception as exc:
        logger.exception("Failed to create IP address on server %s", server_id)
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/servers/{server_id}/config/ip-addresses/{address_id}")
async def delete_ip_address(
    server_id: int,
    address_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Delete an IP address."""
    _require_role(user, OPERATOR_ROLES)
    server = _get_server_or_404(db, server_id)

    try:
        result = await _config_service.delete_ip_address(db, server, address_id)
        return {"success": True, "deleted": result}
    except Exception as exc:
        logger.exception("Failed to delete IP address %s on server %s", address_id, server_id)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/servers/{server_id}/config/firewall-rules")
async def list_firewall_rules_config(
    server_id: int,
    db: Session = Depends(get_db),
    refresh: bool = Query(default=False, description="Bypass cache and fetch live data"),
) -> dict[str, Any]:
    """List firewall rules with editable fields."""
    server = _get_server_or_404(db, server_id)
    try:
        rules = await _config_service.list_firewall_rules(db, server)
        return {"success": True, "rules": rules, "cached": False}
    except Exception as exc:
        logger.exception("Failed to list firewall rules for server %s", server_id)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/servers/{server_id}/config/firewall-rules")
async def create_firewall_rule(
    server_id: int,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Add a firewall rule."""
    _require_role(user, ADMIN_ROLES)
    server = _get_server_or_404(db, server_id)

    try:
        result = await _config_service.create_firewall_rule(db, server, payload)
        return {"success": True, "rule": result}
    except Exception as exc:
        logger.exception("Failed to create firewall rule on server %s", server_id)
        raise HTTPException(status_code=500, detail=str(exc))


@router.patch("/servers/{server_id}/config/firewall-rules/{rule_id}")
async def update_firewall_rule(
    server_id: int,
    rule_id: str,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Update a firewall rule."""
    _require_role(user, ADMIN_ROLES)
    server = _get_server_or_404(db, server_id)

    try:
        result = await _config_service.update_firewall_rule(db, server, rule_id, payload)
        return {"success": True, "rule": result}
    except Exception as exc:
        logger.exception("Failed to update firewall rule %s on server %s", rule_id, server_id)
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/servers/{server_id}/config/firewall-rules/{rule_id}")
async def delete_firewall_rule(
    server_id: int,
    rule_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Delete a firewall rule."""
    _require_role(user, ADMIN_ROLES)
    server = _get_server_or_404(db, server_id)

    try:
        result = await _config_service.delete_firewall_rule(db, server, rule_id)
        return {"success": True, "deleted": result}
    except Exception as exc:
        logger.exception("Failed to delete firewall rule %s on server %s", rule_id, server_id)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/servers/{server_id}/config/dhcp-leases")
async def list_dhcp_leases_config(
    server_id: int,
    db: Session = Depends(get_db),
    refresh: bool = Query(default=False, description="Bypass cache and fetch live data"),
) -> dict[str, Any]:
    """List DHCP leases."""
    server = _get_server_or_404(db, server_id)
    try:
        leases = await _config_service.list_dhcp_leases(db, server)
        return {"success": True, "leases": leases, "cached": False}
    except Exception as exc:
        logger.exception("Failed to list DHCP leases for server %s", server_id)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/servers/{server_id}/config/system")
async def get_system_config(
    server_id: int,
    db: Session = Depends(get_db),
    refresh: bool = Query(default=False, description="Bypass cache and fetch live data"),
) -> dict[str, Any]:
    """Get system configuration."""
    server = _get_server_or_404(db, server_id)
    try:
        config = await _config_service.get_system_config(db, server)
        return {"success": True, "config": config, "cached": False}
    except Exception as exc:
        logger.exception("Failed to get system config for server %s", server_id)
        raise HTTPException(status_code=500, detail=str(exc))


@router.patch("/servers/{server_id}/config/system")
async def update_system_config(
    server_id: int,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Update system configuration (e.g., identity, routerboard settings)."""
    _require_role(user, ADMIN_ROLES)
    server = _get_server_or_404(db, server_id)

    allowed_fields = {"identity", "routerboard", "note", "contact", "location"}
    update_data = {k: v for k, v in payload.items() if k in allowed_fields}

    try:
        result = await _config_service.update_system_config(db, server, update_data)
        return {"success": True, "config": result}
    except Exception as exc:
        logger.exception("Failed to update system config for server %s", server_id)
        raise HTTPException(status_code=500, detail=str(exc))
