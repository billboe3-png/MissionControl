"""
Mission Control Dashboard Service

Provides the primary dashboard payload for the frontend.

Sprint:
    0.1.1 - Dashboard Foundation
"""

from datetime import datetime, timezone


class DashboardService:
    """Service responsible for building the dashboard response."""

    async def get_dashboard(self) -> dict:
        """Return the dashboard payload."""

        return {
            "application": {
                "name": "Mission Control",
                "tagline": "The Daily Workspace for IT Operations",
                "version": "0.1.1",
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
                "docker": {"enabled": True, "status": "connected"},
                "ssh": {"enabled": False, "status": "not_configured"},
                "zabbix": {"enabled": False, "status": "not_configured"},
                "github": {"enabled": False, "status": "not_configured"},
            },
        }


dashboard_service = DashboardService()
