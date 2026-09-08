"""Agent-relay execution for MikroTik servers.

When a MikroTik server is not directly reachable from the Mission
Control host (e.g. a cloud server managing LAN devices), commands can
be relayed through an on-site edge agent. The plugin auto-provisions an
``AgentRemoteTarget`` (SSH) on the chosen agent and dispatches RouterOS
CLI commands via the ``remote_execute`` command type; the agent runs
them over SSH from inside the device's network.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time

from sqlalchemy.orm import Session

from app.models.db.agent import Agent
from app.models.db.agent_remote_target import AgentRemoteTarget
from app.plugins.installed.official_mikrotik.service_types import CommandResult
from app.repositories.agent_remote_target_repository import AgentRemoteTargetRepository
from app.repositories.agent_repository import AgentCommandRepository

logger = logging.getLogger("plugin.mikrotik.relay")

DISPATCH_TIMEOUT_S = 120
WAIT_DEADLINE_S = 150.0
POLL_INTERVAL_S = 1.0
MISSING_CONNECTOR_GRACE_S = 35.0
RELAY_PLUGIN_TAG = "mikrotik"


def _merge_plugin(existing: str | None, plugin: str) -> str:
    parts = [p.strip() for p in (existing or "").split(",") if p.strip()]
    if plugin not in parts:
        parts.append(plugin)
    return ",".join(parts)


def provision_remote_target(
    db: Session,
    server,  # MikroTikServer
    password_encrypted: str | None,
) -> int:
    """Create or refresh the AgentRemoteTarget used to reach this server.

    Returns the target id and stores it on the MikroTikServer row.
    """
    fields = {
        "name": f"mikrotik-{server.name}",
        "hostname": server.host,
        "protocol": "ssh",
        "port": server.ssh_port or 22,
        "username": server.username,
        "enabled": True,
    }
    if password_encrypted:
        fields["password_encrypted"] = password_encrypted

    if server.remote_target_id:
        target = AgentRemoteTargetRepository.get_by_id(db, server.remote_target_id)
        if target is not None and target.agent_id == server.relay_agent_id:
            fields["target_plugins"] = _merge_plugin(
                getattr(target, "target_plugins", None), RELAY_PLUGIN_TAG
            )
            AgentRemoteTargetRepository.update(db, target.id, **fields)
            db.flush()
            return target.id

    fields["target_plugins"] = RELAY_PLUGIN_TAG
    target = AgentRemoteTargetRepository.create(db, agent_id=server.relay_agent_id, **fields)
    db.flush()
    server.remote_target_id = target.id
    return target.id


def delete_remote_target(db: Session, server) -> None:  # MikroTikServer
    """Remove the remote target auto-provisioned for this server."""
    if not server.remote_target_id:
        return
    with_target = (
        db.query(AgentRemoteTarget).filter(AgentRemoteTarget.id == server.remote_target_id).first()
    )
    if with_target is not None and with_target.name == f"mikrotik-{server.name}":
        AgentRemoteTargetRepository.delete(db, with_target.id)
    server.remote_target_id = None


class MikroTikRelayExecutor:
    """Dispatches RouterOS commands through an agent's SSH connector."""

    async def execute_via_agent(
        self,
        db: Session,
        server,  # MikroTikServer
        command: str,
        executed_by: str | None = None,
        poll_interval: float = POLL_INTERVAL_S,
        wait_deadline: float | None = None,
    ) -> CommandResult:
        result = await self._dispatch_and_wait(
            db, server, command, executed_by, poll_interval, wait_deadline
        )
        # A freshly provisioned target reaches the agent on its next
        # heartbeat; retry once if the command outraced the target sync.
        if (
            not result.success
            and "no connector for target" in (result.error or "").lower()
        ):
            logger.info(
                "Agent has not learned target %s yet; retrying after grace period",
                server.remote_target_id,
            )
            await asyncio.sleep(MISSING_CONNECTOR_GRACE_S)
            result = await self._dispatch_and_wait(
                db, server, command, executed_by, poll_interval, wait_deadline
            )
        return result

    async def _dispatch_and_wait(
        self,
        db: Session,
        server,  # MikroTikServer
        command: str,
        executed_by: str | None,
        poll_interval: float,
        wait_deadline: float | None,
    ) -> CommandResult:
        result = CommandResult(success=False)
        started = time.monotonic()
        deadline = wait_deadline if wait_deadline is not None else WAIT_DEADLINE_S

        agent = db.get(Agent, server.relay_agent_id) if server.relay_agent_id else None
        if agent is None:
            result.error = "Relay agent not found"
            return result
        if agent.status != "online":
            result.error = f"Relay agent '{agent.name}' is {agent.status}"
            return result
        if not server.remote_target_id:
            result.error = "No remote target provisioned for this server"
            return result

        cmd = AgentCommandRepository.create(
            db=db,
            agent_id=agent.id,
            command_type="remote_execute",
            command=json.dumps({
                "command": command,
                "target_id": server.remote_target_id,
            }),
            timeout=DISPATCH_TIMEOUT_S,
            requested_by=executed_by or "mikrotik-plugin",
        )
        db.commit()
        logger.info(
            "Relayed MikroTik command via agent %s target %s (command id %s)",
            agent.name,
            server.remote_target_id,
            cmd.id,
        )

        while True:
            await asyncio.sleep(poll_interval)
            # The result is committed by the agent's own request/session;
            # expire the cached instance so the re-fetch sees fresh values.
            db.expire(cmd)
            current = AgentCommandRepository.get_by_id(db, cmd.id)
            if current is not None and current.status in ("completed", "failed"):
                output = current.stdout or ""
                stderr = current.stderr or ""
                exit_code = current.exit_code if current.exit_code is not None else -1
                result.success = bool(current.success) and exit_code == 0
                result.output = output
                result.error = "" if result.success else (stderr or f"exit code {exit_code}")
                return result
            if time.monotonic() - started > deadline:
                result.error = (
                    f"Timed out waiting for agent '{agent.name}' "
                    "to report the command result"
                )
                return result


relay_executor = MikroTikRelayExecutor()
