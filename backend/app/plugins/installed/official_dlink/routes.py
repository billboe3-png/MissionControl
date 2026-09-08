"""
D-Link DGS-1210 Routes - REST API and WebSocket endpoints
"""
import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth_dependency import get_current_user
from app.db.database import get_db
from app.models.db.agent import Agent
from app.models.db.user import User
from app.plugins.installed.official_dlink.config import get_plugin_config
from app.plugins.installed.official_dlink.models import DLinkSwitch, DLinkRemoteTarget
from app.plugins.installed.official_dlink.repository import repository
from app.plugins.installed.official_dlink.service import dlink_service
from app.plugins.installed.official_dlink.webui_manager import webui_manager
from app.plugins.installed.official_dlink.relay import start_webui_stream

logger = logging.getLogger("plugin.dlink.routes")

router = APIRouter(
    prefix="/api/v1/plugins/dlink",
    tags=["dlink-plugin"],
    dependencies=[Depends(get_current_user)],
)

ADMIN_ROLES = {"global_admin", "company_admin", "site_admin"}
OPERATOR_ROLES = ADMIN_ROLES | {"operator"}


def require_operator(user: User = Depends(get_current_user)) -> User:
    if user.role not in OPERATOR_ROLES:
        raise HTTPException(status_code=403, detail="Operator role required")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role not in ADMIN_ROLES:
        raise HTTPException(status_code=403, detail="Admin role required")
    return user


# ---- Pydantic Models ----

class SwitchCreate(BaseModel):
    name: str
    host: str
    ssh_port: int = 22
    telnet_port: int = 23
    webui_port: int = 443
    webui_use_https: bool = True
    relay_agent_id: int
    remote_target_id: int
    company_id: Optional[int] = None
    site_id: Optional[int] = None
    enabled: bool = True


class SwitchUpdate(BaseModel):
    name: Optional[str] = None
    host: Optional[str] = None
    ssh_port: Optional[int] = None
    telnet_port: Optional[int] = None
    webui_port: Optional[int] = None
    webui_use_https: Optional[bool] = None
    relay_agent_id: Optional[int] = None
    remote_target_id: Optional[int] = None
    company_id: Optional[int] = None
    site_id: Optional[int] = None
    enabled: Optional[bool] = None


class SwitchResponse(BaseModel):
    id: int
    name: str
    host: str
    ssh_port: int
    telnet_port: int
    webui_port: int
    webui_use_https: bool
    relay_agent_id: int
    remote_target_id: int
    company_id: Optional[int]
    site_id: Optional[int]
    status: str
    firmware_version: Optional[str]
    hardware_version: Optional[str]
    serial_number: Optional[str]
    model_name: Optional[str]
    mac_address: Optional[str]
    enabled: bool
    last_seen: Optional[str]
    last_error: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class SwitchesResponse(BaseModel):
    items: List[SwitchResponse]
    total: int


class RemoteTargetCreate(BaseModel):
    agent_id: int
    name: str
    hostname: str
    protocol: str = "ssh"
    port: int = 22
    username: str = "admin"
    password: str
    enabled: bool = True
    tags: Optional[str] = None
    notes: Optional[str] = None


class RemoteTargetResponse(BaseModel):
    id: int
    agent_id: int
    name: str
    hostname: str
    protocol: str
    port: int
    username: str
    enabled: bool
    tags: Optional[str]
    notes: Optional[str]
    target_plugins: str
    last_collected_at: Optional[str]
    last_status: str
    last_error: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ExecuteRequest(BaseModel):
    command: str
    timeout: int = 30


class ExecuteResponse(BaseModel):
    success: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    error: Optional[str] = None


class WebUIRequest(BaseModel):
    method: str
    path: str
    body: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None


class PortConfigRequest(BaseModel):
    pvid: Optional[int] = None
    allowed_vlans: Optional[str] = None
    mode: Optional[str] = None


class VlanConfigRequest(BaseModel):
    vlan_id: int
    name: Optional[str] = None
    ports_tagged: Optional[List[int]] = None
    ports_untagged: Optional[List[int]] = None


# ---- Switch Endpoints ----

@router.get("/servers", response_model=SwitchesResponse)
async def list_switches(
    db: Session = Depends(get_db),
    company_id: Optional[int] = Query(None),
    site_id: Optional[int] = Query(None),
    enabled_only: bool = Query(False),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
):
    """List D-Link switches."""
    switches = repository.list_switches(
        db, company_id=company_id, site_id=site_id, enabled_only=enabled_only,
        limit=limit, offset=offset
    )
    total = repository.count_switches(
        db, company_id=company_id, site_id=site_id, enabled_only=enabled_only
    )
    return {"items": switches, "total": total}


