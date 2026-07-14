"""Mission Control Agent - Registration and authentication."""

import logging

from agent.client import AgentClient
from agent.config import AgentSettings

logger = logging.getLogger("mc-agent")


class RegistrationManager:
    """Handles agent registration with Mission Control server."""

    def __init__(self, client: AgentClient, config: AgentSettings):
        self.client = client
        self.config = config

    async def register(
        self,
        hostname: str,
        os_name: str,
        os_version: str,
        ip_address: str,
        agent_version: str,
    ) -> dict:
        """Register this agent with the Mission Control server."""
        payload = {
            "name": self.config.agent_name or hostname,
            "hostname": hostname,
            "operating_system": os_name,
            "os_version": os_version,
            "ip_address": ip_address,
            "agent_version": agent_version,
            "tags": None,
        }

        try:
            result = await self.client.post(
                "/api/v1/agents/register", payload
            )
            logger.info(
                "Registered as agent %d (api_key: %s...)",
                result["agent_id"],
                result["api_key"][:12],
            )
            return result
        except Exception as e:
            logger.error("Registration failed: %s", e)
            raise
