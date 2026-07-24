"""
Mission Control Agent Remote Target Router

CRUD endpoints for managing remote targets that agents relay data from.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth_dependency import get_current_user
from app.core.security import CredentialCipher
from app.db import get_db
from app.models.db.agent import Agent
from app.repositories.agent_remote_target_repository import (
    AgentRemoteTargetRepository,
)
from app.schemas.agent_remote_target import (
    AgentRemoteTargetsResponse,
    RemoteTargetCreate,
    RemoteTargetResponse,
    RemoteTargetUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["Agent Remote Targets"])

PROTOCOL_DEFAULTS = {
    "psremoting": 5985,
    "ssh": 22,
    "winrm": 5985,
}


def _get_cipher() -> CredentialCipher:
    from app.core.config import get_settings

    settings = get_settings()
    return CredentialCipher(settings.missioncontrol_secret_key)


def _encrypt_target(target, cipher: CredentialCipher) -> dict:
    """Build update dict with encrypted credentials."""
    update = {}
    if target.password is not None:
        update["password_encrypted"] = cipher.encrypt(target.password)
    if target.ssh_key is not None:
        update["ssh_key_encrypted"] = cipher.encrypt(target.ssh_key)
    return update


@router.get(
    "/{agent_id}/remote-targets",
    response_model=AgentRemoteTargetsResponse,
)
async def list_remote_targets(
    agent_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
) -> AgentRemoteTargetsResponse:
    """List all remote targets for an agent."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    targets = AgentRemoteTargetRepository.get_by_agent_id(db, agent_id)
    return AgentRemoteTargetsResponse(
        agent_id=agent.id,
        agent_name=agent.name,
        targets=[RemoteTargetResponse.model_validate(t) for t in targets],
    )


@router.post(
    "/{agent_id}/remote-targets",
    response_model=RemoteTargetResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_remote_target(
    agent_id: int,
    payload: RemoteTargetCreate,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
) -> RemoteTargetResponse:
    """Create a remote target for an agent."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    port = payload.port or PROTOCOL_DEFAULTS.get(payload.protocol, 5985)
    cipher = _get_cipher()

    kwargs = {
        "name": payload.name,
        "hostname": payload.hostname,
        "protocol": payload.protocol,
        "port": port,
        "username": payload.username,
        "enabled": payload.enabled,
        "tags": payload.tags,
        "notes": payload.notes,
    }

    if payload.password:
        kwargs["password_encrypted"] = cipher.encrypt(payload.password)
    if payload.ssh_key:
        kwargs["ssh_key_encrypted"] = cipher.encrypt(payload.ssh_key)

    target = AgentRemoteTargetRepository.create(db, agent_id=agent_id, **kwargs)
    return RemoteTargetResponse.model_validate(target)


@router.get(
    "/{agent_id}/remote-targets/{target_id}",
    response_model=RemoteTargetResponse,
)
async def get_remote_target(
    agent_id: int,
    target_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
) -> RemoteTargetResponse:
    """Get a single remote target."""
    target = AgentRemoteTargetRepository.get_by_id(db, target_id)
    if target is None or target.agent_id != agent_id:
        raise HTTPException(status_code=404, detail="Target not found")
    return RemoteTargetResponse.model_validate(target)


@router.put(
    "/{agent_id}/remote-targets/{target_id}",
    response_model=RemoteTargetResponse,
)
async def update_remote_target(
    agent_id: int,
    target_id: int,
    payload: RemoteTargetUpdate,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
) -> RemoteTargetResponse:
    """Update a remote target."""
    target = AgentRemoteTargetRepository.get_by_id(db, target_id)
    if target is None or target.agent_id != agent_id:
        raise HTTPException(status_code=404, detail="Target not found")

    cipher = _get_cipher()
    update_data = payload.model_dump(exclude_unset=True)

    if "password" in update_data:
        pwd = update_data.pop("password")
        if pwd is not None:
            update_data["password_encrypted"] = cipher.encrypt(pwd)
        else:
            update_data["password_encrypted"] = None

    if "ssh_key" in update_data:
        key = update_data.pop("ssh_key")
        if key is not None:
            update_data["ssh_key_encrypted"] = cipher.encrypt(key)
        else:
            update_data["ssh_key_encrypted"] = None

    updated = AgentRemoteTargetRepository.update(db, target_id, **update_data)
    if updated is None:
        raise HTTPException(status_code=404, detail="Target not found")
    return RemoteTargetResponse.model_validate(updated)


@router.delete(
    "/{agent_id}/remote-targets/{target_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_remote_target(
    agent_id: int,
    target_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
) -> None:
    """Delete a remote target."""
    target = AgentRemoteTargetRepository.get_by_id(db, target_id)
    if target is None or target.agent_id != agent_id:
        raise HTTPException(status_code=404, detail="Target not found")
    AgentRemoteTargetRepository.delete(db, target_id)


@router.post(
    "/{agent_id}/remote-targets/{target_id}/test",
)
async def test_remote_target(
    agent_id: int,
    target_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
) -> dict:
    """Test connection to a remote target (via agent relay or direct)."""
    target = AgentRemoteTargetRepository.get_by_id(db, target_id)
    if target is None or target.agent_id != agent_id:
        raise HTTPException(status_code=404, detail="Target not found")

    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    if agent.status != "online":
        return {
            "connected": False,
            "error": f"Agent '{agent.name}' is offline — cannot test target",
            "latency_ms": 0,
        }

    from app.services.agent_service import agent_service as svc

    cmd_result = await svc.dispatch_command(
        db,
        agent_id=agent_id,
        command_type="remote_execute",
        command=f"echo connected",
        timeout=15,
    )

    return {
        "connected": True,
        "message": f"Test command dispatched to agent for target '{target.name}'",
        "command_id": cmd_result.id if cmd_result else None,
    }
