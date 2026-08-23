"""Mission Control Agent - Zabbix monitoring plugin."""

import logging
import os
from typing import Any

from agent.plugin import AgentPlugin

logger = logging.getLogger("mc-agent")


class ZabbixPlugin(AgentPlugin):
    """Zabbix monitoring data collector plugin."""

    name = "zabbix"
    version = "1.0.0"
    description = "Zabbix monitoring data collector"
    platform_required = None

    def __init__(self):
        self._context: dict[str, Any] = {}
        self._base_url = ""
        self._username = ""
        self._password = ""
        self._auth_token = ""
        self._req_id = 1

    async def initialize(self, context: dict[str, Any]) -> bool:
        self._context = context
        self._base_url = os.environ.get("MC_ZABBIX_URL", "")
        self._username = os.environ.get("MC_ZABBIX_USERNAME", "")
        self._password = os.environ.get("MC_ZABBIX_PASSWORD", "")
        if self._base_url and self._username and self._password:
            logged_in = await self._jsonrpc("user.login", {
                "username": self._username,
                "password": self._password,
            })
            if logged_in and logged_in.get("result"):
                self._auth_token = logged_in["result"]
                logger.info("Zabbix plugin authenticated")
                return True
            logger.warning("Zabbix plugin auth failed")
            return False
        logger.info("Zabbix plugin not configured (set MC_ZABBIX_URL/USERNAME/PASSWORD)")
        return False

    async def _jsonrpc(self, method: str, params: dict) -> dict | None:
        try:
            import httpx
            payload = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params,
                "id": self._req_id,
            }
            self._req_id += 1
            if self._auth_token:
                payload["auth"] = self._auth_token
            async with httpx.AsyncClient(verify=False, timeout=30) as client:
                resp = await client.post(self._base_url, json=payload)
                return resp.json()
        except Exception as e:
            logger.warning("Zabbix API call failed: %s", e)
            return None

    async def collect_inventory(self) -> dict[str, Any]:
        if not self._auth_token:
            return {"available": False, "error": "Not authenticated"}

        hosts = await self._jsonrpc("host.get", {
            "output": ["hostid", "host", "name", "status"],
            "selectInterfaces": ["interfaceid", "ip", "dns", "port"],
            "selectGroups": ["groupid", "name"],
            "selectParentTemplates": ["templateid", "name"],
        })
        groups = await self._jsonrpc("hostgroup.get", {
            "output": ["groupid", "name"],
            "selectHosts": ["hostid"],
        })
        triggers = await self._jsonrpc("trigger.get", {
            "output": ["triggerid", "description", "priority", "status", "value"],
            "selectHosts": ["hostid", "host"],
            "filter": {"value": 1},
        })
        problems = await self._jsonrpc("event.get", {
            "output": ["eventid", "name", "severity", "clock"],
            "selectHosts": ["hostid", "host"],
            "filter": {"value": 1},
            "sortfield": ["clock"],
            "sortorder": "DESC",
            "limit": 50,
        })
        templates = await self._jsonrpc("template.get", {
            "output": ["templateid", "name"],
            "selectHosts": ["hostid"],
        })

        return {
            "available": True,
            "hosts": (hosts or {}).get("result", []),
            "host_groups": (groups or {}).get("result", []),
            "triggers": (triggers or {}).get("result", []),
            "problems": (problems or {}).get("result", []),
            "templates": (templates or {}).get("result", []),
        }

    async def execute_command(self, command: str, args: dict[str, Any]) -> dict[str, Any]:
        return {"success": False, "error": f"Unknown command: {command}"}
