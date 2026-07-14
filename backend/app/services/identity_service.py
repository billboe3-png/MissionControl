"""
Mission Control Identity Service

Business logic for identity operations: Active Directory
and Microsoft 365 data retrieval through provider layer.

Sprint 2.2.1 - Identity Platform Foundation.
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

    async def get_domain_controllers(self) -> dict:
        """Get domain controllers from AD provider."""
        logger.info("IdentityService: get_domain_controllers")
        return await self._ad.get_domain_controllers()

    async def get_forest(self) -> dict:
        """Get forest information from AD provider."""
        logger.info("IdentityService: get_forest")
        return await self._ad.get_forest()

    async def get_domain(self) -> dict:
        """Get domain information from AD provider."""
        logger.info("IdentityService: get_domain")
        return await self._ad.get_domain()

    async def get_organizational_units(self) -> dict:
        """Get OUs from AD provider."""
        logger.info("IdentityService: get_organizational_units")
        return await self._ad.get_organizational_units()

    async def get_users(self) -> dict:
        """Get users from AD provider."""
        logger.info("IdentityService: get_users")
        return await self._ad.get_users()

    async def get_groups(self) -> dict:
        """Get groups from AD provider."""
        logger.info("IdentityService: get_groups")
        return await self._ad.get_groups()

    async def get_computers(self) -> dict:
        """Get computers from AD provider."""
        logger.info("IdentityService: get_computers")
        return await self._ad.get_computers()

    async def get_gpos(self) -> dict:
        """Get GPOs from AD provider."""
        logger.info("IdentityService: get_gpos")
        return await self._ad.get_gpos()

    async def get_fsmo_roles(self) -> dict:
        """Get FSMO roles from AD provider."""
        logger.info("IdentityService: get_fsmo_roles")
        return await self._ad.get_fsmo_roles()

    async def get_dns_health(self) -> dict:
        """Get DNS health from AD provider."""
        logger.info("IdentityService: get_dns_health")
        return await self._ad.get_dns_health()

    async def get_dhcp_health(self) -> dict:
        """Get DHCP health from AD provider."""
        logger.info("IdentityService: get_dhcp_health")
        return await self._ad.get_dhcp_health()

    # ------------------------------------------------------------------ #
    # Microsoft 365                                                       #
    # ------------------------------------------------------------------ #

    async def get_tenant(self) -> dict:
        """Get tenant information from M365 provider."""
        logger.info("IdentityService: get_tenant")
        return await self._m365.get_tenant()

    async def get_licenses(self) -> dict:
        """Get license summaries from M365 provider."""
        logger.info("IdentityService: get_licenses")
        return await self._m365.get_licenses()

    async def get_service_health(self) -> dict:
        """Get service health from M365 provider."""
        logger.info("IdentityService: get_service_health")
        return await self._m365.get_service_health()

    async def get_entra_health(self) -> dict:
        """Get Entra health from M365 provider."""
        logger.info("IdentityService: get_entra_health")
        return await self._m365.get_entra_health()

    async def get_exchange_health(self) -> dict:
        """Get Exchange health from M365 provider."""
        logger.info("IdentityService: get_exchange_health")
        return await self._m365.get_exchange_health()

    async def get_secure_score(self) -> dict:
        """Get Secure Score from M365 provider."""
        logger.info("IdentityService: get_secure_score")
        return await self._m365.get_secure_score()

    async def get_message_center(self) -> dict:
        """Get Message Center items from M365 provider."""
        logger.info("IdentityService: get_message_center")
        return await self._m365.get_message_center()

    # ------------------------------------------------------------------ #
    # Combined Overview                                                   #
    # ------------------------------------------------------------------ #

    async def get_overview(self) -> dict:
        """
        Get combined identity overview for the dashboard.

        Aggregates key metrics from both AD and M365 providers.
        """
        logger.info("IdentityService: get_overview")

        dc_data = await self._ad.get_domain_controllers()
        users_data = await self._ad.get_users()
        computers_data = await self._ad.get_computers()
        groups_data = await self._ad.get_groups()
        gpo_data = await self._ad.get_gpos()
        tenant_data = await self._m365.get_tenant()
        service_data = await self._m365.get_service_health()
        score_data = await self._m365.get_secure_score()

        return {
            "success": True,
            "overview": {
                "ad": {
                    "domain_controllers": dc_data.get("total_count", 0),
                    "total_users": users_data.get("total_count", 0),
                    "enabled_users": users_data.get("enabled_count", 0),
                    "disabled_users": users_data.get("disabled_count", 0),
                    "locked_out_users": users_data.get("locked_out_count", 0),
                    "total_computers": computers_data.get("total_count", 0),
                    "total_groups": groups_data.get("total_count", 0),
                    "total_gpos": gpo_data.get("total_count", 0),
                },
                "m365": {
                    "total_users": (
                        tenant_data.get("tenant", {})
                        .get("total_users", 0)
                    ),
                    "licensed_users": (
                        tenant_data.get("tenant", {})
                        .get("licensed_users", 0)
                    ),
                    "total_groups": (
                        tenant_data.get("tenant", {})
                        .get("total_groups", 0)
                    ),
                    "total_devices": (
                        tenant_data.get("tenant", {})
                        .get("total_devices", 0)
                    ),
                    "overall_status": (
                        service_data.get("service_health", {})
                        .get("overall_status", "unknown")
                    ),
                    "active_incidents": (
                        service_data.get("service_health", {})
                        .get("active_incidents", 0)
                    ),
                    "secure_score": (
                        score_data.get("secure_score", {})
                        .get("current_score", 0)
                    ),
                },
            },
        }


identity_service = IdentityService()
