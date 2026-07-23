"""
Veeam Backup & Replication Plugin

Provides dashboard widgets, REST API, and provider integration for
Veeam B&R servers via the Veeam REST API (v1).
"""

import logging
from typing import Any

from app.plugins.server import ServerPluginSDK

logger = logging.getLogger(__name__)


class VeeamPlugin(ServerPluginSDK):
    """Server plugin for Veeam Backup & Replication integration."""

    async def setup(self) -> None:
        logger.info("Veeam plugin setup: %s", self.slug)

    async def start(self) -> None:
        logger.info("Veeam plugin started: %s", self.slug)

    async def stop(self) -> None:
        logger.info("Veeam plugin stopped: %s", self.slug)

    async def health_check(self) -> dict[str, Any]:
        return {"status": "ok", "version": self.version, "plugin": self.slug}

    async def get_dashboard_widgets(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "veeam-jobs",
                "title": "Backup Jobs",
                "component": "VeeamJobsWidget",
                "size": "medium",
                "refresh_interval": 120,
            },
            {
                "id": "veeam-repos",
                "title": "Repositories",
                "component": "VeeamRepositoriesWidget",
                "size": "medium",
                "refresh_interval": 300,
            },
            {
                "id": "veeam-license",
                "title": "License",
                "component": "VeeamLicenseWidget",
                "size": "small",
                "refresh_interval": 600,
            },
        ]

    async def get_widget_data(self, widget_id: str) -> dict[str, Any]:
        return {"widget_id": widget_id, "data": None, "error": "Not connected"}

    async def get_navigation_items(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "veeam-dashboard",
                "label": "Veeam Dashboard",
                "icon": "backup",
                "path": "/plugins/veeam",
                "group": "Plugins",
                "order": 10,
            }
        ]

    async def get_routes(self) -> list[dict[str, Any]]:
        return []

    async def get_settings_schema(self) -> dict[str, Any] | None:
        return {
            "type": "object",
            "properties": {
                "auto_discover": {
                    "type": "boolean",
                    "default": False,
                    "description": "Auto-discover Veeam servers on startup",
                },
                "poll_interval": {
                    "type": "integer",
                    "default": 120,
                    "minimum": 30,
                    "maximum": 3600,
                    "description": "Polling interval in seconds",
                },
            },
        }

    async def get_settings(self) -> dict[str, Any]:
        return self.settings or {"auto_discover": False, "poll_interval": 120}

    async def save_settings(self, settings: dict[str, Any]) -> None:
        self.settings = settings
        logger.info("Veeam plugin settings saved: %s", settings)