@router.get("/servers/{switch_id}", response_model=SwitchResponse)
async def get_switch(
    switch_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a single D-Link switch."""
    switch = repository.get_switch(db, switch_id)
    if not switch:
        raise HTTPException(status_code=404, detail="Switch not found")
    return switch


@router.post("/servers", response_model=SwitchResponse, status_code=status.HTTP_201_CREATED)
async def create_switch(
    payload: SwitchCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_operator),
):
    """Create a new D-Link switch."""
    switch = dlink_service.create_switch(db, **payload.model_dump())
    return switch


@router.patch("/servers/{switch_id}", response_model=SwitchResponse)
async def update_switch(
    switch_id: int,
    payload: SwitchUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_operator),
):
    """Update a D-Link switch."""
    switch = dlink_service.update_switch(db, switch_id, **payload.model_dump(exclude_unset=True))
    if not switch:
        raise HTTPException(status_code=404, detail="Switch not found")
    return switch


@router.delete("/servers/{switch_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_switch(
    switch_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    """Delete a D-Link switch."""
    if not dlink_service.delete_switch(db, switch_id):
        raise HTTPException(status_code=404, detail="Switch not found")


# ---- Remote Target Endpoints ----

@router.get("/targets", response_model=List[RemoteTargetResponse])
async def list_remote_targets(
    agent_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List D-Link remote targets."""
    if agent_id:
        targets = repository.get_remote_targets_by_agent(db, agent_id)
    else:
        targets = db.query(DLinkRemoteTarget).filter(DLinkRemoteTarget.enabled == True).all()
    return targets


@router.post("/targets", response_model=RemoteTargetResponse, status_code=status.HTTP_201_CREATED)
async def create_remote_target(
    payload: RemoteTargetCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_operator),
):
    """Create a D-Link remote target (SSH/Telnet)."""
    from app.plugins.installed.official_dlink.service import encrypt_password
    target = dlink_service.create_remote_target(db, **payload.model_dump())
    return target


@router.delete("/targets/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_remote_target(
    target_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    """Delete a D-Link remote target."""
    if not dlink_service.delete_remote_target(db, target_id):
        raise HTTPException(status_code=404, detail="Remote target not found")


# ---- CLI Execution ----

@router.post("/servers/{switch_id}/execute", response_model=ExecuteResponse)
async def execute_cli(
    switch_id: int,
    payload: ExecuteRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_operator),
):
    """Execute a CLI command on the D-Link switch."""
    result = await dlink_service.execute_cli(db, switch_id, payload.command, payload.timeout)
    return result


@router.post("/servers/{switch_id}/test", response_model=ExecuteResponse)
async def test_connection(
    switch_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_operator),
):
    """Test connectivity to the D-Link switch."""
    result = await dlink_service.test_connection(db, switch_id)
    return result


# ---- Inventory ----

@router.post("/servers/{switch_id}/inventory")
async def collect_inventory(
    switch_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_operator),
):
    """Collect full inventory from the switch."""
    result = await dlink_service.collect_inventory(db, switch_id)
    return result


@router.post("/servers/{switch_id}/mac-table")
async def collect_mac_table(
    switch_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_operator),
):
    """Collect MAC address table (FDB)."""
    result = await dlink_service.collect_mac_table(db, switch_id)
    return result


@router.post("/servers/{switch_id}/vlans")
async def collect_vlans(
    switch_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_operator),
):
    """Collect VLAN configuration."""
    result = await dlink_service.collect_vlans(db, switch_id)
    return result


@router.post("/servers/{switch_id}/port-vlans")
async def collect_port_vlans(
    switch_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_operator),
):
    """Collect per-port VLAN configuration."""
    result = await dlink_service.collect_port_vlans(db, switch_id)
    return result


# ---- MAC Address Table ----

