"""
Mission Control Agent Router

API endpoints for agent management: registration, heartbeat,
command dispatch, inventory, and CRUD.

Sprint 2.7 - Mission Control Agent.
"""

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.auth_dependency import get_current_user
from app.db import get_db
from app.schemas.agent import (
    AgentCommandDispatchRequest,
    AgentCommandListResponse,
    AgentCommandResponse,
    AgentCommandResultRequest,
    AgentCommandResultResponse,
    AgentHeartbeatRequest,
    AgentHeartbeatResponse,
    AgentInventoryResponse,
    AgentListResponse,
    AgentRegisterRequest,
    AgentRegisterResponse,
    AgentResponse,
    AgentUpdate,
)
from app.services.agent_service import AgentService, agent_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["Agents"])


def get_agent_service() -> AgentService:
    return agent_service


# ------------------------------------------------------------------ #
# Version (Agent -> Server)                                           #
# ------------------------------------------------------------------ #


@router.get("/version")
async def get_agent_version():
    """Return the latest agent version for self-update checks."""
    return {"version": "1.0.0"}


# ------------------------------------------------------------------ #
# Agent Registration & Heartbeat (Agent -> Server)                    #
# ------------------------------------------------------------------ #


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=AgentRegisterResponse,
)
async def register_agent(
    payload: AgentRegisterRequest,
    db: Session = Depends(get_db),
    service: AgentService = Depends(get_agent_service),
) -> AgentRegisterResponse:
    """Register a new agent with Mission Control."""
    company_id = None
    site_id = None

    if payload.registration_token:
        from app.services.agent_token_service import AgentTokenService

        token = AgentTokenService.validate_token(
            db, payload.registration_token
        )
        company_id = token.company_id
        site_id = token.site_id
        AgentTokenService.consume_token(db, token)

    return await service.register_agent(
        db, payload, company_id=company_id, site_id=site_id
    )


@router.post(
    "/heartbeat",
    response_model=AgentHeartbeatResponse,
)
async def agent_heartbeat(
    payload: AgentHeartbeatRequest,
    x_agent_api_key: str = Header(..., alias="X-Agent-API-Key"),
    db: Session = Depends(get_db),
    service: AgentService = Depends(get_agent_service),
) -> AgentHeartbeatResponse:
    """Process agent heartbeat and return pending commands."""
    await service.authenticate_agent(db, x_agent_api_key)
    return await service.process_heartbeat(db, payload, x_agent_api_key)


@router.post(
    "/{agent_id}/command-result",
    response_model=AgentCommandResultResponse,
)
async def report_command_result(
    agent_id: int,
    payload: AgentCommandResultRequest,
    x_agent_api_key: str = Header(..., alias="X-Agent-API-Key"),
    db: Session = Depends(get_db),
    service: AgentService = Depends(get_agent_service),
) -> AgentCommandResultResponse:
    """Report command execution result from an agent."""
    await service.authenticate_agent(db, x_agent_api_key)
    return await service.report_command_result(db, payload, agent_id)


@router.post(
    "/{agent_id}/inventory",
)
async def update_inventory(
    agent_id: int,
    inventory_data: dict,
    x_agent_api_key: str = Header(..., alias="X-Agent-API-Key"),
    db: Session = Depends(get_db),
    service: AgentService = Depends(get_agent_service),
) -> dict:
    """Update agent inventory data."""
    await service.authenticate_agent(db, x_agent_api_key)
    return await service.update_inventory(
        db, agent_id, inventory_data, x_agent_api_key
    )


# ------------------------------------------------------------------ #
# CRUD (Dashboard -> Server)                                           #
# ------------------------------------------------------------------ #


@router.get("", response_model=AgentListResponse)
async def list_agents(
    current_user: object = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: AgentService = Depends(get_agent_service),
) -> AgentListResponse:
    """List all registered agents."""
    return await service.list_agents(db)


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: int,
    current_user: object = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: AgentService = Depends(get_agent_service),
) -> AgentResponse:
    """Get a single agent by ID."""
    return await service.get_agent(db, agent_id)


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: int,
    payload: AgentUpdate,
    current_user: object = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: AgentService = Depends(get_agent_service),
) -> AgentResponse:
    """Update agent settings."""
    return await service.update_agent(db, agent_id, payload)


@router.delete(
    "/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_agent(
    agent_id: int,
    current_user: object = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: AgentService = Depends(get_agent_service),
) -> None:
    """Delete an agent."""
    await service.delete_agent(db, agent_id)


@router.get("/{agent_id}/api-key")
async def reveal_agent_api_key(
    agent_id: int,
    current_user: object = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: AgentService = Depends(get_agent_service),
) -> dict:
    """Reveal the API key for an agent."""
    return await service.reveal_api_key(db, agent_id)


@router.post(
    "/{agent_id}/enable",
    response_model=AgentResponse,
)
async def enable_agent(
    agent_id: int,
    current_user: object = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: AgentService = Depends(get_agent_service),
) -> AgentResponse:
    """Enable an agent."""
    return await service.enable_agent(db, agent_id)


@router.post(
    "/{agent_id}/disable",
    response_model=AgentResponse,
)
async def disable_agent(
    agent_id: int,
    current_user: object = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: AgentService = Depends(get_agent_service),
) -> AgentResponse:
    """Disable an agent."""
    return await service.disable_agent(db, agent_id)


