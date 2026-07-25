"""
Mission Control Agent Zabbix Provider

Reads Zabbix monitoring data from agent-collected inventory
stored in Agent.inventory_json.  Implements ZabbixProvider so the
existing Zabbix pages work transparently for agent-relayed hosts.
"""

import json
import logging

from .base_provider import ZabbixProvider

logger = logging.getLogger(__name__)


class AgentZabbixProvider(ZabbixProvider):
    """Zabbix provider backed by agent inventory data."""

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
            "message": "Agent-relayed Zabbix data",
            "version": "agent",
        }

    async def login(self) -> dict:
        return {"success": True}

    async def logout(self) -> dict:
        return {"success": True}

    async def get_summary(self) -> dict:
        hosts = self._get_items("hosts")
        triggers = self._get_items("triggers")
        problems = self._get_items("problems")
        enabled_hosts = sum(1 for h in hosts if h.get("status") == 0)
        disabled_hosts = sum(1 for h in hosts if h.get("status") == 1)
        return {
            "connected": True,
            "version": "agent",
            "hosts": len(hosts),
            "enabled_hosts": enabled_hosts,
            "disabled_hosts": disabled_hosts,
            "groups": len(self._get_items("host_groups")),
            "triggers": len(triggers),
            "problem_triggers": len(problems),
            "events": len(self._get_items("events")),
            "items": len(self._get_items("items")),
            "templates": len(self._get_items("templates")),
        }

    async def get_hosts(self) -> dict:
        hosts = self._get_items("hosts")
        return {"connected": True, "count": len(hosts), "items": hosts}

    async def get_host_groups(self) -> dict:
        groups = self._get_items("host_groups")
        return {"connected": True, "count": len(groups), "items": groups}

    async def get_triggers(self) -> dict:
        triggers = self._get_items("triggers")
        return {"connected": True, "count": len(triggers), "items": triggers}

    async def get_problems(self) -> dict:
        problems = self._get_items("problems")
        return {"connected": True, "count": len(problems), "items": problems}

    async def get_events(self) -> dict:
        events = self._get_items("events")
        return {"connected": True, "count": len(events), "items": events[:50]}

    async def get_items(self) -> dict:
        items = self._get_items("items")
        return {"connected": True, "count": len(items), "items": items[:100]}

    async def get_history(self) -> dict:
        return {"connected": True, "message": "History requires itemid parameter", "items": []}

    async def get_templates(self) -> dict:
        templates = self._get_items("templates")
        return {"connected": True, "count": len(templates), "items": templates}

    async def get_dashboards(self) -> dict:
        dashboards = self._get_items("dashboards")
        return {"connected": True, "count": len(dashboards), "items": dashboards}

    async def get_maps(self) -> dict:
        maps = self._get_items("maps")
        return {"connected": True, "count": len(maps), "items": maps}

    async def get_health(self) -> dict:
        return {
            "connected": True,
            "status": "healthy",
            "version": "agent",
        }
