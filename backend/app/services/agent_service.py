"""
Mission Control Agent Service

Business logic for agent management: registration, heartbeat processing,
command dispatch, inventory updates, and file transfer.
"""

import base64
import hashlib
import os
import json
import logging
import secrets
from datetime import UTC, datetime

from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.db.agent import Agent
from app.models.db.agent_remote_target import AgentRemoteTarget
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
            ip_address=data.ip_address,
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
            profile = json.loads(cmd.integration_profile) if cmd.integration_profile else None
            commands.append(
                AgentPendingCommand(
                    id=cmd.id,
                    command_type=cmd.command_type,
                    command=cmd.command,
                    timeout=cmd.timeout,
                    file_path=cmd.file_path,
                    file_name=cmd.file_name,
                    file_content_b64=cmd.file_content_b64,
                    integration_profile=profile,
                )
            )

        remote_targets = self._get_remote_targets_for_agent(db, agent.id)

        return AgentHeartbeatResponse(
            commands=commands if commands else None,
            heartbeat_interval=agent.heartbeat_interval,
            remote_targets=remote_targets if remote_targets else None,
            active_plugins=(agent.enabled_plugins or agent.active_plugins),
            pending_plugins=self._pending_plugins(
                agent.enabled_plugins, data.active_plugins
            ),
            integration_profiles=self._integration_profiles_for_agent(db, agent.id),
            plugin_updates=self._plugin_updates_for_agent(db, agent.id),
        )

    @staticmethod
    def _pending_plugins(
        enabled_plugins: str | None, active_plugins: str | None
    ) -> list[str]:
        """Return server-selected plugins the agent has not yet reported active."""
        enabled = {p.strip() for p in (enabled_plugins or "").split(",") if p.strip()}
        active = {p.strip() for p in (active_plugins or "").split(",") if p.strip()}
        return sorted(enabled - active)

    def _get_remote_targets_for_agent(
        self, db: Session, agent_id: int
    ) -> list[dict]:
        """Fetch enabled remote targets with decrypted credentials."""
        from app.core.config import get_settings
        from app.core.security import CredentialCipher
        from app.repositories.agent_remote_target_repository import (
            AgentRemoteTargetRepository,
        )

        settings = get_settings()
        cipher = CredentialCipher(settings.missioncontrol_secret_key)
        targets = AgentRemoteTargetRepository.get_enabled_by_agent_id(
            db, agent_id
        )

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
                "tags": t.tags,
            }
            result.append(target_dict)

        return result

    def _integration_profiles_for_agent(
        self, db: Session, agent_id: int
    ) -> list[dict]:
        """Return enabled integration profiles relevant to this agent."""
        from app.repositories.integration_profile_repository import (
            IntegrationProfileRepository,
        )
        from app.models.db.agent import Agent

        agent = db.get(Agent, agent_id)
        if agent is None:
            return []

        profiles = IntegrationProfileRepository.get_all_enabled_by_type(db, "veeam")
        result = []
        cipher = _get_cipher()
        for p in profiles:
            data = {
                "id": p.id,
                "name": p.name,
                "integration_type": p.integration_type,
                "base_url": p.base_url,
                "username": p.username,
                "password": cipher.decrypt(p.encrypted_secret) if p.encrypted_secret else None,
                "verify_ssl": p.verify_ssl if p.verify_ssl is not None else True,
                "timeout": p.timeout,
                "data_source": p.data_source,
                "ssh_host": p.ssh_host,
                "ssh_port": p.ssh_port,
                "ssh_username": p.ssh_username,
                "ssh_password": cipher.decrypt(p.ssh_password_encrypted) if p.ssh_password_encrypted else None,
            }
            result.append(data)
        return result

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
            integration_profile=json.dumps(data.integration_profile) if data.integration_profile is not None else None,
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

        remote_targets = inventory_data.get("remote_targets", {})
        if remote_targets:
            self._sync_remote_target_status(db, agent_id, remote_targets)

        return {"received": True, "message": "Inventory updated"}

    def _sync_remote_target_status(
        self,
        db: Session,
        agent_id: int,
        remote_targets: dict,
    ) -> None:
        """Sync last_collected_at / last_status from agent inventory data."""
        targets = (
            db.query(AgentRemoteTarget)
            .filter(AgentRemoteTarget.agent_id == agent_id)
            .all()
        )
        for t in targets:
            key = f"target-{t.id}"
            data = remote_targets.get(key)
            if data is None:
                continue
            collected_at = data.get("collected_at")
            if collected_at:
                try:
                    t.last_collected_at = datetime.fromisoformat(collected_at)
                except (ValueError, TypeError):
                    t.last_collected_at = datetime.now(UTC)
            t.last_status = data.get("status", "unknown")
            t.last_error = data.get("error")
        db.commit()

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

    async def get_remote_inventory(
        self, db: Session, agent_id: int
    ) -> dict:
        """Get remote target inventory from an agent's latest inventory."""
        agent = AgentRepository.get_by_id(db, agent_id)
        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found",
            )

        if not agent.inventory_json:
            return {
                "agent_id": agent.id,
                "agent_name": agent.name,
                "hostname": agent.hostname,
                "remote_targets": {},
            }

        try:
            inventory = json.loads(agent.inventory_json)
        except json.JSONDecodeError:
            return {
                "agent_id": agent.id,
                "agent_name": agent.name,
                "hostname": agent.hostname,
                "remote_targets": {},
            }

        return {
            "agent_id": agent.id,
            "agent_name": agent.name,
            "hostname": agent.hostname,
            "remote_targets": inventory.get("remote_targets", {}),
        }

    def get_plugin_file(
        self, db: Session, agent_id: int, plugin_name: str
    ) -> dict:
        """Return plugin file content for agent-side installation."""
        agent = AgentRepository.get_by_id(db, agent_id)
        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found",
            )

        mapping = {
            "docker": "docker_plugin.py",
            "linux": "linux_plugin.py",
            "hyperv": "hyperv_plugin.py",
            "windows": "windows_plugin.py",
            "zabbix": "zabbix_plugin.py",
            "active_directory": "ad_plugin.py",
            "microsoft_365": "m365_plugin.py",
            "veeam": "veeam_plugin.py",
            "proxmox": "proxmox_plugin.py",
            "windows_docker": "windows_docker_plugin.py",
        }
        file_name = mapping.get(plugin_name)
        if not file_name:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unknown plugin",
            )

        plugin_root = Path(
            os.environ.get("PROJECT_DIR", "/project")
        ).resolve() / ".agents" / "agent" / "plugins"
        plugin_file = plugin_root / file_name
        if not plugin_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plugin file not found",
            )

        content = plugin_file.read_text(encoding="utf-8")
        return {
            "plugin_name": plugin_name,
            "file_name": file_name,
            "content": content,
        }

    # ------------------------------------------------------------------ #
    # CRUD                                                                #
    # ------------------------------------------------------------------ #

    # ------------------------------------------------------------------ #
    # Fleet Summary                                                       #
    # ------------------------------------------------------------------ #

    async def get_fleet_summary(self, db: Session) -> dict:
        """Return a comprehensive fleet summary for dashboard consumption."""
        try:
            agents = db.execute(select(Agent)).scalars().all()
            total = len(agents)

            status_counts: dict[str, int] = {}
            os_counts: dict[str, int] = {}
            version_counts: dict[str, int] = {}
            company_counts: dict[str, int] = {}
            site_counts: dict[str, int] = {}
            health_counts: dict[str, int] = {}
            heartbeat_latencies: list[float] = []
            recent_failures = 0
            update_up_to_date = 0
            update_available = 0

            now = datetime.now(UTC)

            for a in agents:
                st = a.status or "offline"
                status_counts[st] = status_counts.get(st, 0) + 1

                os_name = a.operating_system or "Unknown"
                os_counts[os_name] = os_counts.get(os_name, 0) + 1

                ver = a.agent_version or "unknown"
                version_counts[ver] = version_counts.get(ver, 0) + 1

                if a.company_id is not None:
                    key = str(a.company_id)
                    company_counts[key] = company_counts.get(key, 0) + 1

                if a.site_id is not None:
                    key = str(a.site_id)
                    site_counts[key] = site_counts.get(key, 0) + 1

                h = a.health or "unknown"
                health_counts[h] = health_counts.get(h, 0) + 1

                if a.last_heartbeat is not None:
                    hb_time = a.last_heartbeat
                    if hb_time.tzinfo is None:
                        hb_time = hb_time.replace(tzinfo=UTC)
                    latency = (now - hb_time).total_seconds()
                    heartbeat_latencies.append(latency * 1000)

            online = status_counts.get("online", 0)
            offline = status_counts.get("offline", 0)
            warning = status_counts.get("warning", 0)
            updating = status_counts.get("updating", 0)
            idle = health_counts.get("idle", 0)
            busy = health_counts.get("busy", 0)

            avg_latency = (
                round(sum(heartbeat_latencies) / len(heartbeat_latencies), 2)
                if heartbeat_latencies
                else 0.0
            )

            cmd_queue = 0
            try:
                from app.models.db.agent_command import AgentCommand

                cmd_queue = db.execute(
                    select(func.count()).select_from(
                        AgentCommand.__table__
                    ).where(AgentCommand.status == "pending")
                ).scalar() or 0
            except Exception:
                pass

            return {
                "total_agents": total,
                "online": online,
                "offline": offline,
                "warning": warning,
                "updating": updating,
                "idle": idle,
                "busy": busy,
                "by_os": os_counts,
                "by_version": version_counts,
                "by_company": company_counts,
                "by_site": site_counts,
                "avg_heartbeat_latency_ms": avg_latency,
                "command_queue_depth": cmd_queue,
                "recent_failures": recent_failures,
                "inventory_age_hours": 0.0,
                "update_status": {
                    "up_to_date": update_up_to_date,
                    "update_available": update_available,
                },
            }
        except Exception as e:
            logger.warning("Fleet summary failed: %s", e)
            return {
                "total_agents": 0,
                "online": 0,
                "offline": 0,
                "warning": 0,
                "updating": 0,
                "idle": 0,
                "busy": 0,
                "by_os": {},
                "by_version": {},
                "by_company": {},
                "by_site": {},
                "avg_heartbeat_latency_ms": 0.0,
                "command_queue_depth": 0,
                "recent_failures": 0,
                "inventory_age_hours": 0.0,
                "update_status": {"up_to_date": 0, "update_available": 0},
            }

    async def get_agent_health_history(
        self, db: Session, agent_id: int, hours: int = 24
    ) -> list[dict]:
        """Return health data points for an agent over a time window."""
        try:
            from datetime import timedelta

            from app.models.db.agent_health import AgentHealth

            cutoff = datetime.now(UTC) - timedelta(hours=hours)

            rows = (
                db.execute(
                    select(AgentHealth)
                    .where(AgentHealth.agent_id == agent_id)
                    .where(AgentHealth.recorded_at >= cutoff)
                    .order_by(desc(AgentHealth.recorded_at))
                    .limit(288)
                )
                .scalars()
                .all()
            )

            return [
                {
                    "recorded_at": r.recorded_at.isoformat()
                    if r.recorded_at
                    else None,
                    "health": r.health,
                    "cpu_percent": r.cpu_percent,
                    "memory_percent": r.memory_percent,
                    "disk_percent": r.disk_percent,
                }
                for r in rows
            ]
        except ImportError:
            logger.debug("AgentHealth model not available")
            return []
        except Exception as e:
            logger.warning(
                "Health history for agent %d failed: %s", agent_id, e,
            )
            return []

    # ------------------------------------------------------------------ #
    # CRUD (continued)                                                    #
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

    async def get_dashboard_summary(self, db: Session) -> dict:
        """Dashboard-friendly agent summary. Never raises."""
        try:
            from sqlalchemy import func, select

            row = db.execute(
                select(
                    func.count(Agent.id).label("total"),
                    func.count(Agent.id).filter(Agent.status == "online").label("online"),
                    func.avg(Agent.cpu_percent).filter(
                        Agent.status == "online", Agent.cpu_percent.isnot(None)
                    ).label("avg_cpu"),
                    func.avg(Agent.memory_percent).filter(
                        Agent.status == "online", Agent.memory_percent.isnot(None)
                    ).label("avg_mem"),
                )
            ).one()

            total = row.total or 0
            online = row.online or 0
            avg_cpu = row.avg_cpu
            avg_mem = row.avg_mem

            return {
                "total": total,
                "online": online,
                "offline": total - online,
                "avg_cpu": round(float(avg_cpu), 1) if avg_cpu else 0,
                "avg_memory": round(float(avg_mem), 1) if avg_mem else 0,
            }
        except Exception as e:
            logger.warning("Dashboard: agent summary failed: %s", e)
            return {
                "total": 0,
                "online": 0,
                "offline": 0,
                "avg_cpu": 0,
                "avg_memory": 0,
            }

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

    async def reveal_api_key(
        self, db: Session, agent_id: int
    ) -> dict:
        """Return the stored API key for the agent."""
        agent = AgentRepository.get_by_id(db, agent_id)
        if agent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found",
            )
        return {"agent_id": agent.id, "api_key": agent.api_key}

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
            enabled_plugins=agent.enabled_plugins,
            api_key_masked=f"mc_agent_...{agent.api_key[-6:]}" if agent.api_key else None,
            created_at=agent.created_at,
            updated_at=agent.updated_at,
            registered_at=agent.registered_at,
        )
        return response


    def _plugin_updates_for_agent(
        self, db: Session, agent_id: int
    ) -> dict[str, str] | None:
        """Return base64-encoded plugin files that differ from deployed versions."""
        from app.repositories.agent_repository import AgentRepository

        agent = AgentRepository.get_by_id(db, agent_id)
        if agent is None:
            return None

        plugin_root = (
            Path(os.environ.get("PROJECT_DIR", "/project")).resolve()
            / ".agents"
            / "agent"
            / "plugins"
        )
        updates: dict[str, str] = {}
        for plugin_name in ["veeam"]:
            file_name = f"{plugin_name}_plugin.py"
            plugin_file = plugin_root / file_name
            if not plugin_file.exists():
                continue
            content = plugin_file.read_text(encoding="utf-8")
            updates[plugin_name] = base64.b64encode(
                content.encode("utf-8")
            ).decode("utf-8")
        return updates or None


agent_service = AgentService()
