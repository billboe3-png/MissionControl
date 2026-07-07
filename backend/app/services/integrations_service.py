"""
Mission Control Integrations Service

Provides integration data for the dashboard.

Sprint:
    1.0.3 - Dashboard Service Refactor
"""

from app.services.docker_service import get_docker_status


class IntegrationsService:
    """Integration dashboard section."""

    async def get_data(self) -> dict:

        return {
            "docker": await get_docker_status(),
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
        }


integrations_service = IntegrationsService()
