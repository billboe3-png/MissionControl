"""
Mission Control Zabbix Provider (Production)

Production Zabbix provider using JSON-RPC API.
Read-only operations against Zabbix monitoring server.

Sprint 2.3.0 - Enterprise Zabbix Integration.
"""

import logging
import time

from app.providers.zabbix.base_provider import ZabbixProvider

logger = logging.getLogger(__name__)


def _get_zabbix_config() -> dict:
    """Get Zabbix configuration from settings."""
    try:
        from app.core.config import get_settings

        settings = get_settings()
        return {
            "url": settings.zabbix_url,
            "username": settings.zabbix_username,
            "password": settings.zabbix_password,
            "verify_ssl": settings.zabbix_verify_ssl,
            "timeout": settings.zabbix_timeout,
            "retries": settings.zabbix_retries,
        }
    except Exception:
        return {
            "url": "",
            "username": "",
            "password": "",
            "verify_ssl": True,
            "timeout": 30,
            "retries": 3,
        }


class ApiZabbixProvider(ZabbixProvider):
    """
    Production Zabbix provider using JSON-RPC API.

    Authenticates via user.login and performs read-only
    operations against the Zabbix monitoring server.
    All methods return standardized dicts and never raise exceptions.
    """

    def __init__(self) -> None:
        self._auth_token: str | None = None
        self._request_id = 0

    def _is_configured(self) -> bool:
        config = _get_zabbix_config()
        return bool(config["url"] and config["username"])

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    def _jsonrpc(
        self,
        method: str,
        params: dict | None = None,
        auth: bool = True,
    ) -> dict | None:
        """Execute a JSON-RPC request against Zabbix API."""
        config = _get_zabbix_config()

        if not config["url"]:
            return None

        try:
            import requests

            url = f"{config['url']}/api_jsonrpc.php"
            payload: dict = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params or {},
                "id": self._next_id(),
            }
            if auth and self._auth_token:
                payload["auth"] = self._auth_token

            headers = {"Content-Type": "application/json-rpc"}

            for attempt in range(config["retries"]):
                try:
                    response = requests.post(
                        url,
                        json=payload,
                        headers=headers,
                        timeout=config["timeout"],
                        verify=config["verify_ssl"],
                    )

                    if response.status_code == 200:
                        result = response.json()
                        if "error" in result:
                            logger.warning(
                                "Zabbix: JSON-RPC error %s: %s",
                                result["error"].get("code"),
                                result["error"].get("data"),
                            )
                            return None
                        return result.get("result")

                    logger.warning(
                        "Zabbix: HTTP %d on attempt %d",
                        response.status_code,
                        attempt + 1,
                    )
                except requests.exceptions.RequestException as e:
                    logger.warning(
                        "Zabbix: request failed attempt %d: %s",
                        attempt + 1,
                        type(e).__name__,
                    )
                    if attempt < config["retries"] - 1:
                        time.sleep(1)

            return None
        except Exception as e:
            logger.warning("Zabbix: _jsonrpc error: %s", type(e).__name__)
            return None

    async def _ensure_session(self) -> bool:
        """Ensure we have a valid session, auto-login if needed."""
        if self._auth_token:
            return True
        result = await self.login()
        return result.get("success", False)

    # ------------------------------------------------------------------ #
    # Standardized Interface                                              #
    # ------------------------------------------------------------------ #

    async def test_connection(self) -> dict:
        """Test connectivity to Zabbix."""
        config = _get_zabbix_config()
        if not config["url"]:
            return {"connected": False, "error": "ZABBIX_URL not configured"}

        start = time.monotonic()
        result = self._jsonrpc("apiinfo.version", auth=False)
        latency_ms = int((time.monotonic() - start) * 1000)

        if result:
            return {
                "connected": True,
                "latency_ms": latency_ms,
                "message": f"Zabbix {result} reachable",
                "version": result,
                "server": config["url"],
            }

        return {
            "connected": False,
            "error": "Failed to connect to Zabbix",
            "latency_ms": latency_ms,
        }

    async def login(self) -> dict:
        """Authenticate with Zabbix."""
        config = _get_zabbix_config()
        if not config["url"] or not config["username"]:
            return {"connected": False, "error": "Zabbix not configured"}

        result = self._jsonrpc(
            "user.login",
            {"username": config["username"], "password": config["password"]},
            auth=False,
        )

        if result:
            self._auth_token = result
            return {"success": True, "message": "Session established"}

        return {"success": False, "error": "Authentication failed"}

    async def logout(self) -> dict:
        """End Zabbix session."""
        if self._auth_token:
            self._auth_token = None
        return {"success": True}

    async def get_summary(self) -> dict:
        """Get monitoring overview."""
        if not self._is_configured():
            return {"connected": False, "error": "Zabbix not configured"}

        if not await self._ensure_session():
            return {"connected": False, "error": "Session failed"}

        version = self._jsonrpc("apiinfo.version", auth=False) or "unknown"

        hosts = self._jsonrpc("host.get", {"output": ["hostid", "status", "available"]})
        host_list = hosts if isinstance(hosts, list) else []
        host_count = len(host_list)

        result = self._jsonrpc("trigger.get", {
            "output": ["triggerid", "value", "priority"],
        })
        trigger_list = result if isinstance(result, list) else []
        problems = [t for t in trigger_list if t.get("value") == "1"]
        critical = sum(1 for t in problems if t.get("priority", "0") in ("4", "5"))
        warning = len(problems) - critical

        return {
            "connected": True,
            "version": version,
            "server_name": "Zabbix",
            "host_count": host_count,
            "problem_count": len(problems),
            "critical_count": critical,
            "warning_count": warning,
            "ok_count": host_count - len(problems),
            "uptime_hours": 0,
            "api_latency_ms": 0,
        }

    async def get_hosts(self) -> dict:
        """List monitored hosts."""
        if not self._is_configured():
            return {"connected": False, "error": "Zabbix not configured"}
        if not await self._ensure_session():
            return {"connected": False, "error": "Session failed"}

        result = self._jsonrpc("host.get", {
            "output": ["hostid", "host", "name", "status", "available"],
            "selectInterfaces": ["ip"],
            "selectGroups": ["name"],
            "selectParentTemplates": ["name"],
            "sortfield": "host",
        })

        if not isinstance(result, list):
            return {"connected": False, "error": "Failed to retrieve hosts"}

        hosts = []
        for h in result:
            ips = h.get("interfaces", [])
            groups = [g.get("name", "") for g in h.get("groups", [])]
            templates = [t.get("name", "") for t in h.get("parentTemplates", [])]
            hosts.append({
                "hostid": h.get("hostid", ""),
                "host": h.get("host", ""),
                "name": h.get("name", ""),
                "status": "enabled" if h.get("status") == "0" else "disabled",
                "available": (
                    "available" if h.get("available") == "1" else "unavailable"
                ),
                "interface": ips[0].get("ip", "") if ips else "",
                "groups": groups,
                "templates": templates,
            })

        enabled = sum(1 for h in hosts if h["status"] == "enabled")
        available_count = sum(1 for h in hosts if h["available"] == "available")

        return {
            "connected": True,
            "hosts": hosts,
            "total_count": len(hosts),
            "enabled_count": enabled,
            "disabled_count": len(hosts) - enabled,
            "available_count": available_count,
            "unavailable_count": len(hosts) - available_count,
        }

    async def get_host_groups(self) -> dict:
        """List host groups."""
        if not self._is_configured():
            return {"connected": False, "error": "Zabbix not configured"}
        if not await self._ensure_session():
            return {"connected": False, "error": "Session failed"}

        result = self._jsonrpc("hostgroup.get", {
            "output": ["groupid", "name"],
            "selectHosts": ["hostid"],
            "sortfield": "name",
        })

        if not isinstance(result, list):
            return {"connected": False, "error": "Failed to retrieve groups"}

        groups = [
            {
                "groupid": g.get("groupid", ""),
                "name": g.get("name", ""),
                "host_count": len(g.get("hosts", [])),
            }
            for g in result
        ]

        return {"connected": True, "groups": groups, "total_count": len(groups)}

    async def get_triggers(self) -> dict:
        """List triggers."""
        if not self._is_configured():
            return {"connected": False, "error": "Zabbix not configured"}
        if not await self._ensure_session():
            return {"connected": False, "error": "Session failed"}

        result = self._jsonrpc("trigger.get", {
            "output": ["triggerid", "description", "status", "priority", "value"],
            "selectHosts": ["host"],
            "sortfield": "priority",
            "sortorder": "DESC",
            "limit": 100,
        })

        if not isinstance(result, list):
            return {"connected": False, "error": "Failed to retrieve triggers"}

        triggers = []
        for t in result:
            triggers.append({
                "triggerid": t.get("triggerid", ""),
                "description": t.get("description", ""),
                "status": "enabled" if t.get("status") == "0" else "disabled",
                "priority": {
                    0: "info", 1: "info", 2: "warning",
                    3: "high", 4: "disaster",
                }.get(int(t.get("priority", 0)), "unknown"),
                "value": "PROBLEM" if t.get("value") == "1" else "OK",
                "hosts": [h.get("host", "") for h in t.get("hosts", [])],
            })

        enabled = sum(1 for t in triggers if t["status"] == "enabled")
        problem_count = sum(1 for t in triggers if t["value"] == "PROBLEM")

        return {
            "connected": True,
            "triggers": triggers,
            "total_count": len(triggers),
            "enabled_count": enabled,
            "disabled_count": len(triggers) - enabled,
            "problem_count": problem_count,
            "ok_count": len(triggers) - problem_count,
        }

    async def get_problems(self) -> dict:
        """List current problems."""
        if not self._is_configured():
            return {"connected": False, "error": "Zabbix not configured"}
        if not await self._ensure_session():
            return {"connected": False, "error": "Session failed"}

        result = self._jsonrpc("problem.get", {
            "output": ["eventid", "name", "severity", "acknowledged", "clock"],
            "selectHosts": ["host"],
            "sortfield": "clock",
            "sortorder": "DESC",
            "limit": 100,
        })

        if not isinstance(result, list):
            return {"connected": False, "error": "Failed to retrieve problems"}

        problems = [
            {
                "eventid": p.get("eventid", ""),
                "name": p.get("name", ""),
                "severity": {
                    0: "info", 1: "info", 2: "warning",
                    3: "high", 4: "disaster",
                }.get(int(p.get("severity", 0)), "unknown"),
                "status": "PROBLEM",
                "acknowledged": p.get("acknowledged") == "1",
                "host": (
                    p.get("hosts", [{}])[0].get("host", "")
                    if p.get("hosts") else ""
                ),
                "timestamp": p.get("clock", ""),
            }
            for p in result
        ]

        severity_counts: dict[str, int] = {}
        for p in problems:
            sev = p["severity"]
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        acknowledged = sum(1 for p in problems if p["acknowledged"])

        return {
            "connected": True,
            "problems": problems,
            "total_count": len(problems),
            "severity_counts": severity_counts,
            "acknowledged_count": acknowledged,
            "unacknowledged_count": len(problems) - acknowledged,
        }

    async def get_events(self) -> dict:
        """List recent events."""
        if not self._is_configured():
            return {"connected": False, "error": "Zabbix not configured"}
        if not await self._ensure_session():
            return {"connected": False, "error": "Session failed"}

        result = self._jsonrpc("event.get", {
            "output": ["eventid", "name", "severity", "value", "clock"],
            "selectHosts": ["host"],
            "sortfield": "clock",
            "sortorder": "DESC",
            "limit": 50,
        })

        if not isinstance(result, list):
            return {"connected": False, "error": "Failed to retrieve events"}

        events = [
            {
                "eventid": e.get("eventid", ""),
                "name": e.get("name", ""),
                "severity": {
                    0: "info", 1: "info", 2: "warning",
                    3: "high", 4: "disaster",
                }.get(int(e.get("severity", 0)), "unknown"),
                "status": "PROBLEM" if e.get("value") == "1" else "OK",
                "host": (
                    e.get("hosts", [{}])[0].get("host", "")
                    if e.get("hosts") else ""
                ),
                "timestamp": e.get("clock", ""),
            }
            for e in result
        ]

        return {"connected": True, "events": events, "total_count": len(events)}

    async def get_items(self) -> dict:
        """List items."""
        if not self._is_configured():
            return {"connected": False, "error": "Zabbix not configured"}
        if not await self._ensure_session():
            return {"connected": False, "error": "Session failed"}

        result = self._jsonrpc("item.get", {
            "output": [
                "itemid", "name", "key_", "status",
                "type", "lastvalue", "hostid",
            ],
            "sortfield": "name",
            "limit": 100,
        })

        if not isinstance(result, list):
            return {"connected": False, "error": "Failed to retrieve items"}

        items = [
            {
                "itemid": it.get("itemid", ""),
                "name": it.get("name", ""),
                "key_:": it.get("key_", ""),
                "status": "enabled" if it.get("status") == "0" else "disabled",
                "type": "Zabbix agent" if it.get("type") == "0" else "External check",
                "last_value": it.get("lastvalue", ""),
                "host": it.get("hostid", ""),
            }
            for it in result
        ]

        supported = sum(1 for it in items if it["status"] == "enabled")

        return {
            "connected": True,
            "items": items,
            "total_count": len(items),
            "supported_count": supported,
            "unsupported_count": len(items) - supported,
        }

    async def get_history(self) -> dict:
        """Get historical data."""
        if not self._is_configured():
            return {"connected": False, "error": "Zabbix not configured"}
        if not await self._ensure_session():
            return {"connected": False, "error": "Session failed"}

        return {
            "connected": True,
            "history": [],
            "total_count": 0,
            "message": "History requires itemid parameter",
        }

    async def get_templates(self) -> dict:
        """List templates."""
        if not self._is_configured():
            return {"connected": False, "error": "Zabbix not configured"}
        if not await self._ensure_session():
            return {"connected": False, "error": "Session failed"}

        result = self._jsonrpc("template.get", {
            "output": ["templateid", "name"],
            "selectHosts": ["hostid"],
            "sortfield": "name",
        })

        if not isinstance(result, list):
            return {"connected": False, "error": "Failed to retrieve templates"}

        templates = [
            {
                "templateid": t.get("templateid", ""),
                "name": t.get("name", ""),
                "hosts_count": len(t.get("hosts", [])),
            }
            for t in result
        ]

        return {
            "connected": True,
            "templates": templates,
            "total_count": len(templates),
        }

    async def get_dashboards(self) -> dict:
        """List dashboards."""
        if not self._is_configured():
            return {"connected": False, "error": "Zabbix not configured"}
        if not await self._ensure_session():
            return {"connected": False, "error": "Session failed"}

        result = self._jsonrpc("dashboard.get", {
            "output": ["dashboardid", "name", "display_name", "owner"],
            "selectPages": ["dashboardid"],
            "sortfield": "name",
        })

        if not isinstance(result, list):
            return {
                "connected": True,
                "dashboards": [],
                "total_count": 0,
                "message": "Dashboard API not available in this Zabbix version",
            }

        dashboards = [
            {
                "dashboardid": d.get("dashboardid", ""),
                "name": d.get("name", ""),
                "display_name": d.get("display_name", d.get("name", "")),
                "owner": d.get("owner", ""),
                "pages": len(d.get("pages", [])),
            }
            for d in result
        ]

        return {
            "connected": True,
            "dashboards": dashboards,
            "total_count": len(dashboards),
        }

    async def get_maps(self) -> dict:
        """List maps."""
        if not self._is_configured():
            return {"connected": False, "error": "Zabbix not configured"}
        if not await self._ensure_session():
            return {"connected": False, "error": "Session failed"}

        result = self._jsonrpc("map.get", {
            "output": ["sysmapid", "name", "width", "height"],
            "selectLinks": ["selementid1"],
            "sortfield": "name",
        })

        if not isinstance(result, list):
            return {"connected": False, "error": "Failed to retrieve maps"}

        maps = [
            {
                "sysmapid": m.get("sysmapid", ""),
                "name": m.get("name", ""),
                "width": int(m.get("width", 0)),
                "height": int(m.get("height", 0)),
                "elements": len(m.get("links", [])),
            }
            for m in result
        ]

        return {"connected": True, "maps": maps, "total_count": len(maps)}

    async def get_health(self) -> dict:
        """Get Zabbix health."""
        if not self._is_configured():
            return {"connected": False, "error": "Zabbix not configured"}
        if not await self._ensure_session():
            return {"connected": False, "error": "Session failed"}

        version = self._jsonrpc("apiinfo.version", auth=False) or "unknown"

        return {
            "connected": True,
            "status": "healthy",
            "version": version,
            "server": _get_zabbix_config()["url"],
            "uptime_hours": 0,
            "api_latency_ms": 0,
            "database": {"status": "unknown", "type": "unknown", "size_mb": 0},
            "proxy_count": 0,
            "poller_items_per_sec": 0,
            "trigger_functions_per_sec": 0,
        }
