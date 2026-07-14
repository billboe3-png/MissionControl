"""
Mission Control Microsoft 365 Provider (Mocked)

Returns mocked Microsoft 365 data for development and testing.
No Graph API connections. No authentication.

Sprint 2.2.0 - Microsoft 365 & Active Directory Integration.
"""

import logging
from datetime import UTC, datetime

from app.providers.identity.base_provider import Microsoft365Provider

logger = logging.getLogger(__name__)


class MockMicrosoft365Provider(Microsoft365Provider):
    """
    Mocked Microsoft 365 provider.

    Returns realistic sample data for all M365 operations.
    Used for development, testing, and UI scaffolding.
    """

    async def test_connection(self) -> dict:
        """Test M365 connectivity (mocked)."""
        logger.info("M365: test_connection (mocked)")
        return {
            "connected": True,
            "latency_ms": 45,
            "message": "Mocked M365 connection successful",
            "tenant": "Contoso Corporation",
            "tenant_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        }

    async def get_summary(self) -> dict:
        """Return mocked tenant summary."""
        logger.info("M365: get_summary (mocked)")
        return {
            "connected": True,
            "tenant": {
                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "display_name": "Contoso Corporation",
                "domain": "contoso.com",
                "verified_domains": [
                    "contoso.com",
                    "contoso.onmicrosoft.com",
                ],
                "tenant_type": "AAD",
                "mfa_enabled": True,
                "directory_sync_enabled": True,
            },
            "user_count": 2134,
            "licensed_users": 1987,
            "group_count": 456,
            "device_count": 1203,
            "licenses": [
                {
                    "sku": "ENTERPRISEPREMIUM",
                    "name": "Microsoft 365 E5",
                    "total": 500,
                    "assigned": 478,
                    "available": 22,
                },
                {
                    "sku": "SPE_E3",
                    "name": "Microsoft 365 E3",
                    "total": 1200,
                    "assigned": 1156,
                    "available": 44,
                },
            ],
        }

    async def get_users(self) -> dict:
        """Return mocked user summaries."""
        logger.info("M365: get_users (mocked)")
        return {
            "connected": True,
            "users": [
                {
                    "id": "u1",
                    "display_name": "Robert Barnes",
                    "email": "rbarnes@contoso.com",
                    "department": "IT",
                    "job_title": "Systems Administrator",
                    "account_enabled": True,
                    "licensed": True,
                },
                {
                    "id": "u2",
                    "display_name": "Alice Smith",
                    "email": "asmith@contoso.com",
                    "department": "Engineering",
                    "job_title": "Senior Engineer",
                    "account_enabled": True,
                    "licensed": True,
                },
                {
                    "id": "u3",
                    "display_name": "Mike Jones",
                    "email": "mjones@contoso.com",
                    "department": "Sales",
                    "job_title": "Account Executive",
                    "account_enabled": False,
                    "licensed": False,
                },
            ],
            "total_count": 2134,
            "enabled_count": 2098,
            "disabled_count": 36,
            "licensed_count": 1987,
        }

    async def get_groups(self) -> dict:
        """Return mocked group summaries."""
        logger.info("M365: get_groups (mocked)")
        return {
            "connected": True,
            "groups": [
                {
                    "id": "g1",
                    "display_name": "All Employees",
                    "mail": "allemployees@contoso.com",
                    "member_count": 2134,
                    "type": "Unified",
                },
                {
                    "id": "g2",
                    "display_name": "IT Admins",
                    "mail": "itadmins@contoso.com",
                    "member_count": 45,
                    "type": "Security",
                },
            ],
            "total_count": 456,
        }

    async def get_devices(self) -> dict:
        """Return mocked device summaries."""
        logger.info("M365: get_devices (mocked)")
        return {
            "connected": True,
            "devices": [
                {
                    "id": "d1",
                    "display_name": "DESKTOP-JBARNES",
                    "os": "Windows 11",
                    "version": "23H2",
                    "compliant": True,
                    "last_sync": datetime.now(UTC).isoformat(),
                },
                {
                    "id": "d2",
                    "display_name": "LAPTOP-ASMITH",
                    "os": "Windows 11",
                    "version": "23H2",
                    "compliant": True,
                    "last_sync": datetime.now(UTC).isoformat(),
                },
            ],
            "total_count": 1203,
            "compliant_count": 1178,
            "non_compliant_count": 25,
        }

    async def get_health(self) -> dict:
        """Return mocked M365 service health."""
        logger.info("M365: get_health (mocked)")
        return {
            "connected": True,
            "status": "healthy",
            "overall_status": "healthy",
            "services": [
                {
                    "name": "Exchange Online",
                    "status": "healthy",
                },
                {
                    "name": "SharePoint Online",
                    "status": "healthy",
                },
                {
                    "name": "Microsoft Teams",
                    "status": "healthy",
                },
                {
                    "name": "Entra ID",
                    "status": "healthy",
                },
                {
                    "name": "Intune",
                    "status": "degraded",
                    "issues": [
                        {
                            "title": "Device enrollment delays",
                            "status": "investigating",
                        }
                    ],
                },
            ],
            "active_incidents": 1,
            "resolved_last_30_days": 3,
            "secure_score": {
                "current_score": 72.4,
                "max_score": 100,
                "percentage": 72.4,
            },
        }


m365_provider = MockMicrosoft365Provider()
