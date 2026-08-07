"""
Mission Control Edge Agent Router

Pull-based config sync and data ingestion for offline-first edge agents.
Cloud never pushes config; edge pulls when online.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from pathlib import Path

from app.core.auth_dependency import get_current_user
from app.db import get_db
from app.repositories.agent_repository import AgentRepository
from app.schemas.agent import AgentHeartbeatRequest
from app.services.agent_service import AgentService, agent_service

try:
    from app.ai.assistant import ai_assistant
except Exception:  # pragma: no cover - optional dependency
    ai_assistant = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/edge", tags=["Edge Agent"])


def get_agent_service() -> AgentService:
    return agent_service


def _resolve_api_key(x_agent_api_key: str | None, authorization: str | None) -> str:
    """Accept either X-Agent-API-Key or Authorization: Bearer <key>."""
    if x_agent_api_key:
        return x_agent_api_key
    if authorization:
        parts = authorization.split(" ", 1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]
        return authorization
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing X-Agent-API-Key or Authorization header",
    )


# ------------------------------------------------------------------
# Edge AI - server-side assistant for edge agents
# ------------------------------------------------------------------


class EdgeAIAskRequest(BaseModel):
    question: str
    context: dict[str, Any] | None = None
    timestamp: str | None = None


@router.post("/{agent_id}/ai/ask")
async def edge_ai_ask(
    agent_id: int,
    payload: EdgeAIAskRequest,
    x_agent_api_key: str = Header(..., alias="X-Agent-API-Key"),
    db: Session = Depends(get_db),
    service: AgentService = Depends(get_agent_service),
):
    """Server-side AI assistant for edge agents."""
    agent = await service.authenticate_agent(db, x_agent_api_key)
    if agent.id != agent_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Agent ID mismatch")

    if ai_assistant is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI assistant unavailable")

    try:
        result = await ai_assistant.query(payload.question, db)
        result.setdefault("sources", [])
        result.setdefault("timestamp", datetime.now(UTC).isoformat())
        return result
    except Exception as e:
        logger.error("Edge AI query failed: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="AI query failed")


# ------------------------------------------------------------------ #
# Edge config pull
# ------------------------------------------------------------------ #


@router.get("/{agent_id}/config")
async def get_edge_config(
    agent_id: int,
    request: Request,
    x_agent_api_key: str | None = Header(None, alias="X-Agent-API-Key"),
    authorization: str | None = Header(None, alias="Authorization"),
    db: Session = Depends(get_db),
    service: AgentService = Depends(get_agent_service),
):
    """Return the current configuration manifest for an edge agent."""
    api_key = _resolve_api_key(x_agent_api_key, authorization)
    agent = await service.authenticate_agent(db, api_key)
    if agent.id != agent_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Agent ID mismatch")

    manifest = _build_config_manifest(db, agent, service)
    return manifest


def _build_config_manifest(db: Session, agent, service: AgentService) -> dict:
    """Build the configuration manifest for the edge agent."""
    profiles = service._integration_profiles_for_agent(db, agent.id)
    remote_targets = service._get_remote_targets_for_agent(db, agent.id)
    pending_plugins = []
    if agent.enabled_plugins:
        pending_plugins = service._pending_plugins(agent.enabled_plugins, agent.active_plugins)

    return {
        "config_version": 1,
        "agent_id": agent.id,
        "last_modified": datetime.now(UTC).isoformat(),
        "config": {
            "heartbeat_interval": agent.heartbeat_interval or 60,
            "inventory_interval": (agent.heartbeat_interval or 60) * 2,
            "data_dir": "/var/lib/mc-agent",
        },
        "plugins": pending_plugins,
        "remote_targets": remote_targets,
        "integration_profiles": profiles,
    }


# ------------------------------------------------------------------ #
# Edge data push
# ------------------------------------------------------------------ #


@router.post("/{agent_id}/inventory")
async def push_edge_inventory(
    agent_id: int,
    request: Request,
    x_agent_api_key: str | None = Header(None, alias="X-Agent-API-Key"),
    authorization: str | None = Header(None, alias="Authorization"),
    db: Session = Depends(get_db),
    service: AgentService = Depends(get_agent_service),
):
    """Accept inventory data from an edge agent."""
    api_key = _resolve_api_key(x_agent_api_key, authorization)
    agent = await service.authenticate_agent(db, api_key)
    if agent.id != agent_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Agent ID mismatch")

    content = await request.body()
    try:
        payload = json.loads(gzip.decompress(content))
    except Exception:
        payload = await request.json()

    records = payload.get("records", [])
    stored = 0
    plugins = payload.get("plugins")

    if not plugins and records:
        plugins = {}
        for record in records:
            plugin_name = record.get("plugin_name")
            if plugin_name is None:
                continue
            entry = dict(record)
            entry.pop("plugin_name", None)
            plugins.setdefault(plugin_name, {}).update(entry.get("data", {}) if isinstance(entry.get("data"), dict) else {"value": str(entry.get("data"))})
    payload_to_store = {"plugins": plugins} if plugins else payload

    if payload_to_store.get("plugins"):
        try:
            await service.update_inventory(db, agent_id, payload_to_store, api_key)
            stored = 1
        except Exception as e:
            logger.warning("Failed to store aggregated inventory payload: %s", e)
    elif records:
        for record in records:
            try:
                await service.update_inventory(db, agent_id, record, api_key)
                stored += 1
            except Exception as e:
                logger.warning("Failed to store inventory record: %s", e)

    logger.info("Edge inventory: received %d, stored %d", len(records), stored)
    return {"status": "ok", "received": len(records), "stored": stored}


@router.post("/{agent_id}/heartbeat")
async def push_edge_heartbeat(
    agent_id: int,
    payload: AgentHeartbeatRequest,
    x_agent_api_key: str | None = Header(None, alias="X-Agent-API-Key"),
    authorization: str | None = Header(None, alias="Authorization"),
    db: Session = Depends(get_db),
    service: AgentService = Depends(get_agent_service),
):
    """Accept heartbeat from an edge agent."""
    api_key = _resolve_api_key(x_agent_api_key, authorization)
    agent = await service.authenticate_agent(db, api_key)
    if agent.id != agent_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Agent ID mismatch")

    AgentRepository.update(
        db,
        agent.id,
        status="online",
        last_heartbeat=datetime.now(UTC),
    )

    return {"status": "ok", "agent_id": agent_id}


# ------------------------------------------------------------------ #
# Edge plugin files
# ------------------------------------------------------------------ #


@router.get("/{agent_id}/plugins/{plugin_name}")
async def get_edge_plugin(
    agent_id: int,
    plugin_name: str,
    x_agent_api_key: str | None = Header(None, alias="X-Agent-API-Key"),
    authorization: str | None = Header(None, alias="Authorization"),
    db: Session = Depends(get_db),
    service: AgentService = Depends(get_agent_service),
):
    """Return a plugin source file for the edge agent."""
    api_key = _resolve_api_key(x_agent_api_key, authorization)
    agent = await service.authenticate_agent(db, api_key)
    if agent.id != agent_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Agent ID mismatch")

    plugin_file = _plugin_file_for_agent(db, agent, plugin_name)
    if plugin_file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plugin not found")

    checksum = hashlib.sha256(plugin_file.encode("utf-8")).hexdigest()[:16]
    return {
        "file_name": plugin_name,
        "content": plugin_file,
        "version": "1.0.0",
        "checksum": checksum,
    }


def _plugin_file_for_agent(db: Session, agent, plugin_name: str) -> str | None:
    """Return plugin source content for the edge agent."""
    plugin_root = Path("/project/.agents/agent/plugins")
    candidate = plugin_root / plugin_name
    if candidate.exists():
        return candidate.read_text(encoding="utf-8")

    fallback = plugin_root / f"{plugin_name}.py"
    if fallback.exists():
        return fallback.read_text(encoding="utf-8")

    return None


@router.post("/{agent_id}/bundle/download")
@router.get("/{agent_id}/bundle/download")
async def download_edge_bundle(
    agent_id: int,
    x_agent_api_key: str | None = Header(None, alias="X-Agent-API-Key"),
    authorization: str | None = Header(None, alias="Authorization"),
    db: Session = Depends(get_db),
    service: AgentService = Depends(get_agent_service),
):
    """Serve the current agent bundle ZIP for self-update."""
    api_key = _resolve_api_key(x_agent_api_key, authorization)
    agent = await service.authenticate_agent(db, api_key)
    if agent.id != agent_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Agent ID mismatch")

    bundle_path = Path("/project/.agents/agent-bundle-live.zip")
    if not bundle_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bundle not found")

    version_path = bundle_path.with_suffix(".version")
    version = version_path.read_text(encoding="utf-8").strip() if version_path.exists() else ""
    versioned_name = f"agent-bundle-{version}.zip" if version else "agent-bundle-live.zip"
    response = FileResponse(
        path=str(bundle_path),
        media_type="application/zip",
        filename=versioned_name,
    )
    if version:
        response.headers["X-Agent-Bundle-Version"] = version
    return response
