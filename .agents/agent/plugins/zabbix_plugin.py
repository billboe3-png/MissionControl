"""Mission Control Agent - Zabbix monitoring plugin."""

import logging
import os
from typing import Any

from agent.plugin import AgentPlugin

logger = logging.getLogger("mc-agent")


class ZabbixPlugin(AgentPlugin):
    """Zabbix monitoring data collector plugin."""

    name = "zabbix"
    version = "3.0.0-rc1"
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
        logger.info("Zabbix plugin initialized")
        return True

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

        hosts = await self._jsonrpc(
            "host.get",
            {
                "output": ["hostid", "host", "name", "status"],
                "selectInterfaces": ["interfaceid", "ip", "dns", "port"],
                "selectGroups": ["groupid", "name"],
                "selectParentTemplates": ["templateid", "name"],
            },
        )
        groups = await self._jsonrpc(
            "hostgroup.get",
            {
                "output": ["groupid", "name"],
                "selectHosts": ["hostid"],
            },
        )
        triggers = await self._jsonrpc(
            "trigger.get",
            {
                "output": ["triggerid", "description", "priority", "status", "value"],
                "selectHosts": ["hostid", "host"],
                "filter": {"value": 1},
            },
        )
        problems = await self._jsonrpc(
            "event.get",
            {
                "output": ["eventid", "name", "severity", "clock"],
                "selectHosts": ["hostid", "host"],
                "filter": {"value": 1},
                "sortfield": ["clock"],
                "sortorder": "DESC",
                "limit": 50,
            },
        )
        templates = await self._jsonrpc(
            "template.get",
            {
                "output": ["templateid", "name"],
                "selectHosts": ["hostid"],
            },
        )

        return {
            "available": True,
            "hosts": (hosts or {}).get("result", []),
            "host_groups": (groups or {}).get("result", []),
            "triggers": (triggers or {}).get("result", []),
            "problems": (problems or {}).get("result", []),
            "templates": (templates or {}).get("result", []),
        }

    async def execute_command(
        self, command: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        if command == "test_connection":
            tested = await self._test_connection(args)
            return {
                "success": tested.get("available", False),
                "stdout": str(tested),
                "stderr": str(tested.get("error", "")),
                "exit_code": 0 if tested.get("available") else 1,
            }
        return {"success": False, "error": f"Unknown command: {command}"}

    async def _test_connection(
        self, args: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        args = args or {}
        base_url = args.get("base_url") or self._base_url
        username = args.get("username") or self._username
        password = args.get("password") or self._password

        if not base_url or not username or password is None:
            return {"available": False, "error": "Missing Zabbix credentials"}
        try:
            from httpx import AsyncClient
        except Exception as exc:
            return {"available": False, "error": f"httpx_missing:{exc}"}
        try:
            async with AsyncClient(
                verify=False, timeout=max(int(args.get("timeout") or 30), 5)
            ) as client:
                login_payload = {
                    "jsonrpc": "2.0",
                    "method": "user.login",
                    "params": {"username": username, "password": password},
                    "id": 1,
                }
                login_resp = await client.post(base_url, json=login_payload)
                login_data = login_resp.json()
                if not login_data.get("result"):
                    return {"available": False, "error": str(login_data.get("error"))}
                auth_token = login_data["result"]
                try:
                    version_payload = {
                        "jsonrpc": "2.0",
                        "method": "apiinfo.version",
                        "params": {},
                        "auth": auth_token,
                        "id": 2,
                    }
                    version_resp = await client.post(base_url, json=version_payload)
                    version_data = version_resp.json()
                    version = version_data.get("result")
                    return {
                        "available": True,
                        "version": version,
                        "latency_ms": None,
                    }
                except Exception as exc:
                    return {"available": True, "version": None, "error": str(exc)}
        except Exception as exc:
            return {"available": False, "error": str(exc)}
