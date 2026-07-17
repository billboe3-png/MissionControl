"""
Mission Control Agent Service

Business logic for agent management: registration, heartbeat processing,
command dispatch, inventory updates, and file transfer.
"""

import hashlib
import json
import logging
import secrets
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.db.agent import Agent
from app.repositories.agent_repository import (
    AgentCommandRepository,
    AgentRepository,
)
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
    AgentPendingCommand,
    AgentRegisterRequest,
    AgentRegisterResponse,
    AgentResponse,
    AgentUpdate,
)

logger = logging.getLogger(__name__)

AGENT_API_KEY_PREFIX = "mc_agent_"


def _generate_api_key() -> str:
    """Generate a secure API key for agent authentication."""
    random_bytes = secrets.token_hex(32)
    return f"{AGENT_API_KEY_PREFIX}{random_bytes}"


def _hash_api_key(api_key: str) -> str:
    """Hash an API key for storage comparison."""
    return hashlib.sha256(api_key.encode()).hexdigest()


class AgentService:
    """Service layer for agent management."""

    # ------------------------------------------------------------------ #
    # Registration                                                        #
    # ------------------------------------------------------------------ #

    async def register_agent(
        self,
        db: Session,
        data: AgentRegisterRequest,
        company_id: int | None = None,
        site_id: int | None = None,
    ) -> AgentRegisterResponse:
        """Register a new agent with Mission Control."""
        existing = AgentRepository.get_by_hostname(
            db, data.hostname
        )
        if existing is not None:
            existing_api_key = _generate_api_key()
            AgentRepository.update(
                db,
                existing.id,
                name=data.name,
                operating_system=data.operating_system,
                os_version=data.os_version,
                ip_address=data.ip_address,
                agent_version=data.agent_version,
                tags=data.tags,
                status="online",
                last_heartbeat=datetime.now(UTC),
                registered_at=datetime.now(UTC),
                api_key=existing_api_key,
            )
            return AgentRegisterResponse(
                agent_id=existing.id,
                api_key=existing_api_key,
                heartbeat_interval=existing.heartbeat_interval,
                message="Agent re-registered successfully",
            )

        api_key = _generate_api_key()
        agent = AgentRepository.create(
            db,
            name=data.name,
            hostname=data.hostname,
            api_key=api_key,
            company_id=company_id,
            site_id=site_id,
            operating_system=data.operating_system,
            os_version=data.os_version,
            ip_address=data.ip_address,
            agent_version=data.agent_version,
            tags=data.tags,
            status="online",
            last_heartbeat=datetime.now(UTC),
            registered_at=datetime.now(UTC),
        )

        logger.info(
            "Agent registered: %s (%s)", data.name, data.hostname
        )

        return AgentRegisterResponse(
            agent_id=agent.id,
            api_key=api_key,
            heartbeat_interval=agent.heartbeat_interval,
            message="Agent registered successfully",
        )

    # ------------------------------------------------------------------ #
    # Authentication                                                      #
    # ------------------------------------------------------------------ #

    async def authenticate_agent(
        self, db: Session, api_key: str
    ) -> Agent:
        """Validate an API key and return the associated agent."""
        if not api_key or not api_key.startswith(AGENT_API_KEY_PREFIX):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key format",
            )

        agent = AgentRepository.get_by_api_key(db, api_key)
        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
            )
        if not agent.enabled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Agent is disabled",
            )
        return agent

    # ------------------------------------------------------------------ #
    # Heartbeat                                                           #
    # ------------------------------------------------------------------ #

    async def process_heartbeat(
        self,
        db: Session,
        data: AgentHeartbeatRequest,
        api_key: str,
    ) -> AgentHeartbeatResponse:
        """Process heartbeat from an agent and return pending commands."""
        agent = AgentRepository.get_by_id(db, data.agent_id)
        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found",
            )

        if agent.api_key != api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key mismatch",
            )

        AgentRepository.update(
            db,
            agent.id,
            status="online",
            last_heartbeat=datetime.now(UTC),
            health=data.health,
            cpu_percent=data.cpu_percent,
            memory_percent=data.memory_percent,
            disk_percent=data.disk_percent,
            agent_version=data.agent_version,
            active_plugins=data.active_plugins,
        )

        pending_commands = AgentCommandRepository.get_pending_for_agent(
            db, agent.id
        )

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

        return AgentHeartbeatResponse(
            commands=commands if commands else None,
            heartbeat_interval=agent.heartbeat_interval,
        )

    # ------------------------------------------------------------------ #
    # Command Results                                                     #
    # ------------------------------------------------------------------ #

    async def report_command_result(
        self,
        db: Session,
        data: AgentCommandResultRequest,
        agent_id: int,
    ) -> AgentCommandResultResponse:
        """Record command execution result from an agent."""
        cmd = AgentCommandRepository.get_by_id(db, data.command_id)
        if cmd is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Command not found",
            )
        if cmd.agent_id != agent_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Command does not belong to this agent",
            )

        updates: dict = {
            "exit_code": data.exit_code,
            "stdout": data.stdout,
            "stderr": data.stderr,
            "success": data.success,
            "duration_ms": data.duration_ms,
            "error_message": data.error_message,
            "completed_at": datetime.now(UTC),
            "status": "completed" if data.success else "failed",
        }

        if data.file_content_b64:
            updates["file_content_b64"] = data.file_content_b64

        AgentCommandRepository.update(db, data.command_id, **updates)

        return AgentCommandResultResponse(
            received=True,
            message="Command result recorded",
        )

    # ------------------------------------------------------------------ #
    # Command Dispatch                                                    #
    # ------------------------------------------------------------------ #

    async def dispatch_command(
        self, db: Session, data: AgentCommandDispatchRequest
    ) -> AgentCommandResponse:
        """Dispatch a command to an agent for execution."""
        agent = AgentRepository.get_by_id(db, data.agent_id)
        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found",
            )

        if agent.status != "online":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agent is {agent.status}, cannot dispatch command",
            )

        cmd = AgentCommandRepository.create(
            db,
            agent_id=data.agent_id,
            command_type=data.command_type,
            command=data.command,
            timeout=data.timeout,
            file_path=data.file_path,
            file_name=data.file_name,
            file_content_b64=data.file_content_b64,
            requested_by=data.requested_by,
            status="pending",
        )

        logger.info(
            "Command %d dispatched to agent %s: %s",
            cmd.id,
            agent.name,
            data.command_type,
        )

        return AgentCommandResponse(
            id=cmd.id,
            agent_id=cmd.agent_id,
            command_type=cmd.command_type,
            command=cmd.command,
            status=cmd.status,
            timeout=cmd.timeout,
            requested_by=cmd.requested_by,
            created_at=cmd.created_at,
        )

    # ------------------------------------------------------------------ #
    # Inventory                                                           #
    # ------------------------------------------------------------------ #

    async def update_inventory(
        self,
        db: Session,
        agent_id: int,
        inventory_data: dict,
        api_key: str,
    ) -> dict:
        """Update agent inventory data."""
        agent = AgentRepository.get_by_id(db, agent_id)
        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found",
            )
        if agent.api_key != api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key mismatch",
            )

        inventory_json = json.dumps(inventory_data)
        AgentRepository.update(
            db,
            agent_id,
            inventory_json=inventory_json,
            updated_at=datetime.now(UTC),
        )

        return {"received": True, "message": "Inventory updated"}

    async def get_inventory(
        self, db: Session, agent_id: int
    ) -> AgentInventoryResponse:
        """Get current inventory for an agent."""
        agent = AgentRepository.get_by_id(db, agent_id)
        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found",
            )

        inventory = None
        if agent.inventory_json:
            try:
                inventory = json.loads(agent.inventory_json)
            except json.JSONDecodeError:
                inventory = None

        return AgentInventoryResponse(
            agent_id=agent.id,
            agent_name=agent.name,
            hostname=agent.hostname,
            operating_system=agent.operating_system,
            os_version=agent.os_version,
            cpu_percent=agent.cpu_percent,
            memory_percent=agent.memory_percent,
            disk_percent=agent.disk_percent,
            inventory=inventory,
        )

    # ------------------------------------------------------------------ #
    # CRUD                                                                #
    # ------------------------------------------------------------------ #

    async def list_agents(
        self, db: Session
    ) -> AgentListResponse:
        """List all agents with online/offline counts."""
        agents = AgentRepository.get_all(db)
        online = sum(1 for a in agents if a.status == "online")
        offline = len(agents) - online
        return AgentListResponse(
            count=len(agents),
            online=online,
            offline=offline,
            items=[self._to_response(a) for a in agents],
        )

    async def get_agent(
        self, db: Session, agent_id: int
    ) -> AgentResponse:
        """Get a single agent."""
        agent = AgentRepository.get_by_id(db, agent_id)
        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found",
            )
        return self._to_response(agent)

    async def update_agent(
        self, db: Session, agent_id: int, data: AgentUpdate
    ) -> AgentResponse:
        """Update agent settings."""
        updates = data.model_dump(exclude_unset=True)
        agent = AgentRepository.update(db, agent_id, **updates)
        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found",
            )
        return self._to_response(agent)

    async def delete_agent(
        self, db: Session, agent_id: int
    ) -> None:
        """Delete an agent."""
        deleted = AgentRepository.delete(db, agent_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found",
            )

    async def enable_agent(
        self, db: Session, agent_id: int
    ) -> AgentResponse:
        """Enable an agent."""
        agent = AgentRepository.update(db, agent_id, enabled=True)
        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found",
            )
        return self._to_response(agent)

    async def disable_agent(
        self, db: Session, agent_id: int
    ) -> AgentResponse:
        """Disable an agent."""
        agent = AgentRepository.update(db, agent_id, enabled=False)
        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found",
            )
        return self._to_response(agent)

    # ------------------------------------------------------------------ #
    # Command History                                                     #
    # ------------------------------------------------------------------ #

    async def get_commands(
        self,
        db: Session,
        agent_id: int | None = None,
        status_filter: str | None = None,
        limit: int = 50,
    ) -> AgentCommandListResponse:
        """List commands with optional filters."""
        if agent_id:
            commands = AgentCommandRepository.get_by_agent(
                db, agent_id, limit
            )
        else:
            commands = AgentCommandRepository.get_all(
                db, limit, status=status_filter
            )
        return AgentCommandListResponse(
            count=len(commands),
            items=[
                AgentCommandResponse.model_validate(c) for c in commands
            ],
        )

    async def get_agent_commands(
        self, db: Session, agent_id: int
    ) -> AgentCommandListResponse:
        """Get command history for a specific agent."""
        agent = AgentRepository.get_by_id(db, agent_id)
        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found",
            )
        commands = AgentCommandRepository.get_by_agent(db, agent_id)
        return AgentCommandListResponse(
            count=len(commands),
            items=[
                AgentCommandResponse.model_validate(c) for c in commands
            ],
        )

    # ------------------------------------------------------------------ #
    # Stale Agent Detection                                               #
    # ------------------------------------------------------------------ #

    async def mark_stale_agents_offline(
        self, db: Session
    ) -> int:
        """Mark agents as offline if they haven't sent a heartbeat."""
        stale = AgentRepository.get_stale_agents(
            db, threshold_seconds=120
        )
        count = 0
        for agent in stale:
            AgentRepository.update(db, agent.id, status="offline")
            count += 1
        return count

    # ------------------------------------------------------------------ #
    # Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _to_response(self, agent: Agent) -> AgentResponse:
        """Convert an ORM agent to a response."""
        return AgentResponse(
            id=agent.id,
            name=agent.name,
            hostname=agent.hostname,
            status=agent.status,
            operating_system=agent.operating_system,
            os_version=agent.os_version,
            ip_address=agent.ip_address,
            agent_version=agent.agent_version,
            enabled=agent.enabled,
            health=agent.health,
            cpu_percent=agent.cpu_percent,
            memory_percent=agent.memory_percent,
            disk_percent=agent.disk_percent,
            last_heartbeat=agent.last_heartbeat,
            heartbeat_interval=agent.heartbeat_interval,
            tags=agent.tags,
            notes=agent.notes,
            active_plugins=agent.active_plugins,
            created_at=agent.created_at,
            updated_at=agent.updated_at,
            registered_at=agent.registered_at,
        )


agent_service = AgentService()
