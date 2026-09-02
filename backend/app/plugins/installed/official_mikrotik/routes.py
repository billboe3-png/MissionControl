"""
MikroTik REST API Routes

All routes require authentication. Mutating operations require an admin
role; execution/test/backup/webfig require operator or above.
Response shapes match frontend/src/services/mikrotik.ts.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.auth_dependency import get_current_user
from app.db.database import get_db
from app.models.db.agent import Agent
from app.models.db.user import User
from app.plugins.installed.official_mikrotik.cache import cache_manager
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
from app.plugins.installed.official_mikrotik.config_routes import router as config_router

logger = logging.getLogger("plugin.mikrotik.routes")

router = APIRouter(
    prefix="/api/v1/plugins/mikrotik",
    tags=["mikrotik-plugin"],
    dependencies=[Depends(get_current_user)],
)

ADMIN_ROLES = {"global_admin", "company_admin", "site_admin"}
OPERATOR_ROLES = ADMIN_ROLES | {"operator"}

EDITABLE_FIELDS = {
    "name",
    "host",
    "ssh_port",
    "telnet_enabled",
    "telnet_port",
    "username",
    "api_enabled",
    "api_port",
    "relay_agent_id",
    "enabled",
}

# Fields that must re-provision the relay's SSH remote target when changed.
RELAY_TARGET_FIELDS = {"host", "ssh_port", "username", "relay_agent_id"}

_repository = MikroTikRepository()


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Server not found")
    return server


def _extract_server_fields(payload: dict[str, Any]) -> dict[str, Any]:
    """Whitelist editable fields and encrypt a plaintext password if present."""
    fields: dict[str, Any] = {k: v for k, v in payload.items() if k in EDITABLE_FIELDS}
    password = payload.pop("password", None)
    # Never accept a client-supplied value directly into password_encrypted.
    payload.pop("password_encrypted", None)
    if password is not None:
        fields["password_encrypted"] = encrypt_password(str(password))
    return fields


def _check_duplicate_name(db: Session, name: str, exclude_id: int | None = None) -> None:
    existing = _repository.get_server_by_name(db, name)
    if existing is not None and existing.id != exclude_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A server with this name already exists",
        )


def _require_relay_agent(db: Session, relay_agent_id: int | None) -> None:
    if relay_agent_id is None:
        return
    if db.get(Agent, relay_agent_id) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Relay agent {relay_agent_id} not found",
        )


def _sync_relay_target(db: Session, server: MikroTikServer) -> None:
    """Create/update/remove the SSH remote target backing this server."""
    if not server.relay_agent_id:
        if server.remote_target_id:
            delete_remote_target(db, server)
        return
    _require_relay_agent(db, server.relay_agent_id)
    provision_remote_target(db, server, server.password_encrypted)


# ---------------------------------------------------------------------- #
# Server CRUD                                                             #
# ---------------------------------------------------------------------- #


@router.get("/servers")
def list_servers(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """List all MikroTik servers."""
    return cache_manager.get_servers(db)


@router.post("/servers", status_code=status.HTTP_201_CREATED)
def create_server(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Register a new MikroTik server."""
    _require_role(user, ADMIN_ROLES)
    name = str(payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=422, detail="name is required")
    _check_duplicate_name(db, name)

    fields = _extract_server_fields(dict(payload))
    fields["name"] = name
    _require_relay_agent(db, fields.get("relay_agent_id"))
    server = _repository.create_server(db, **fields)
    if server.relay_agent_id:
        _sync_relay_target(db, server)
    db.commit()
    logger.info("MikroTik server id=%s created by %s", server.id, user.email)
    return cache_manager._server_to_dict(server)