@router.get("/servers/{switch_id}/macs")
async def list_macs(
    switch_id: int,
    port: Optional[str] = Query(None),
    vlan_id: Optional[int] = Query(None),
    active_only: bool = Query(True),
    limit: int = Query(500, le=2000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List MAC address table entries."""
    entries = repository.get_mac_entries(
        db, switch_id, port=port, vlan_id=vlan_id,
        active_only=active_only, limit=limit, offset=offset
    )
    total = repository.count_mac_entries(
        db, switch_id, port=port, vlan_id=vlan_id, active_only=active_only
    )
    return {"items": entries, "total": total}


# ---- VLANs ----

@router.get("/servers/{switch_id}/vlans")
async def list_vlans(
    switch_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List VLANs on the switch."""
    vlans = repository.get_vlans(db, switch_id)
    return {"items": vlans}


@router.post("/servers/{switch_id}/vlans", response_model=Dict[str, Any])
async def create_or_update_vlan(
    switch_id: int,
    payload: VlanConfigRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_operator),
):
    """Create or update a VLAN."""
    result = await dlink_service.configure_vlan(
        db, switch_id,
        payload.vlan_id,
        payload.name,
        payload.ports_tagged,
        payload.ports_untagged
    )
    if result.get("success"):
        # Also update local DB
        tagged = ",".join(str(p) for p in (payload.ports_tagged or []))
        untagged = ",".join(str(p) for p in (payload.ports_untagged or []))
        repository.upsert_vlan(db, switch_id, payload.vlan_id, payload.name, tagged, untagged, None)
        db.commit()
    return result


@router.delete("/servers/{switch_id}/vlans/{vlan_id}")
async def delete_vlan(
    switch_id: int,
    vlan_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    """Delete a VLAN."""
    if not repository.delete_vlan(db, switch_id, vlan_id):
        raise HTTPException(status_code=404, detail="VLAN not found")
    return {"success": True}


# ---- Port VLAN Configuration ----

@router.get("/servers/{switch_id}/port-vlans")
async def list_port_vlans(
    switch_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List per-port VLAN configuration."""
    ports = repository.get_port_vlans(db, switch_id)
    return {"items": ports}


@router.post("/servers/{switch_id}/ports/{port}/vlan", response_model=Dict[str, Any])
async def configure_port_vlan(
    switch_id: int,
    port: str,
    payload: PortConfigRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_operator),
):
    """Configure port VLAN settings."""
    # Build CLI command
    cmd_parts = [f"config ports {port}"]
    if payload.pvid is not None:
        cmd_parts.append(f"pvid {payload.pvid}")
    if payload.allowed_vlans is not None:
        cmd_parts.append(f"allowed_vlan {payload.allowed_vlans}")
    if payload.mode is not None:
        cmd_parts.append(f"mode {payload.mode}")

    result = await dlink_service.execute_cli(db, switch_id, " ".join(cmd_parts))
    if result.get("success"):
        repository.upsert_port_vlan(
            db, switch_id, port,
            payload.pvid or 1,
            payload.allowed_vlans,
            payload.mode or "access"
        )
        db.commit()
    return result


# ---- Web UI REST Proxy ----

@router.post("/servers/{switch_id}/webui/request")
async def webui_request(
    switch_id: int,
    payload: WebUIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_operator),
):
    """Proxy a REST request to the D-Link switch web UI."""
    result = await dlink_service.webui_request(
        db, switch_id,
        payload.method, payload.path,
        payload.body, payload.headers
    )
    return result


# ---- Web UI WebSocket Tunnel ----

@router.websocket("/servers/{switch_id}/webui")
async def webui_websocket(
    websocket: WebSocket,
    switch_id: int,
    token: str = Query(default=""),
):
    """WebSocket tunnel for D-Link Web UI through the relay agent."""
    from app.services.auth_service import AuthService

    await websocket.accept()
    db = SessionLocal()
    try:
        user = None
        if token:
            try:
                user = AuthService.get_current_user(db, token)
            except (ValueError, Exception):
                user = None
        if user is None:
            await websocket.send_json({"type": "error", "message": "Unauthorized"})
            await websocket.close()
            return

        switch = repository.get_switch(db, switch_id)
        if switch is None:
            await websocket.send_json({"type": "error", "message": "Switch not found"})
            await websocket.close()
            return
        if not switch.relay_agent_id:
            await websocket.send_json({"type": "error", "message": "No relay agent configured"})
            await websocket.close()
            return
        agent = db.get(Agent, switch.relay_agent_id)
        if agent is None or agent.status != "online":
            await websocket.send_json({"type": "error", "message": "Relay agent offline"})
            await websocket.close()
            return
    finally:
        db.close()

    import asyncio

    session_id = f"dlink-webui-{switch_id}-{uuid.uuid4().hex[:12]}"
    webui_manager.create_session(session_id)

    # Instruct the agent to start the TCP tunnel
    await start_webui_stream(agent, switch, session_id)

    try:
        async def ws_to_session() -> None:
            while True:
                try:
                    msg = await websocket.receive_text()
                except WebSocketDisconnect:
                    webui_manager.close_session(session_id)
                    break
                if msg == "__CLOSE__":
                    webui_manager.close_session(session_id)
                    break
                session = webui_manager.get_session(session_id)
                if session:
                    session.send_input(msg)

        async def session_to_ws() -> None:
            while True:
                await asyncio.sleep(0.05)
                session = webui_manager.get_session(session_id)
                if session is None:
                    break
                chunks = session.read_output()
                if chunks:
                    import base64 as _b64
                    for chunk in chunks:
                        await websocket.send_text(_b64.b64encode(chunk).decode())
                if session.status in ("closed", "error"):
                    await websocket.send_text("__CLOSED__")
                    break

        done, pending = await asyncio.wait(
            [
                asyncio.create_task(ws_to_session()),
                asyncio.create_task(session_to_ws()),
            ],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
    finally:
        webui_manager.close_session(session_id)


# ---- Health ----

@router.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "plugin": "official_dlink"}


# Need to import SessionLocal
from app.db.database import SessionLocal