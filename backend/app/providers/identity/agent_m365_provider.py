"""
Mission Control Agent Microsoft 365 Provider

Reads Microsoft 365 data from agent-collected inventory
stored in Agent.inventory_json.  Implements Microsoft365Provider
so the existing M365 pages work transparently for agent-relayed hosts.
"""

import json
import logging

from .base_provider import Microsoft365Provider

logger = logging.getLogger(__name__)


class AgentMicrosoft365Provider(Microsoft365Provider):
    """Microsoft 365 provider backed by agent inventory data."""

    def __init__(self, inventory: dict, hostname: str = "agent") -> None:
        self._inventory = inventory or {}
        self._hostname = hostname

    def _get_items(self, key: str) -> list[dict]:
        raw = self._inventory.get(key, [])
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                raw = []
        if isinstance(raw, dict):
            raw = [raw]
        return raw

    async def test_connection(self) -> dict:
        return {
            "connected": True,
            "message": "Agent-relayed Microsoft 365 data",
            "tenant": self._inventory.get("tenant", self._hostname),
        }

    async def get_summary(self) -> dict:
        users = self._get_items("users")
        groups = self._get_items("groups")
        devices = self._get_items("devices")
        return {
            "connected": True,
            "tenant": self._inventory.get("tenant", self._hostname),
            "domains": len(self._get_items("domains")),
            "users": len(users),
            "groups": len(groups),
            "devices": len(devices),
            "licensed_users": sum(1 for u in users if u.get("is_licensed", False)),
            "service_health": self._inventory.get("service_health", {}),
        }

    async def get_users(self) -> dict:
        users = self._get_items("users")
        return {"connected": True, "count": len(users), "items": users}

    async def get_groups(self) -> dict:
        groups = self._get_items("groups")
        return {"connected": True, "count": len(groups), "items": groups}

    async def get_devices(self) -> dict:
        devices = self._get_items("devices")
        return {"connected": True, "count": len(devices), "items": devices}

    async def get_health(self) -> dict:
        return {
            "connected": True,
            "status": "healthy",
            "tenant": self._inventory.get("tenant", self._hostname),
        }
