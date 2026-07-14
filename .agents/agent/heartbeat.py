"""Mission Control Agent - Heartbeat system."""

import asyncio
import logging

from agent.client import AgentClient
from agent.config import AgentSettings

logger = logging.getLogger("mc-agent")


class HeartbeatManager:
    """Manages periodic heartbeats to Mission Control server."""

    def __init__(self, client: AgentClient, config: AgentSettings):
        self.client = client
        self.config = config
        self._running = False

    async def send_heartbeat(
        self,
        agent_id: int,
        health: str = "healthy",
        cpu_percent: float | None = None,
        memory_percent: float | None = None,
        disk_percent: float | None = None,
        agent_version: str | None = None,
        active_plugins: str | None = None,
    ) -> dict:
        """Send a single heartbeat and receive pending commands."""
        payload = {
            "agent_id": agent_id,
            "health": health,
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "disk_percent": disk_percent,
            "agent_version": agent_version,
            "active_plugins": active_plugins,
        }

        try:
            result = await self.client.post(
                "/api/v1/agents/heartbeat", payload
            )
            logger.debug(
                "Heartbeat sent for agent %d, %d pending commands",
                agent_id,
                len(result.get("commands") or []),
            )
            return result
        except Exception as e:
            logger.warning("Heartbeat failed: %s", e)
            raise
