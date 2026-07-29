"""
AI Context Engine

Collects and normalizes data from all platform sources into a single
context object for AI analysis. The context engine is the ONLY way
AI accesses platform data.

Sources: Dashboard, Agents, Heartbeats, Event Bus, Zabbix, Veeam,
UniFi, Docker, Automation, Plugins, Companies, Sites, Users,
Recent commands, Recent incidents.

AI NEVER executes infrastructure changes.
"""

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ContextBuilder:
    """Builds a normalized context object from all platform sources."""

    async def build(self, db: Session) -> dict[str, Any]:
        """Build full context from all available sources."""
        context: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "sources": {},
        }

        collectors = [
            ("dashboard", self._collect_dashboard),
            ("agents", self._collect_agents),
            ("health", self._collect_health),
            ("zabbix", self._collect_zabbix),
            ("veeam", self._collect_veeam),
            ("unifi", self._collect_unifi),
            ("docker", self._collect_docker),
            ("automation", self._collect_automation),
            ("integrations", self._collect_integrations),
            ("incidents", self._collect_incidents),
        ]

        for name, collector in collectors:
            try:
                context["sources"][name] = await collector(db)
            except Exception as exc:
                logger.debug("Context collection failed for %s: %s", name, exc)
                context["sources"][name] = {"error": str(exc)[:200]}

        context["alerts"] = self._extract_all_alerts(context["sources"])
        context["summary"] = self._build_summary(context["sources"])

        return context

    def _extract_all_alerts(self, sources: dict) -> list[dict]:
        """Extract and normalize alerts from all sources into a single list."""
        alerts: list[dict] = []
        alert_id = 0

        zabbix = sources.get("zabbix", {})
        if isinstance(zabbix, dict) and zabbix.get("connected") is not False:
            for p in zabbix.get("problems", [])[:10]:
                alert_id += 1
                alerts.append({
                    "id": f"zbx_{alert_id}",
                    "source": "zabbix",
                    "severity": p.get("severity", "warning"),
                    "message": p.get("name", p.get("message", "")),
                    "host_name": p.get("host", "Unknown"),
                    "timestamp": p.get("timestamp", datetime.now(UTC).isoformat()),
                    "tags": ["zabbix", "monitoring"],
                    "affected_systems": ["monitoring"],
                })

        veeam = sources.get("veeam", {})
        if isinstance(veeam, dict) and veeam.get("connected") is not False:
            failed = veeam.get("failed_jobs", [])
            for j in failed[:5]:
                alert_id += 1
                alerts.append({
                    "id": f"vbr_{alert_id}",
                    "source": "veeam",
                    "severity": "warning",
                    "message": f"Backup job failed: {j.get('name', 'Unknown')}",
                    "host_name": j.get("server_name", "Veeam Server"),
                    "timestamp": datetime.now(UTC).isoformat(),
                    "tags": ["veeam", "backup"],
                    "affected_systems": ["backup"],
                })

        docker = sources.get("docker", {})
        if isinstance(docker, dict) and docker.get("connected") is not False:
            unhealthy = docker.get("unhealthy_containers", 0)
            if unhealthy > 0:
                alert_id += 1
                alerts.append({
                    "id": f"dkr_{alert_id}",
                    "source": "docker",
                    "severity": "warning",
                    "message": f"{unhealthy} unhealthy Docker container(s)",
                    "host_name": docker.get("host_name", "Docker Host"),
                    "timestamp": datetime.now(UTC).isoformat(),
                    "tags": ["docker", "containers"],
                    "affected_systems": ["containers"],
                })

        unifi = sources.get("unifi", {})
        if isinstance(unifi, dict) and unifi.get("connected") is not False:
            offline = unifi.get("offline_devices", 0)
            if offline > 0:
                alert_id += 1
                alerts.append({
                    "id": f"uni_{alert_id}",
                    "source": "unifi",
                    "severity": "warning",
                    "message": f"{offline} UniFi device(s) offline",
                    "host_name": "UniFi Network",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "tags": ["unifi", "networking"],
                    "affected_systems": ["networking"],
                })

        return alerts

    def _build_summary(self, sources: dict) -> dict[str, Any]:
        """Build a quick summary of all sources."""
        summary: dict[str, Any] = {}
        for name, data in sources.items():
            if isinstance(data, dict) and "error" not in data:
                summary[name] = "available"
            elif isinstance(data, dict):
                summary[name] = "error"
            else:
                summary[name] = "unavailable"
        return summary

    async def _collect_dashboard(self, db: Session) -> dict[str, Any]:
        try:
            from app.services.dashboard_service import dashboard_service
            return await dashboard_service.get_dashboard(db)
        except Exception as e:
            return {"error": str(e)[:200]}

    async def _collect_agents(self, db: Session) -> dict[str, Any]:
        try:
            from app.services.agent_service import agent_service
            return await agent_service.get_dashboard_summary(db)
        except Exception as e:
            return {"error": str(e)[:200]}

    async def _collect_health(self, db: Session) -> dict[str, Any]:
        try:
            from app.providers.health_provider import health_provider
            return await health_provider.get_health(db)
        except Exception as e:
            return {"error": str(e)[:200]}

    async def _collect_zabbix(self, _db: Session) -> dict[str, Any]:
        try:
            from app.providers.zabbix.provider_factory import get_zabbix_provider
            provider = get_zabbix_provider()
            data = await provider.get_summary()
            try:
                problems = await provider.get_problems()
                data["problems"] = problems.get("problems", [])
            except Exception:
                data.setdefault("problems", [])
            return data
        except Exception as e:
            return {"error": str(e)[:200]}

    async def _collect_veeam(self, _db: Session) -> dict[str, Any]:
        try:
            from app.db.database import SessionLocal
            from app.plugins.installed.official_veeam.cache import cache_manager
            session = SessionLocal()
            try:
                summary = cache_manager.get_summary(session)
                summary["connected"] = True
                return summary
            finally:
                session.close()
        except Exception as e:
            return {"error": str(e)[:200]}

    async def _collect_unifi(self, _db: Session) -> dict[str, Any]:
        try:
            from app.db.database import SessionLocal
            from app.plugins.installed.official_unifi.cache import cache_manager
            session = SessionLocal()
            try:
                summary = cache_manager.get_summary(session)
                summary["connected"] = True
                return summary
            finally:
                session.close()
        except Exception as e:
            return {"error": str(e)[:200]}

    async def _collect_docker(self, _db: Session) -> dict[str, Any]:
        try:
            from app.db.database import SessionLocal
            from app.plugins.installed.official_docker.cache import cache_manager
            session = SessionLocal()
            try:
                summary = cache_manager.get_summary(session)
                summary["connected"] = True
                return summary
            finally:
                session.close()
        except Exception as e:
            return {"error": str(e)[:200]}

    async def _collect_automation(self, db: Session) -> dict[str, Any]:
        try:
            from app.services.automation_service import automation_service
            return await automation_service.get_automation_summary(db)
        except Exception as e:
            return {"error": str(e)[:200]}

    async def _collect_integrations(self, db: Session) -> dict[str, Any]:
        try:
            from app.services.integration_service import integration_service
            return await integration_service.get_dashboard_summary(db)
        except Exception as e:
            return {"error": str(e)[:200]}

    async def _collect_incidents(self, _db: Session) -> dict[str, Any]:
        return {"recent": [], "total": 0}


context_builder = ContextBuilder()
