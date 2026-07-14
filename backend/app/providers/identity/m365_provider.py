"""
Mission Control Microsoft 365 Provider (Mocked)

Returns mocked Microsoft 365 data for development and testing.
No Graph API connections. No authentication.

Sprint 2.2.1 - Identity Platform Foundation.
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

    async def get_tenant(self) -> dict:
        """Return mocked tenant information."""
        logger.info("M365: get_tenant (mocked)")
        return {
            "success": True,
            "tenant": {
                "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "name": "Contoso Corporation",
                "display_name": "Contoso Corporation",
                "domain": "contoso.com",
                "verified_domains": ["contoso.com", "contoso.onmicrosoft.com"],
                "default_domain": "contoso.com",
                "tenant_type": "AAD",
                "created_at": "2018-06-01T00:00:00Z",
                "created_by": "admin@contoso.com",
                "directory_sync_enabled": True,
                "directory_sync_last_sync": datetime.now(UTC).isoformat(),
                "mfa_enabled": True,
                "conditional_access_enabled": True,
                "total_users": 2134,
                "licensed_users": 1987,
                "total_groups": 456,
                "total_devices": 1203,
            },
        }

    async def get_licenses(self) -> dict:
        """Return mocked license summary data."""
        logger.info("M365: get_licenses (mocked)")
        return {
            "success": True,
            "licenses": [
                {
                    "sku_part_number": "ENTERPRISEPREMIUM",
                    "display_name": "Microsoft 365 E5",
                    "total_licenses": 500,
                    "assigned_licenses": 478,
                    "available_licenses": 22,
                    "cost_per_user_monthly": 57.00,
                    "total_monthly_cost": 27226.00,
                },
                {
                    "sku_part_number": "SPE_E3",
                    "display_name": "Microsoft 365 E3",
                    "total_licenses": 1200,
                    "assigned_licenses": 1156,
                    "available_licenses": 44,
                    "cost_per_user_monthly": 36.00,
                    "total_monthly_cost": 41616.00,
                },
                {
                    "sku_part_number": "EXCHANGESTANDARD",
                    "display_name": "Exchange Online Plan 1",
                    "total_licenses": 300,
                    "assigned_licenses": 289,
                    "available_licenses": 11,
                    "cost_per_user_monthly": 4.00,
                    "total_monthly_cost": 1156.00,
                },
                {
                    "sku_part_number": "EMSPREMIUM",
                    "display_name": "Enterprise Mobility + Security E5",
                    "total_licenses": 500,
                    "assigned_licenses": 478,
                    "available_licenses": 22,
                    "cost_per_user_monthly": 16.00,
                    "total_monthly_cost": 7648.00,
                },
            ],
            "total_sku_count": 4,
            "total_assigned": 2401,
            "total_available": 99,
            "total_monthly_cost": 77646.00,
        }

    async def get_service_health(self) -> dict:
        """Return mocked Microsoft 365 service health data."""
        logger.info("M365: get_service_health (mocked)")
        now = datetime.now(UTC).isoformat()
        return {
            "success": True,
            "service_health": {
                "overall_status": "healthy",
                "services": [
                    {
                        "name": "Exchange Online",
                        "status": "healthy",
                        "feature": "Exchange",
                        "issues": [],
                    },
                    {
                        "name": "SharePoint Online",
                        "status": "healthy",
                        "feature": "SharePoint",
                        "issues": [],
                    },
                    {
                        "name": "Microsoft Teams",
                        "status": "healthy",
                        "feature": "Microsoft Teams",
                        "issues": [],
                    },
                    {
                        "name": "OneDrive for Business",
                        "status": "healthy",
                        "feature": "OneDrive",
                        "issues": [],
                    },
                    {
                        "name": "Entra ID",
                        "status": "healthy",
                        "feature": "Azure Active Directory",
                        "issues": [],
                    },
                    {
                        "name": "Intune",
                        "status": "degraded",
                        "feature": "Intune",
                        "issues": [
                            {
                                "title": "Device enrollment delays",
                                "status": "investigating",
                                "impact": "Minor",
                                "start_time": now,
                                "last_update": now,
                            }
                        ],
                    },
                ],
                "active_incidents": 1,
                "resolved_last_30_days": 3,
            },
        }

    async def get_entra_health(self) -> dict:
        """Return mocked Entra ID health data."""
        logger.info("M365: get_entra_health (mocked)")
        return {
            "success": True,
            "entra_health": {
                "status": "healthy",
                "sign_in_success_rate": 99.7,
                "total_sign_ins_24h": 4523,
                "failed_sign_ins_24h": 14,
                "mfa_success_rate": 99.2,
                "conditional_access_policies": 12,
                "active_policies": 12,
                "blocked_sign_ins_24h": 8,
                "risk_detections_24h": 3,
                "risky_users": 1,
                "deleted_objects_30d": 15,
                "password_reset_registrations": 1876,
                "self_service_password_resets_30d": 42,
            },
        }

    async def get_exchange_health(self) -> dict:
        """Return mocked Exchange Online health data."""
        logger.info("M365: get_exchange_health (mocked)")
        return {
            "success": True,
            "exchange_health": {
                "status": "healthy",
                "mailboxes_total": 1987,
                "mailboxes_active": 1945,
                "mailboxes_online": 1987,
                "daily_emails_sent": 23456,
                "daily_emails_received": 31234,
                "average_mailbox_size_gb": 12.4,
                "total_mailbox_size_gb": 24638.8,
                "dags_count": 2,
                "databases_count": 8,
                "database_availability": 99.99,
                "queue_length": 0,
                "transport_rules_count": 15,
                "connectors_count": 8,
            },
        }

    async def get_secure_score(self) -> dict:
        """Return mocked Secure Score data."""
        logger.info("M365: get_secure_score (mocked)")
        return {
            "success": True,
            "secure_score": {
                "current_score": 72.4,
                "max_score": 100,
                "percentage": 72.4,
                "comparison_to_industry": {
                    "your_score": 72.4,
                    "average_score": 58.2,
                    "tier": "above_average",
                },
                "categories": [
                    {
                        "name": "Identity",
                        "current_score": 18.5,
                        "max_score": 25,
                        "percentage": 74.0,
                    },
                    {
                        "name": "Devices",
                        "current_score": 14.2,
                        "max_score": 20,
                        "percentage": 71.0,
                    },
                    {
                        "name": "Apps",
                        "current_score": 11.8,
                        "max_score": 15,
                        "percentage": 78.7,
                    },
                    {
                        "name": "Data",
                        "current_score": 15.4,
                        "max_score": 25,
                        "percentage": 61.6,
                    },
                    {
                        "name": "Infrastructure",
                        "current_score": 12.5,
                        "max_score": 15,
                        "percentage": 83.3,
                    },
                ],
                "recommended_actions_count": 18,
                "high_priority_actions": 4,
                "last_calculated": datetime.now(UTC).isoformat(),
            },
        }

    async def get_message_center(self) -> dict:
        """Return mocked Message Center items."""
        logger.info("M365: get_message_center (mocked)")
        now = datetime.now(UTC).isoformat()
        return {
            "success": True,
            "message_center": {
                "total_items": 8,
                "items": [
                    {
                        "id": "MC123456",
                        "title": "Microsoft Teams: New meeting experience rolling out",
                        "category": "Stay Informed",
                        "severity": "Standard",
                        "message": (
                            "A new meeting experience will be "
                            "rolled out starting next month."
                        ),
                        "action_required": False,
                        "published_at": now,
                        "end_of_rollout": now,
                        "affected_services": ["Microsoft Teams"],
                        "compatibility_impact": "No action required",
                    },
                    {
                        "id": "MC123457",
                        "title": "Exchange Online: TLS 1.2 enforcement deadline",
                        "category": "Act Now",
                        "severity": "Critical",
                        "message": (
                            "TLS 1.0 and 1.1 will be disabled. "
                            "Ensure all clients support TLS 1.2."
                        ),
                        "action_required": True,
                        "published_at": now,
                        "end_of_rollout": now,
                        "affected_services": ["Exchange Online"],
                        "compatibility_impact": "Clients must support TLS 1.2",
                    },
                    {
                        "id": "MC123458",
                        "title": "SharePoint Online: Modernization of classic sites",
                        "category": "Stay Informed",
                        "severity": "Standard",
                        "message": (
                            "Classic SharePoint sites will begin "
                            "automated modernization."
                        ),
                        "action_required": False,
                        "published_at": now,
                        "end_of_rollout": now,
                        "affected_services": ["SharePoint Online"],
                        "compatibility_impact": "No action required",
                    },
                ],
            },
        }


m365_provider = MockMicrosoft365Provider()
