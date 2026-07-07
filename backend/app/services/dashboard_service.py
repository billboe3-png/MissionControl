"""
Mission Control Dashboard Service

Provides the primary dashboard payload for the frontend.

Sprint:
    1.0.2 - Live Docker Integration
"""

from datetime import datetime, timezone

from app.services.docker_service import get_docker_status


class DashboardService:
    """Service responsible for building the dashboard response."""

    async def get_dashboard(self) -> dict:
        """Return the dashboard payload."""

        docker = await get_docker_status()

        return {
            "application": {
                "name": "Mission Control",
                "tagline": "The Daily Workspace for IT Operations",
                "version": "1.0.2",
            },
            "generated": datetime.now(timezone.utc).isoformat(),
            "health": {
                "backend": {"status": "healthy"},
                "database": {"status": "healthy"},
                "redis": {"status": "healthy"},
            },
            "projects": {"count": 0, "items": []},
            "tasks": {"count": 0, "items": []},
            "notes": {"count": 0, "items": []},
            "resume": None,
            "parking_lot": {"count": 0, "items": []},
            "integrations": {
                "docker": docker,
                "ssh": {
                    "enabled": False,
                    "status": "not_configured",
                },
                "zabbix": {
                    "enabled": False,
                    "status": "not_configured",
                },
                "github": {
                    "enabled": False,
                    "status": "not_configured",
                },
            },
        }


dashboard_service = DashboardService()
