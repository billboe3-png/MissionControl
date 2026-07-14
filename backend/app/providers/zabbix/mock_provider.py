"""
Mission Control Zabbix Provider (Mocked)

Returns mocked Zabbix data for development and testing.
No API connections. Simulates various environments.

Sprint 2.3.0 - Enterprise Zabbix Integration.
"""

import logging
import time
from datetime import UTC, datetime

from app.providers.zabbix.base_provider import ZabbixProvider

logger = logging.getLogger(__name__)

MOCK_MODE = "healthy"


def set_mock_mode(mode: str) -> None:
    """Set the mock mode for testing different scenarios."""
    global MOCK_MODE
    MOCK_MODE = mode


class MockZabbixProvider(ZabbixProvider):
    """
    Mocked Zabbix provider.

    Returns realistic sample data for all Zabbix operations.
    Supports multiple modes: healthy, large, offline, auth_failure,
    empty, timeout.
    """

    def __init__(self) -> None:
        self._authenticated = False

    def _should_fail(self) -> bool:
        return MOCK_MODE in ("offline", "auth_failure", "timeout")

    def _is_empty(self) -> bool:
        return MOCK_MODE == "empty"

    def _get_offline_response(self) -> dict:
        if MOCK_MODE == "offline":
            return {
                "connected": False,
                "error": "Zabbix server unreachable",
            }
        if MOCK_MODE == "auth_failure":
            return {
                "connected": False,
                "error": "Authentication failed: invalid credentials",
            }
        if MOCK_MODE == "timeout":
            return {
                "connected": False,
                "error": "Request timed out after 30s",
            }
        return {}

    async def test_connection(self) -> dict:
        logger.info("Zabbix: test_connection (mocked, mode=%s)", MOCK_MODE)
        if self._should_fail():
            return self._get_offline_response()
        return {
            "connected": True,
            "latency_ms": 23,
            "message": "Mocked Zabbix connection successful",
            "version": "7.0.0",
            "server": "zabbix.corp.contoso.com",
        }

    async def login(self) -> dict:
        logger.info("Zabbix: login (mocked, mode=%s)", MOCK_MODE)
        if self._should_fail():
            return self._get_offline_response()
        self._authenticated = True
        return {"success": True, "message": "Session established"}

    async def logout(self) -> dict:
        logger.info("Zabbix: logout (mocked)")
        self._authenticated = False
        return {"success": True}

    async def get_summary(self) -> dict:
        logger.info("Zabbix: get_summary (mocked)")
        if self._should_fail():
            return self._get_offline_response()
        if self._is_empty():
            return {
                "connected": True,
                "version": "7.0.0",
                "server_name": "Zabbix",
                "host_count": 0,
                "problem_count": 0,
                "critical_count": 0,
                "warning_count": 0,
                "ok_count": 0,
                "uptime_hours": 0,
                "api_latency_ms": 0,
            }

        count = 500 if MOCK_MODE == "large" else 42
        return {
            "connected": True,
            "version": "7.0.0",
            "server_name": "Zabbix Production",
            "host_count": count,
            "problem_count": 3,
            "critical_count": 1,
            "warning_count": 2,
            "ok_count": count - 3,
            "uptime_hours": 2160,
            "api_latency_ms": 45,
        }

    async def get_hosts(self) -> dict:
        logger.info("Zabbix: get_hosts (mocked)")
        if self._should_fail():
            return self._get_offline_response()
        if self._is_empty():
            return {
                "connected": True,
                "hosts": [],
                "total_count": 0,
                "enabled_count": 0,
                "disabled_count": 0,
                "available_count": 0,
                "unavailable_count": 0,
            }

        linux_groups = ["Linux servers", "Production"]
        win_groups = ["Windows servers", "Production"]
        linux_tpl = ["Template OS Linux by Zabbix agent"]
        win_tpl = ["Template OS Windows by Zabbix agent"]
        limit = 501 if MOCK_MODE == "large" else 43

        hosts = []
        for i in range(1, limit):
            is_linux = i % 3 == 0
            hosts.append({
                "hostid": str(i),
                "host": f"host{i:03d}.corp.contoso.com",
                "name": f"Server {i:03d}",
                "status": (
                    "enabled" if i % 10 != 0 else "disabled"
                ),
                "available": (
                    "available" if i % 20 != 0 else "unavailable"
                ),
                "interface": f"10.0.{i // 255}.{i % 255}",
                "groups": linux_groups if is_linux else win_groups,
                "templates": linux_tpl if is_linux else win_tpl,
                "last_access": datetime.now(UTC).isoformat(),
            })

        enabled = sum(
            1 for h in hosts if h["status"] == "enabled"
        )
        available = sum(
            1 for h in hosts if h["available"] == "available"
        )

        return {
            "connected": True,
            "hosts": hosts,
            "total_count": len(hosts),
            "enabled_count": enabled,
            "disabled_count": len(hosts) - enabled,
            "available_count": available,
            "unavailable_count": len(hosts) - available,
        }

    async def get_host_groups(self) -> dict:
        logger.info("Zabbix: get_host_groups (mocked)")
        if self._should_fail():
            return self._get_offline_response()
        if self._is_empty():
            return {
                "connected": True,
                "groups": [],
                "total_count": 0,
            }

        groups = [
            {"groupid": "1", "name": "Linux servers", "host_count": 18},
            {"groupid": "2", "name": "Windows servers", "host_count": 15},
            {"groupid": "3", "name": "Production", "host_count": 35},
            {"groupid": "4", "name": "Development", "host_count": 7},
            {"groupid": "5", "name": "Database servers", "host_count": 6},
            {"groupid": "6", "name": "Web servers", "host_count": 12},
            {"groupid": "7", "name": "Network devices", "host_count": 8},
            {"groupid": "8", "name": "Virtual machines", "host_count": 22},
        ]

        return {
            "connected": True,
            "groups": groups,
            "total_count": len(groups),
        }

    async def get_triggers(self) -> dict:
        logger.info("Zabbix: get_triggers (mocked)")
        if self._should_fail():
            return self._get_offline_response()
        if self._is_empty():
            return {
                "connected": True,
                "triggers": [],
                "total_count": 0,
                "enabled_count": 0,
                "disabled_count": 0,
                "problem_count": 0,
                "ok_count": 0,
            }

        triggers = [
            {
                "triggerid": "1",
                "description": "CPU load too high",
                "status": "enabled",
                "priority": "high",
                "value": "PROBLEM",
                "hosts": ["host001.corp.contoso.com"],
            },
            {
                "triggerid": "2",
                "description": "Disk space low on /",
                "status": "enabled",
                "priority": "disaster",
                "value": "PROBLEM",
                "hosts": ["host005.corp.contoso.com"],
            },
            {
                "triggerid": "3",
                "description": "High memory usage",
                "status": "enabled",
                "priority": "warning",
                "value": "PROBLEM",
                "hosts": ["host012.corp.contoso.com"],
            },
            {
                "triggerid": "4",
                "description": "Service sshd down",
                "status": "enabled",
                "priority": "high",
                "value": "OK",
                "hosts": ["host003.corp.contoso.com"],
            },
            {
                "triggerid": "5",
                "description": "Network latency",
                "status": "enabled",
                "priority": "warning",
                "value": "OK",
                "hosts": ["host020.corp.contoso.com"],
            },
            {
                "triggerid": "6",
                "description": "Certificate expiring soon",
                "status": "enabled",
                "priority": "info",
                "value": "PROBLEM",
                "hosts": ["host008.corp.contoso.com"],
            },
        ]

        enabled = sum(
            1 for t in triggers if t["status"] == "enabled"
        )
        problem_count = sum(
            1 for t in triggers if t["value"] == "PROBLEM"
        )

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
        logger.info("Zabbix: get_problems (mocked)")
        if self._should_fail():
            return self._get_offline_response()
        if self._is_empty():
            return {
                "connected": True,
                "problems": [],
                "total_count": 0,
                "severity_counts": {},
                "acknowledged_count": 0,
                "unacknowledged_count": 0,
            }

        now = datetime.now(UTC).isoformat()
        problems = [
            {
                "eventid": "1001",
                "name": "CPU load too high",
                "severity": "high",
                "status": "PROBLEM",
                "acknowledged": False,
                "host": "host001.corp.contoso.com",
                "timestamp": now,
            },
            {
                "eventid": "1002",
                "name": "Disk space low on /",
                "severity": "disaster",
                "status": "PROBLEM",
                "acknowledged": True,
                "host": "host005.corp.contoso.com",
                "timestamp": now,
            },
            {
                "eventid": "1003",
                "name": "High memory usage",
                "severity": "warning",
                "status": "PROBLEM",
                "acknowledged": False,
                "host": "host012.corp.contoso.com",
                "timestamp": now,
            },
        ]

        severity_counts: dict[str, int] = {}
        for p in problems:
            sev = p["severity"]
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        acknowledged = sum(
            1 for p in problems if p["acknowledged"]
        )

        return {
            "connected": True,
            "problems": problems,
            "total_count": len(problems),
            "severity_counts": severity_counts,
            "acknowledged_count": acknowledged,
            "unacknowledged_count": len(problems) - acknowledged,
        }

    async def get_events(self) -> dict:
        logger.info("Zabbix: get_events (mocked)")
        if self._should_fail():
            return self._get_offline_response()
        if self._is_empty():
            return {
                "connected": True,
                "events": [],
                "total_count": 0,
            }

        sevs = ["info", "warning", "high"]
        now = datetime.now(UTC).isoformat()
        events = []
        for i in range(1, 21):
            events.append({
                "eventid": str(2000 + i),
                "name": f"Event {i}",
                "severity": sevs[i % 3],
                "status": "PROBLEM" if i % 4 == 0 else "OK",
                "host": f"host{i:03d}.corp.contoso.com",
                "timestamp": now,
            })

        return {
            "connected": True,
            "events": events,
            "total_count": len(events),
        }

    async def get_items(self) -> dict:
        logger.info("Zabbix: get_items (mocked)")
        if self._should_fail():
            return self._get_offline_response()
        if self._is_empty():
            return {
                "connected": True,
                "items": [],
                "total_count": 0,
                "supported_count": 0,
                "unsupported_count": 0,
            }

        names = [
            "CPU load", "Memory usage",
            "Disk space", "Network in", "Network out",
        ]
        items = []
        for i in range(1, 51):
            items.append({
                "itemid": str(i),
                "name": names[(i - 1) % 5],
                "key_": f"system.cpu.load[{i}]",
                "status": "enabled",
                "type": "Zabbix agent",
                "last_value": str(round(50 + i * 0.5, 1)),
                "host": f"host{i:03d}.corp.contoso.com",
            })

        supported = sum(
            1 for it in items if it["status"] == "enabled"
        )

        return {
            "connected": True,
            "items": items,
            "total_count": len(items),
            "supported_count": supported,
            "unsupported_count": len(items) - supported,
        }

    async def get_history(self) -> dict:
        logger.info("Zabbix: get_history (mocked)")
        if self._should_fail():
            return self._get_offline_response()
        if self._is_empty():
            return {
                "connected": True,
                "history": [],
                "total_count": 0,
            }

        now = time.time()
        history = [
            {
                "clock": str(int(now - (59 - i) * 60)),
                "value": str(round(40 + i * 0.8, 1)),
            }
            for i in range(60)
        ]

        return {
            "connected": True,
            "history": history,
            "total_count": len(history),
        }

    async def get_templates(self) -> dict:
        logger.info("Zabbix: get_templates (mocked)")
        if self._should_fail():
            return self._get_offline_response()
        if self._is_empty():
            return {
                "connected": True,
                "templates": [],
                "total_count": 0,
            }

        templates = [
            {
                "templateid": "1",
                "name": "Template OS Linux by Zabbix agent",
                "hosts_count": 18,
            },
            {
                "templateid": "2",
                "name": "Template OS Windows by Zabbix agent",
                "hosts_count": 15,
            },
            {
                "templateid": "3",
                "name": "Template App MySQL by Zabbix agent 2",
                "hosts_count": 4,
            },
            {
                "templateid": "4",
                "name": "Template App PostgreSQL by Zabbix agent 2",
                "hosts_count": 2,
            },
            {
                "templateid": "5",
                "name": "Template App Apache by Zabbix agent",
                "hosts_count": 8,
            },
            {
                "templateid": "6",
                "name": "Template App Nginx by Zabbix agent",
                "hosts_count": 4,
            },
            {
                "templateid": "7",
                "name": "Template Network SNMP Generic",
                "hosts_count": 8,
            },
            {
                "templateid": "8",
                "name": "Template Module Zabbix agent 2",
                "hosts_count": 42,
            },
        ]

        return {
            "connected": True,
            "templates": templates,
            "total_count": len(templates),
        }

    async def get_dashboards(self) -> dict:
        logger.info("Zabbix: get_dashboards (mocked)")
        if self._should_fail():
            return self._get_offline_response()
        if self._is_empty():
            return {
                "connected": True,
                "dashboards": [],
                "total_count": 0,
            }

        dashboards = [
            {
                "dashboardid": "1",
                "name": "Production Overview",
                "display_name": "Production Overview",
                "owner": "admin",
                "pages": 3,
            },
            {
                "dashboardid": "2",
                "name": "Network Operations",
                "display_name": "Network Operations Center",
                "owner": "admin",
                "pages": 2,
            },
            {
                "dashboardid": "3",
                "name": "Database Health",
                "display_name": "Database Health Monitoring",
                "owner": "dba_team",
                "pages": 1,
            },
        ]

        return {
            "connected": True,
            "dashboards": dashboards,
            "total_count": len(dashboards),
        }

    async def get_maps(self) -> dict:
        logger.info("Zabbix: get_maps (mocked)")
        if self._should_fail():
            return self._get_offline_response()
        if self._is_empty():
            return {
                "connected": True,
                "maps": [],
                "total_count": 0,
            }

        maps = [
            {
                "sysmapid": "1",
                "name": "Network Topology",
                "width": 1200,
                "height": 800,
                "elements": 15,
            },
            {
                "sysmapid": "2",
                "name": "Data Center Layout",
                "width": 1600,
                "height": 1200,
                "elements": 28,
            },
            {
                "sysmapid": "3",
                "name": "Cloud Infrastructure",
                "width": 1400,
                "height": 1000,
                "elements": 22,
            },
        ]

        return {
            "connected": True,
            "maps": maps,
            "total_count": len(maps),
        }

    async def get_health(self) -> dict:
        logger.info("Zabbix: get_health (mocked)")
        if self._should_fail():
            return {
                "connected": False,
                "status": "unavailable",
                "error": "Zabbix server unreachable",
            }
        if self._is_empty():
            return {
                "connected": True,
                "status": "healthy",
                "version": "7.0.0",
                "server": "zabbix.corp.contoso.com",
                "uptime_hours": 0,
                "api_latency_ms": 0,
                "database": {
                    "status": "unknown",
                    "type": "unknown",
                    "size_mb": 0,
                },
                "proxy_count": 0,
                "poller_items_per_sec": 0,
                "trigger_functions_per_sec": 0,
            }

        return {
            "connected": True,
            "status": "healthy",
            "version": "7.0.0",
            "server": "zabbix.corp.contoso.com",
            "uptime_hours": 2160,
            "api_latency_ms": 45,
            "database": {
                "status": "healthy",
                "type": "PostgreSQL",
                "size_mb": 2048,
            },
            "proxy_count": 2,
            "poller_items_per_sec": 150,
            "trigger_functions_per_sec": 85,
        }
