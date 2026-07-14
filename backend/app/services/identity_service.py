"""
Mission Control Identity Service

Business logic for identity operations: Active Directory
and Microsoft 365 data retrieval through provider layer.

Sprint 2.2.0 - Microsoft 365 & Active Directory Integration.
"""

import logging

from app.providers.identity.provider_factory import (
    get_active_directory_provider,
    get_microsoft365_provider,
)

logger = logging.getLogger(__name__)


class IdentityService:
    """
    Service layer for identity operations.

    Orchestrates AD and M365 provider calls and formats
    responses for the API layer.
    """

    def __init__(self) -> None:
        self._ad = get_active_directory_provider()
        self._m365 = get_microsoft365_provider()

    # ------------------------------------------------------------------ #
    # Active Directory                                                    #
    # ------------------------------------------------------------------ #

    async def ad_test_connection(self) -> dict:
        """Test AD connectivity."""
        return await self._ad.test_connection()

    async def ad_get_summary(self) -> dict:
        """Get AD domain and forest summary."""
        return await self._ad.get_summary()

    async def ad_get_users(self) -> dict:
        """Get AD users."""
        return await self._ad.get_users()

    async def ad_get_groups(self) -> dict:
        """Get AD groups."""
        return await self._ad.get_groups()

    async def ad_get_devices(self) -> dict:
        """Get AD computers/devices."""
        return await self._ad.get_devices()

    async def ad_get_health(self) -> dict:
        """Get AD health and replication status."""
        return await self._ad.get_health()

    # ------------------------------------------------------------------ #
    # Microsoft 365                                                       #
    # ------------------------------------------------------------------ #

    async def m365_test_connection(self) -> dict:
        """Test M365 connectivity."""
        return await self._m365.test_connection()

    async def m365_get_summary(self) -> dict:
        """Get tenant summary."""
        return await self._m365.get_summary()

    async def m365_get_users(self) -> dict:
        """Get M365 users."""
        return await self._m365.get_users()

    async def m365_get_groups(self) -> dict:
        """Get M365 groups."""
        return await self._m365.get_groups()

    async def m365_get_devices(self) -> dict:
        """Get M365 managed devices."""
        return await self._m365.get_devices()

    async def m365_get_health(self) -> dict:
        """Get M365 service health."""
        return await self._m365.get_health()

    # ------------------------------------------------------------------ #
    # Combined Overview                                                   #
    # ------------------------------------------------------------------ #

    async def get_overview(self) -> dict:
        """
        Get combined identity overview for the dashboard.

        Aggregates key metrics from both AD and M365 providers.
        """
        ad_summary = await self._ad.get_summary()
        ad_health = await self._ad.get_health()
        m365_summary = await self._m365.get_summary()
        m365_health = await self._m365.get_health()

        return {
            "success": True,
            "overview": {
                "ad": {
                    "connected": ad_summary.get("connected", False),
                    "domain": ad_summary.get("domain", {}).get("name", "N/A"),
                    "user_count": ad_summary.get("user_count", 0),
                    "group_count": ad_summary.get("group_count", 0),
                    "computer_count": ad_summary.get("computer_count", 0),
                    "health": ad_health.get("status", "unknown"),
                    "replication": ad_health.get("replication", {}),
                },
                "m365": {
                    "connected": m365_summary.get("connected", False),
                    "tenant": m365_summary.get("tenant", {}).get("display_name", "N/A"),
                    "licensed_users": m365_summary.get("licensed_users", 0),
                    "license_count": len(m365_summary.get("licenses", [])),
                    "health": m365_health.get("status", "unknown"),
                    "active_incidents": m365_health.get("active_incidents", 0),
                },
            },
        }


identity_service = IdentityService()
