"""
Mission Control Application Service

Provides application metadata for the dashboard.

Sprint:
    1.0.3 - Dashboard Service Refactor
"""

from datetime import UTC, datetime


class ApplicationService:
    """Application dashboard section."""

    async def get_data(self) -> dict:
        """Return application information."""

        return {
            "name": "Mission Control",
            "tagline": "The Daily Workspace for IT Operations",
            "version": "3.0.0-rc1",
        }

    async def generated(self) -> str:
        """Return dashboard generation timestamp."""

        return datetime.now(UTC).isoformat()


application_service = ApplicationService()
