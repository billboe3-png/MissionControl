"""
MikroTik REST API Routes
"""
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.plugins.installed.official_mikrotik.cache import cache_manager
from app.plugins.installed.official_mikrotik.models import MikroTikServer
from app.plugins.installed.official_mikrotik.proxy import proxy as webfig_proxy
from app.plugins.installed.official_mikrotik.ssh_client import MikroTikSSHClient
from app.plugins.installed.official_mikrotik.telnet_client import MikroTikTelnetClient

logger = logging.getLogger("plugin.mikrotik.routes")

router = APIRouter(prefix="/api/v1/plugins/mikrotik", tags=["mikrotik-plugin"])


@router.get("/servers")
def list_servers(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """List all MikroTik servers."""
    return cache_manager.get_servers(db)


@router.post("/servers")
def create_server(payload: dict[str, Any], db: Session = Depends(get_db)) -> dict[str, Any]:
    """Register a new MikroTik server."""
    server = cache_manager.upsert_server(db, payload)
    db.flush()
    return cache_manager._server_to_dict(server)


@router.get("/servers/{server_id}")
def get_server(server_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get server details."""
    server = cache_manager.get_server(db, server_id)
    if server is None:
        raise HTTPException(status_code=404, detail="Server not found")
    return server


@router.put("/servers/{server_id}")
def update_server(server_id: int, payload: dict[str, Any], db: Session = Depends(get_db)) -> dict[str, Any]:
    """Update a server."""
    payload["id"] = server_id
    server = cache_manager.upsert_server(db, payload)
    db.flush()
    return cache_manager._server_to_dict(server)


@router.delete("/servers/{server_id}")
def delete_server(server_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Delete a server."""
    if not cache_manager.delete_server(db, server_id):
        raise HTTPException(status_code=404, detail="Server not found")
    return {"success": True}


@router.post("/servers/{server_id}/test")
async def test_server(server_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Test connection to a MikroTik server."""
    server = db.get(MikroTikServer, server_id)
    if server is None:
        raise HTTPException(status_code=404, detail="Server not found")

    client = MikroTikSSHClient(
        host=server.host,
        username=server.username,
        password=server.password_encrypted or "",
        port=server.ssh_port,
    )
    try:
        output = await client.execute("/system resource print")
        version = ""
        for line in output.splitlines():
            if line.startswith("version="):
                version = line.split("=", 1)[1].strip()
                break
        return {"connected": True, "version": version, "name": server.name, "server_id": server.id}
    except Exception as exc:
        logger.warning("MikroTik test failed for %s: %s", server.host, exc)
        return {"connected": False, "version": "", "name": server.name, "server_id": server.id, "error": str(exc)}


@router.get("/servers/{server_id}/interfaces")
async def get_interfaces(server_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get interfaces from cache or live."""
    cached = cache_manager.get_interfaces(db, server_id)
    if cached:
        return {"success": True, "interfaces": cached}

    server = db.get(MikroTikServer, server_id)
    if server is None:
        raise HTTPException(status_code=404, detail="Server not found")

    client = MikroTikSSHClient(
        host=server.host,
        username=server.username,
        password=server.password_encrypted or "",
        port=server.ssh_port,
    )
    try:
        output = await client.execute("/interface print detail")
        interfaces = MikroTikSSHClient._parse_key_value_output(output)
        cache_manager.replace_interfaces(db, server_id, interfaces)
        return {"success": True, "interfaces": interfaces}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/servers/{server_id}/firewall")
async def get_firewall(server_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get firewall rules from cache or live."""
    cached = cache_manager.get_firewall_rules(db, server_id)
    if cached:
        return {"success": True, "rules": cached}

    server = db.get(MikroTikServer, server_id)
    if server is None:
        raise HTTPException(status_code=404, detail="Server not found")

    client = MikroTikSSHClient(
        host=server.host,
        username=server.username,
        password=server.password_encrypted or "",
        port=server.ssh_port,
    )
    try:
        output = await client.execute("/ip firewall filter print detail")
        rules = MikroTikSSHClient._parse_key_value_output(output)
        cache_manager.replace_firewall_rules(db, server_id, rules)
        return {"success": True, "rules": rules}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/servers/{server_id}/dhcp")
async def get_dhcp(server_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get DHCP leases from cache or live."""
    cached = cache_manager.get_dhcp_leases(db, server_id)
    if cached:
        return {"success": True, "leases": cached}

    server = db.get(MikroTikServer, server_id)
    if server is None:
        raise HTTPException(status_code=404, detail="Server not found")

    client = MikroTikSSHClient(
        host=server.host,
        username=server.username,
        password=server.password_encrypted or "",
        port=server.ssh_port,
    )
    try:
        output = await client.execute("/ip dhcp-server lease print detail")
        leases = MikroTikSSHClient._parse_key_value_output(output)
        cache_manager.replace_dhcp_leases(db, server_id, leases)
        return {"success": True, "leases": leases}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/servers/{server_id}/system")
async def get_system(server_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get system resource info."""
    server = db.get(MikroTikServer, server_id)
    if server is None:
        raise HTTPException(status_code=404, detail="Server not found")

    client = MikroTikSSHClient(
        host=server.host,
        username=server.username,
        password=server.password_encrypted or "",
        port=server.ssh_port,
    )
    try:
        output = await client.execute("/system resource print")
        info = MikroTikSSHClient._parse_key_value_output(output)
        return {"success": True, "info": info[0] if info else {}}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/servers/{server_id}/backup")
async def backup_config(server_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Trigger a configuration backup download."""
    server = db.get(MikroTikServer, server_id)
    if server is None:
        raise HTTPException(status_code=404, detail="Server not found")

    client = MikroTikSSHClient(
        host=server.host,
        username=server.username,
        password=server.password_encrypted or "",
        port=server.ssh_port,
    )
    try:
        await client.execute("/system backup save name=mc-backup")
        await client.execute("/tool fetch url=flash/mc-backup.backup mode=http")
        return {"success": True, "message": "Backup saved as mc-backup.backup"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/servers/{server_id}/execute")
async def execute_command(server_id: int, payload: dict[str, Any], db: Session = Depends(get_db)) -> dict[str, Any]:
    """Execute an arbitrary MikroTik command."""
    server = db.get(MikroTikServer, server_id)
    if server is None:
        raise HTTPException(status_code=404, detail="Server not found")

    command = payload.get("command")
    if not command:
        raise HTTPException(status_code=400, detail="Missing command")

    use_telnet = bool(payload.get("telnet") and server.telnet_enabled)
    if use_telnet:
        client = MikroTikTelnetClient(
            host=server.host,
            username=server.username,
            password=server.password_encrypted or "",
            port=server.telnet_port or 23,
        )
    else:
        client = MikroTikSSHClient(
            host=server.host,
            username=server.username,
            password=server.password_encrypted or "",
            port=server.ssh_port,
        )

    try:
        output = await client.execute(command)
        return {"success": True, "output": output}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/servers/{server_id}/webfig/{path:path}")
async def proxy_webfig(server_id: int, path: str, request: Request, db: Session = Depends(get_db)):
    """Proxy WebFig UI through Mission Control."""
    return await webfig_proxy.handle_request(server_id, path, request, db)
