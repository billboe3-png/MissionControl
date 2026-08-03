"""
Mission Control Agent Active Directory Provider

Reads Active Directory data from agent-collected inventory
stored in Agent.inventory_json.  Implements ActiveDirectoryProvider
so the existing AD pages work transparently for agent-relayed hosts.
"""

import json
import logging

from .base_provider import ActiveDirectoryProvider

logger = logging.getLogger(__name__)


class AgentActiveDirectoryProvider(ActiveDirectoryProvider):
    """Active Directory provider backed by agent inventory data."""

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
            "message": "Agent-relayed Active Directory data",
            "server": self._hostname,
        }

    async def get_summary(self) -> dict:
        users = self._get_items("users")
        groups = self._get_items("groups")
        devices = self._get_items("devices")
        return {
            "connected": True,
            "domain": self._inventory.get("domain", self._hostname),
            "forest": self._inventory.get("forest", ""),
            "users": len(users),
            "groups": len(groups),
            "devices": len(devices),
            "enabled_users": sum(1 for u in users if not u.get("disabled", False)),
            "disabled_users": sum(1 for u in users if u.get("disabled", False)),
            "domain_controllers": len(self._get_items("domain_controllers")),
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
            "server": self._hostname,
            "domain": self._inventory.get("domain", self._hostname),
        }

    async def reset_password(self, sam_account_name: str, new_password: str) -> dict:
        return {"success": False, "error": "Agent-relayed AD provider is read-only"}

    async def unlock_account(self, sam_account_name: str) -> dict:
        return {"success": False, "error": "Agent-relayed AD provider is read-only"}

    async def enable_account(self, sam_account_name: str) -> dict:
        return {"success": False, "error": "Agent-relayed AD provider is read-only"}

    async def disable_account(self, sam_account_name: str) -> dict:
        return {"success": False, "error": "Agent-relayed AD provider is read-only"}

    async def rename_user(self, sam_account_name: str, new_display_name: str, new_first_name: str | None = None, new_last_name: str | None = None) -> dict:
        return {"success": False, "error": "Agent-relayed AD provider is read-only"}

    async def get_user_groups(self, sam_account_name: str) -> dict:
        return {"success": False, "error": "Agent-relayed AD provider is read-only"}

    async def add_to_group(self, sam_account_name: str, group_name: str) -> dict:
        return {"success": False, "error": "Agent-relayed AD provider is read-only"}

    async def remove_from_group(self, sam_account_name: str, group_name: str) -> dict:
        return {"success": False, "error": "Agent-relayed AD provider is read-only"}
