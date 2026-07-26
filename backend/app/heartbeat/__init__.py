"""
Mission Control Heartbeat Service

Dedicated service responsible for all heartbeat processing.
Every heartbeat flows through this service — no direct processing
in routers or other services.

Responsibilities:
    - Receive heartbeat from agent
    - Update agent last seen / online status
    - Update agent version / metrics / health
    - Queue pending commands for delivery
    - Return commands to execute
    - Trigger automation events
    - Publish heartbeat events to the event bus
    - Sync remote target updates
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.events import Event, EventType, event_bus
from app.models.db.agent import Agent as Agent
from app.repositories.agent_repository import AgentCommandRepository, AgentRepository
from app.schemas.agent import (
    AgentHeartbeatResponse,
    AgentPendingCommand,
)
from app.state import AgentState, agent_state_engine

logger = logging.getLogger(__name__)


class HeartbeatService:
    """Processes all agent heartbeats through a single pipeline."""

    async def process_heartbeat(
        self,
        db: Session,
        agent_id: int,
        health: str | None = None,
        cpu_percent: float | None = None,
        memory_percent: float | None = None,
        disk_percent: float | None = None,
        agent_version: str | None = None,
        active_plugins: str | None = None,
        api_key: str | None = None,
    ) -> AgentHeartbeatResponse:
        """Process a heartbeat and return pending commands + remote targets."""

        # 1. Authenticate and fetch agent
        agent = AgentRepository.get_by_id(db, agent_id)
        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found",
            )

        if api_key and agent.api_key != api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key mismatch",
            )

        # 2. Update agent state
        old_status = agent.status
        AgentRepository.update(
            db,
            agent.id,
            status="online",
            last_heartbeat=datetime.now(UTC),
            health=health,
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            disk_percent=disk_percent,
            agent_version=agent_version,
            active_plugins=active_plugins,
        )

        # 3. Update state engine
        agent.status = "online"
        agent.last_heartbeat = datetime.now(UTC)
        agent.health = health
        new_state = agent_state_engine.get_state(agent)
        agent_state_engine.update_state(db, agent.id, new_state)

        # 4. Publish heartbeat event
        await event_bus.publish(
            Event(
                type=EventType.HEARTBEAT_RECEIVED,
                data={
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "health": health,
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "disk_percent": disk_percent,
                    "agent_version": agent_version,
                    "state": new_state.value,
                },
                source="heartbeat_service",
            )
        )

        # 5. Publish online/offline transition events
        if old_status != "online" and agent.status == "online":
            await event_bus.publish(
                Event(
                    type=EventType.AGENT_ONLINE,
                    data={"agent_id": agent.id, "agent_name": agent.name},
                    source="heartbeat_service",
                )
            )

        # 6. Fetch pending commands
        pending_commands = AgentCommandRepository.get_pending_for_agent(db, agent.id)
        commands = []
        for cmd in pending_commands:
            AgentCommandRepository.update(
                db, cmd.id, status="dispatched", started_at=datetime.now(UTC)
            )
            commands.append(
                AgentPendingCommand(
                    id=cmd.id,
                    command_type=cmd.command_type,
                    command=cmd.command,
                    timeout=cmd.timeout,
                    file_path=cmd.file_path,
                    file_name=cmd.file_name,
                    file_content_b64=cmd.file_content_b64,
                )
            )

            # Publish command dispatched event
            await event_bus.publish(
                Event(
                    type=EventType.COMMAND_DISPATCHED,
                    data={
                        "agent_id": agent.id,
                        "command_id": cmd.id,
                        "command_type": cmd.command_type,
                    },
                    source="heartbeat_service",
                )
            )

        # 7. Fetch remote targets
        remote_targets = self._get_remote_targets(db, agent.id)

        return AgentHeartbeatResponse(
            commands=commands if commands else None,
            heartbeat_interval=agent.heartbeat_interval,
            remote_targets=remote_targets if remote_targets else None,
        )

    def _get_remote_targets(self, db: Session, agent_id: int) -> list[dict]:
        """Fetch enabled remote targets with decrypted credentials."""
        from app.core.config import get_settings
        from app.core.security import CredentialCipher
        from app.repositories.agent_remote_target_repository import (
            AgentRemoteTargetRepository,
        )

        settings = get_settings()
        cipher = CredentialCipher(settings.missioncontrol_secret_key)
        targets = AgentRemoteTargetRepository.get_enabled_by_agent_id(db, agent_id)

        result = []
        for t in targets:
            target_dict = {
                "id": t.id,
                "name": t.name,
                "hostname": t.hostname,
                "protocol": t.protocol,
                "port": t.port,
                "username": t.username,
                "password": (
                    cipher.decrypt(t.password_encrypted)
                    if t.password_encrypted
                    else None
                ),
                "ssh_key": (
                    cipher.decrypt(t.ssh_key_encrypted)
                    if t.ssh_key_encrypted
                    else None
                ),
            }
            result.append(target_dict)
        return result

    async def mark_agent_offline(self, db: Session, agent_id: int) -> None:
        """Mark an agent as offline and publish event."""
        AgentRepository.update(db, agent_id, status="offline")
        agent = AgentRepository.get_by_id(db, agent_id)
        if agent:
            agent_state_engine.update_state(db, agent_id, AgentState.OFFLINE)

        await event_bus.publish(
            Event(
                type=EventType.AGENT_OFFLINE,
                data={"agent_id": agent_id},
                source="heartbeat_service",
            )
        )


# Global singleton
heartbeat_service = HeartbeatService()