@router.get("/servers/{server_id}")
def get_server(server_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get server details."""
    server = cache_manager.get_server(db, server_id)
    if server is None:
        raise HTTPException(status_code=404, detail="Server not found")
    return server


@router.put("/servers/{server_id}")
def update_server(
    server_id: int,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Update a server."""
    _require_role(user, ADMIN_ROLES)
    server = _get_server_or_404(db, server_id)

    if "name" in payload:
        new_name = str(payload["name"] or "").strip()
        if not new_name:
            raise HTTPException(status_code=422, detail="name cannot be empty")
        _check_duplicate_name(db, new_name, exclude_id=server_id)
        payload["name"] = new_name

    if "relay_agent_id" in payload:
        _require_relay_agent(db, payload["relay_agent_id"])

    relay_triggers = bool(
        RELAY_TARGET_FIELDS.intersection(payload) or "name" in payload or "password" in payload
    )

    fields = _extract_server_fields(dict(payload))
    updated = _repository.update_server(db, server, **fields)
    if relay_triggers or "relay_agent_id" in fields:
        _sync_relay_target(db, updated)
    db.commit()
    logger.info("MikroTik server id=%s updated by %s", server_id, user.email)
    return cache_manager._server_to_dict(updated)


@router.delete("/servers/{server_id}")
def delete_server(
    server_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Delete a server."""
    _require_role(user, ADMIN_ROLES)
    server = _get_server_or_404(db, server_id)
    delete_remote_target(db, server)
    if not cache_manager.delete_server(db, server_id):
        raise HTTPException(status_code=404, detail="Server not found")
    db.commit()
    logger.info("MikroTik server id=%s deleted by %s", server_id, user.email)
    return {"success": True}


# ---------------------------------------------------------------------- #
# Operations                                                              #
# ---------------------------------------------------------------------- #


@router.post("/servers/{server_id}/test")
async def test_server(
    server_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Test connection to a MikroTik server."""
    _require_role(user, OPERATOR_ROLES)
    server = _get_server_or_404(db, server_id)
    result = await mikrotik_service.test_server(db, server)
    logger.info(
        "MikroTik server id=%s tested by %s -> connected=%s",
        server_id,
        user.email,
        result.get("connected"),
    )
    return result


@router.get("/servers/{server_id}/interfaces")
async def get_interfaces(server_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get interfaces from cache or live."""
    cached = cache_manager.get_interfaces(db, server_id)
    if cached:
        return {"success": True, "interfaces": cached}

    server = _get_server_or_404(db, server_id)
    interfaces = await mikrotik_service.fetch_interfaces(db, server)
    cache_manager.replace_interfaces(db, server_id, interfaces)
    db.commit()
    return {"success": True, "interfaces": interfaces}


@router.get("/servers/{server_id}/firewall")
async def get_firewall(server_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get firewall rules from cache or live."""
    cached = cache_manager.get_firewall_rules(db, server_id)
    if cached:
        return {"success": True, "rules": cached}

    server = _get_server_or_404(db, server_id)
    rules = await mikrotik_service.fetch_firewall(db, server)
    cache_manager.replace_firewall_rules(db, server_id, rules)
    db.commit()
    return {"success": True, "rules": rules}


@router.get("/servers/{server_id}/dhcp")
async def get_dhcp(server_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get DHCP leases from cache or live."""
    cached = cache_manager.get_dhcp_leases(db, server_id)
    if cached:
        return {"success": True, "leases": cached}

    server = _get_server_or_404(db, server_id)
    leases = await mikrotik_service.fetch_dhcp_leases(db, server)
    cache_manager.replace_dhcp_leases(db, server_id, leases)
    db.commit()
    return {"success": True, "leases": leases}


@router.get("/servers/{server_id}/system")
async def get_system(server_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get system resource info."""
    server = _get_server_or_404(db, server_id)
    info = await mikrotik_service.fetch_system(db, server)
    return {"success": True, "info": info}


@router.post("/servers/{server_id}/backup")
async def backup_config(
    server_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Trigger a configuration backup on the device."""
    _require_role(user, OPERATOR_ROLES)
    server = _get_server_or_404(db, server_id)
    result = await mikrotik_service.run_command(
        db,
        server,
        "/system backup save name=mc-backup",
        executed_by=user.email,
        connector_type="ssh",
    )
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    return {"success": True, "message": "Backup saved as mc-backup.backup"}


@router.post("/servers/{server_id}/execute")
async def execute_command(
    server_id: int,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Execute a read command on a MikroTik server."""
    _require_role(user, OPERATOR_ROLES)
    server = _get_server_or_404(db, server_id)

    command = payload.get("command")
    if not command or not isinstance(command, str):
        raise HTTPException(status_code=400, detail="Missing command")

    use_telnet = bool(payload.get("telnet") and server.telnet_enabled)
    result = await mikrotik_service.run_command(
        db,
        server,
        command,
        executed_by=user.email,
        connector_type="telnet" if use_telnet else None,
    )
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    return {"success": True, "output": result.output}


@router.get("/servers/{server_id}/logs")
async def list_command_logs(
    server_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Recent command audit log for a server."""
    _require_role(user, OPERATOR_ROLES)
    _get_server_or_404(db, server_id)
    entries = _repository.list_command_logs(db, server_id, limit=limit)
    return {
        "count": len(entries),
        "items": [
            {
                "id": entry.id,
                "connector_type": entry.connector_type,
                "command": entry.command,
                "success": entry.success,
                "error": entry.error,
                "duration_ms": entry.duration_ms,
                "executed_by": entry.executed_by,
                "created_at": entry.created_at.isoformat() if entry.created_at else None,
            }
            for entry in entries
        ],
    }


@router.get("/servers/{server_id}/webfig/{path:path}")
async def proxy_webfig(
    server_id: int,
    path: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Proxy WebFig UI through Mission Control."""
    _require_role(user, OPERATOR_ROLES)
    return await webfig_proxy.handle_request(server_id, path, request, db)


@router.get("/agents")
async def list_relay_agents(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Edge agents available as relays (for the server form dropdown)."""
    agents = db.query(Agent).order_by(Agent.name).all()
    return [
        {
            "id": agent.id,
            "name": agent.name,
            "status": agent.status,
            "ip_address": agent.ip_address,
        }
        for agent in agents
    ]


# ---------------------------------------------------------------------- #
# Plugin-level                                                            #
# ---------------------------------------------------------------------- #


@router.get("/health")
async def plugin_health(db: Session = Depends(get_db)) -> dict[str, Any]:
    servers = _repository.list_servers(db)
    online = sum(1 for s in servers if s.status == "online")
    degraded = sum(1 for s in servers if s.status not in ("online", "unknown"))
    overall = "ok"
    if servers and online == 0:
        overall = "warning"
    return {
        "status": overall,
        "connectors": list(CONNECTOR_TYPES),
        "total_servers": len(servers),
        "enabled_servers": sum(1 for s in servers if s.enabled),
        "online_servers": online,
        "degraded_servers": degraded,
    }