# ------------------------------------------------------------------ #
# Command Dispatch (Dashboard -> Server -> Agent)                      #
# ------------------------------------------------------------------ #


@router.post(
    "/{agent_id}/execute",
    status_code=status.HTTP_201_CREATED,
    response_model=AgentCommandResponse,
)
async def dispatch_command(
    agent_id: int,
    payload: AgentCommandDispatchRequest,
    current_user: object = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: AgentService = Depends(get_agent_service),
) -> AgentCommandResponse:
    """Dispatch a command to an agent for execution."""
    payload.agent_id = agent_id
    return await service.dispatch_command(db, payload)


@router.get(
    "/{agent_id}/commands",
    response_model=AgentCommandListResponse,
)
async def get_agent_commands(
    agent_id: int,
    limit: int = Query(50, ge=1, le=500),
    current_user: object = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: AgentService = Depends(get_agent_service),
) -> AgentCommandListResponse:
    """Get command history for a specific agent."""
    return await service.get_agent_commands(db, agent_id)


@router.get(
    "/commands/all",
    response_model=AgentCommandListResponse,
)
async def get_all_commands(
    agent_id: int | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=500),
    current_user: object = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: AgentService = Depends(get_agent_service),
) -> AgentCommandListResponse:
    """List all agent commands with optional filters."""
    return await service.get_commands(
        db, agent_id=agent_id, status_filter=status_filter, limit=limit
    )


# ------------------------------------------------------------------ #
# Inventory                                                            #
# ------------------------------------------------------------------ #


@router.get(
    "/{agent_id}/inventory",
    response_model=AgentInventoryResponse,
)
async def get_inventory(
    agent_id: int,
    current_user: object = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: AgentService = Depends(get_agent_service),
) -> AgentInventoryResponse:
    """Get current inventory for an agent."""
    return await service.get_inventory(db, agent_id)


@router.get(
    "/{agent_id}/remote-inventory",
)
async def get_remote_inventory(
    agent_id: int,
    current_user: object = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: AgentService = Depends(get_agent_service),
) -> dict:
    """Get remote target inventory from an agent's latest inventory data."""
    return await service.get_remote_inventory(db, agent_id)


@router.get(
    "/debug/fix_agent_version.ps1",
    include_in_schema=False,
)
async def debug_fix_agent_version() -> Response:
    """Serve a local-only patcher script for the deployed Windows agent."""
    source = Path("/project/backend/debug/fix_agent_version.py")
    if not source.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="patcher not found")
    return Response(
        content=source.read_bytes(),
        media_type="text/x-powershell",
        headers={"Cache-Control": "no-store"},
    )


@router.get(
    "/debug/plugins/veeam_plugin.py",
    include_in_schema=False,
)
async def debug_veeam_plugin() -> Response:
    source = Path("/project/.agents/agent/plugins/veeam_plugin.py")
    if not source.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="plugin not found")
    return Response(
        content=source.read_bytes(),
        media_type="text/x-python",
        headers={"Cache-Control": "no-store"},
    )


@router.get(
    "/debug/uninstall_agent.ps1",
    include_in_schema=False,
)
async def debug_uninstall_agent() -> Response:
    source = Path("/project/backend/debug/uninstall_agent.ps1")
    if not source.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="uninstall script not found")
    return Response(
        content=source.read_bytes(),
        media_type="text/x-powershell",
        headers={"Cache-Control": "no-store"},
    )


@router.get(
    "/debug/install-agent.bat",
    include_in_schema=False,
)
async def debug_install_agent_bat() -> Response:
    source = Path("/project/backend/debug/install-agent.bat")
    if not source.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="installer not found")
    return Response(
        content=source.read_bytes(),
        media_type="application/x-msdos-program",
        headers={"Cache-Control": "no-store"},
    )


@router.get(
    "/{agent_id}/plugins/{plugin_name}",
    include_in_schema=False,
)
async def get_agent_plugin(agent_id: int, plugin_name: str) -> Response:
    source = Path("/project/.agents/agent/plugins") / plugin_name
    if not source.exists():
        source = Path("/project/.agents/agent/plugins") / f"{plugin_name}.py"
    if not source.exists():
        source = Path("/project/.agents/agent/plugins") / f"{plugin_name}_plugin.py"
    if not source.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="plugin not found")
    return Response(
        content=source.read_bytes(),
        media_type="text/x-python",
        headers={"Cache-Control": "no-store", "X-Plugin-Name": plugin_name},
    )



@router.post(
    "/{agent_id}/bundles/download",
    include_in_schema=False,
)
async def download_agent_bundle(agent_id: int) -> Response:
    source = Path("/project/.agents/agent-bundle-live.zip")
    if not source.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="bundle not found")
    return Response(
        content=source.read_bytes(),
        media_type="application/zip",
        headers={
            "Cache-Control": "no-store",
            "Content-Disposition": f'attachment; filename="missioncontrol-agent-3.0.0-rc1.zip"',
        },
    )


@router.post(
    "/bundles/download",
    include_in_schema=False,
)
async def download_agent_bundle_global() -> Response:
    source = Path("/project/.agents/agent-bundle-live.zip")
    if not source.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="bundle not found")
    return Response(
        content=source.read_bytes(),
        media_type="application/zip",
        headers={
            "Cache-Control": "no-store",
            "Content-Disposition": 'attachment; filename="missioncontrol-agent-3.0.0-rc1.zip"',
        },
    )
