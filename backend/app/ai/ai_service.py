"""
Mission Control AI Service

Service layer that bridges routers to the AI engine.
Handles data collection from providers, invokes AI analysis,
and formats responses.

AI NEVER executes infrastructure changes.

Sprint 2.6.0 - AI Operations Engine.
"""

import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class AIService:
    """Service layer for AI operations."""

    async def get_overview(self, db: Session) -> dict:
        """Get AI operations overview for the dashboard."""
        from app.ai.ai_engine import ai_engine

        context = await self._collect_context(db)
        overview = await ai_engine.get_ai_overview(context)
        return overview

    async def analyze(self, db: Session) -> dict:
        """Full incident analysis pipeline."""
        from app.ai.ai_engine import ai_engine

        context = await self._collect_context(db)
        alerts = self._extract_alerts(context)
        return await ai_engine.analyze_incidents(alerts)

    async def get_recommendations(self, db: Session) -> dict:
        """Get all current recommendations."""
        from app.ai.ai_engine import ai_engine

        context = await self._collect_context(db)
        alerts = self._extract_alerts(context)
        analysis = await ai_engine.analyze_incidents(alerts)
        return analysis.get("recommendations", {})

    async def get_correlations(self, db: Session) -> dict:
        """Get correlated alerts."""

        context = await self._collect_context(db)
        alerts = self._extract_alerts(context)
        from app.ai.correlation_engine import correlation_engine

        return correlation_engine.correlate(alerts)

    async def get_incidents(self, db: Session) -> dict:
        """Get classified incidents."""
        from app.ai.ai_engine import ai_engine

        context = await self._collect_context(db)
        alerts = self._extract_alerts(context)
        analysis = await ai_engine.analyze_incidents(alerts)
        return {
            "incidents": analysis.get("classified", []),
            "summary": analysis.get("summary", {}),
            "top_risks": analysis.get("top_risks", []),
        }

    async def get_health_score(self, db: Session) -> dict:
        """Get system health score."""
        from app.ai.ai_engine import ai_engine

        context = await self._collect_context(db)
        return await ai_engine.get_health_score(context)

    async def search(self, query: str, db: Session) -> dict:
        """Natural language search."""
        from app.ai.ai_engine import ai_engine

        context = await self._collect_context(db)
        return await ai_engine.natural_language_search(query, context)

    async def get_history(self, db: Session) -> dict:
        """Get AI analysis history (placeholder for future persistence)."""
        return {
            "analyses": [],
            "total": 0,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    async def test_provider(self) -> dict:
        """Test the current AI provider connection."""
        from app.ai.ai_provider import get_ai_provider

        provider = get_ai_provider()
        result = await provider.test_connection()
        info = await provider.get_provider_info()
        return {**result, "provider": info}

    async def get_provider_status(self) -> dict:
        """Get current AI provider status."""
        from app.ai.ai_provider import get_ai_provider

        provider = get_ai_provider()
        info = await provider.get_provider_info()
        test = await provider.test_connection()
        return {
            "provider": info,
            "connected": test.get("success", False),
        }

    async def _collect_context(self, db: Session) -> dict:
        """Collect context data from all available providers."""
        context = {}

        context["health"] = await self._get_health(db)
        context["system"] = self._get_system()
        context["docker"] = await self._get_docker()
        context["zabbix"] = await self._get_zabbix()
        context["hyperv"] = await self._get_hyperv(db)
        context["integrations"] = await self._get_integrations(db)
        context["remote"] = await self._get_remote(db)

        return context

    def _extract_alerts(self, context: dict) -> list[dict]:
        """Extract alerts from context data for AI analysis."""
        alerts = []
        alert_id = 0

        zabbix = context.get("zabbix", {})
        if isinstance(zabbix, dict) and zabbix.get("connected") is not False:
            problem_count = zabbix.get("problem_count", 0)
            if problem_count > 0:
                critical = zabbix.get("critical_count", 0)
                warning = zabbix.get("warning_count", 0)
                for _ in range(min(critical, 5)):
                    alert_id += 1
                    alerts.append(
                        {
                            "id": f"zbx_{alert_id}",
                            "source": "zabbix",
                            "severity": "critical",
                            "message": "Zabbix critical problem detected",
                            "host_name": "Monitored Host",
                            "timestamp": datetime.now(UTC).isoformat(),
                            "tags": ["zabbix", "monitoring"],
                            "affected_systems": ["monitoring"],
                            "host_importance": "zabbix_server",
                            "alert_frequency": critical,
                            "historical_failures": 0,
                        }
                    )
                for _ in range(min(warning, 5)):
                    alert_id += 1
                    alerts.append(
                        {
                            "id": f"zbx_{alert_id}",
                            "source": "zabbix",
                            "severity": "warning",
                            "message": "Zabbix warning detected",
                            "host_name": "Monitored Host",
                            "timestamp": datetime.now(UTC).isoformat(),
                            "tags": ["zabbix", "monitoring"],
                            "affected_systems": ["monitoring"],
                            "host_importance": "unknown",
                            "alert_frequency": warning,
                            "historical_failures": 0,
                        }
                    )

        hyperv = context.get("hyperv", {})
        if isinstance(hyperv, dict) and hyperv.get("connected") is not False:
            stopped = hyperv.get("stopped", 0)
            if stopped > 0:
                alert_id += 1
                alerts.append(
                    {
                        "id": f"hv_{alert_id}",
                        "source": "hyperv",
                        "severity": "warning",
                        "message": f"{stopped} virtual machine(s) stopped",
                        "host_name": "Hyper-V Host",
                        "timestamp": datetime.now(UTC).isoformat(),
                        "tags": ["hyperv", "virtualization"],
                        "affected_systems": ["virtualization"],
                        "host_importance": "hyperv_host",
                        "alert_frequency": stopped,
                        "historical_failures": 0,
                    }
                )

        return alerts

    async def _get_health(self, db: Session) -> dict:
        try:
            from app.providers.health_provider import health_provider

            return await health_provider.get_health(db)
        except Exception as e:
            logger.debug("AI: health data failed: %s", e)
            return {}

    def _get_system(self) -> dict:
        try:
            from app.providers.system_provider import system_provider

            return system_provider.get_system_info()
        except Exception as e:
            logger.debug("AI: system data failed: %s", e)
            return {}

    async def _get_docker(self) -> dict:
        try:
            from app.providers.docker_provider import docker_provider

            return await docker_provider.get_docker_data()
        except Exception as e:
            logger.debug("AI: docker data failed: %s", e)
            return {}

    async def _get_zabbix(self) -> dict:
        try:
            from app.providers.zabbix.provider_factory import get_zabbix_provider

            provider = get_zabbix_provider()
            return await provider.get_summary()
        except Exception as e:
            logger.debug("AI: zabbix data failed: %s", e)
            return {}

    async def _get_hyperv(self, db: Session) -> dict:
        try:
            from app.providers.hyperv_dashboard import (
                virtualization_dashboard_provider,
            )

            return await virtualization_dashboard_provider.get_virtualization_data(db)
        except Exception as e:
            logger.debug("AI: hyperv data failed: %s", e)
            return {}

    async def _get_integrations(self, db: Session) -> dict:
        try:
            from app.repositories.integration_profile_repository import (
                IntegrationProfileRepository,
            )

            profiles = IntegrationProfileRepository.get_all(db)
            return {
                "count": len(profiles),
                "items": [
                    {
                        "type": p.integration_type,
                        "enabled": p.enabled,
                    }
                    for p in profiles
                ],
            }
        except Exception as e:
            logger.debug("AI: integrations data failed: %s", e)
            return {"count": 0, "items": []}

    async def _get_remote(self, db: Session) -> dict:
        try:
            from app.repositories.remote_host_repository import RemoteHostRepository

            hosts = RemoteHostRepository.get_all(db)
            enabled = [h for h in hosts if h.enabled]
            return {
                "total": len(hosts),
                "enabled": len(enabled),
            }
        except Exception as e:
            logger.debug("AI: remote data failed: %s", e)
            return {"total": 0, "enabled": 0}


ai_service = AIService()
