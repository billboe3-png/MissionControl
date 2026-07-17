"""
Mission Control Server Plugin SDK

Base class for plugins that run inside the Mission Control server.
Server plugins can register dashboard widgets, REST APIs, pages,
navigation items, settings panels, providers, integrations,
notifications, reports, database models, migrations, and background jobs.
"""

from abc import abstractmethod
from typing import Any

from app.plugins.base import PluginSDK


class ServerPluginSDK(PluginSDK):
    """
    Abstract base class for server-side plugins.

    Server plugins extend the Mission Control backend with:
    - Dashboard widgets
    - REST API endpoints
    - Navigation items and pages
    - Settings panels
    - Provider integrations
    - Notification channels
    - Background jobs
    - Database models and migrations
    """

    # ------------------------------------------------------------------ #
    # Dashboard                                                           #
    # ------------------------------------------------------------------ #

    async def get_dashboard_widgets(self) -> list[dict[str, Any]]:
        """Return dashboard widget definitions.

        Each widget dict should contain:
        - id: unique widget identifier
        - title: display title
        - component: frontend component name
        - size: "small" | "medium" | "large"
        - refresh_interval: seconds between refreshes
        """
        return []

    async def get_widget_data(self, widget_id: str) -> dict[str, Any]:
        """Return data for a specific dashboard widget."""
        return {}

    # ------------------------------------------------------------------ #
    # REST API                                                            #
    # ------------------------------------------------------------------ #

    def get_routes(self) -> list[dict[str, Any]]:
        """Return additional REST API routes.

        Each route dict should contain:
        - path: URL path suffix
        - method: HTTP method
        - handler: async callable
        - summary: human-readable description
        """
        return []

    # ------------------------------------------------------------------ #
    # Navigation                                                          #
    # ------------------------------------------------------------------ #

    async def get_navigation_items(self) -> list[dict[str, Any]]:
        """Return navigation sidebar items.

        Each item should contain:
        - id: unique identifier
        - label: display label
        - icon: icon name or path
        - path: frontend route path
        - group: navigation group (e.g., "Dashboard", "Infrastructure")
        - order: sort order within group
        """
        return []

    # ------------------------------------------------------------------ #
    # Settings                                                            #
    # ------------------------------------------------------------------ #

    async def get_settings_schema(self) -> dict[str, Any] | None:
        """Return JSON schema for plugin settings panel."""
        return None

    async def get_settings(self) -> dict[str, Any]:
        """Return current settings values."""
        return {}

    async def save_settings(self, settings: dict[str, Any]) -> None:
        """Save settings values."""

    # ------------------------------------------------------------------ #
    # Providers                                                           #
    # ------------------------------------------------------------------ #

    def get_providers(self) -> dict[str, Any]:
        """Return provider instances this plugin offers.

        Returns a dict mapping provider name to provider instance.
        """
        return {}

    # ------------------------------------------------------------------ #
    # Notifications                                                       #
    # ------------------------------------------------------------------ #

    async def send_notification(
        self, title: str, body: str, severity: str = "info"
    ) -> bool:
        """Send a notification through this plugin's channel.

        Returns True if sent successfully.
        """
        return False

    # ------------------------------------------------------------------ #
    # Background Jobs                                                     #
    # ------------------------------------------------------------------ #

    async def get_scheduled_jobs(self) -> list[dict[str, Any]]:
        """Return scheduled background job definitions.

        Each job dict should contain:
        - id: unique job identifier
        - name: human-readable name
        - schedule: cron expression or interval seconds
        - handler: async callable
        """
        return []

    # ------------------------------------------------------------------ #
    # Database                                                            #
    # ------------------------------------------------------------------ #

    def get_models(self) -> list[Any]:
        """Return additional SQLAlchemy model classes for migration."""
        return []

    async def get_migrations(self) -> list[dict[str, Any]]:
        """Return plugin-specific Alembic migration scripts."""
        return []
