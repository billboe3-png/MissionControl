"""
Mission Control Active Directory Provider (Mocked)

Returns mocked Active Directory data for development and testing.
No LDAP connections. No PowerShell execution.

Sprint 2.2.0 - Microsoft 365 & Active Directory Integration.
"""

import logging
from datetime import UTC, datetime

from app.providers.identity.base_provider import ActiveDirectoryProvider

logger = logging.getLogger(__name__)


class MockActiveDirectoryProvider(ActiveDirectoryProvider):
    """
    Mocked Active Directory provider.

    Returns realistic sample data for all AD operations.
    Used for development, testing, and UI scaffolding.
    """

    async def test_connection(self) -> dict:
        """Test AD connectivity (mocked)."""
        logger.info("AD: test_connection (mocked)")
        return {
            "connected": True,
            "latency_ms": 12,
            "message": "Mocked AD connection successful",
            "server": "DC01.corp.contoso.com",
            "domain": "corp.contoso.com",
        }

    async def get_summary(self) -> dict:
        """Return mocked domain/forest summary."""
        logger.info("AD: get_summary (mocked)")
        return {
            "connected": True,
            "domain": {
                "name": "corp.contoso.com",
                "netbios_name": "CORP",
                "functional_level": "Windows Server 2022",
                "domain_controllers": 3,
                "site_count": 2,
            },
            "forest": {
                "name": "corp.contoso.com",
                "functional_level": "Windows Server 2022",
                "domain_count": 2,
                "domains": [
                    "corp.contoso.com",
                    "child.corp.contoso.com",
                ],
                "global_catalog_count": 2,
            },
            "user_count": 1247,
            "group_count": 156,
            "computer_count": 834,
            "ou_count": 42,
        }

    async def get_users(self) -> dict:
        """Return mocked user summaries."""
        logger.info("AD: get_users (mocked)")
        return {
            "connected": True,
            "users": [
                {
                    "sam_account_name": "jbarnes",
                    "display_name": "Robert Barnes",
                    "email": "rbarnes@corp.contoso.com",
                    "department": "IT",
                    "title": "Systems Administrator",
                    "enabled": True,
                    "ou": "IT Department",
                },
                {
                    "sam_account_name": "asmith",
                    "display_name": "Alice Smith",
                    "email": "asmith@corp.contoso.com",
                    "department": "Engineering",
                    "title": "Senior Engineer",
                    "enabled": True,
                    "ou": "Corporate",
                },
                {
                    "sam_account_name": "mjones",
                    "display_name": "Mike Jones",
                    "email": "mjones@corp.contoso.com",
                    "department": "Sales",
                    "title": "Account Executive",
                    "enabled": False,
                    "ou": "Corporate",
                },
            ],
            "total_count": 1247,
            "enabled_count": 1198,
            "disabled_count": 49,
        }

    async def get_groups(self) -> dict:
        """Return mocked group summaries."""
        logger.info("AD: get_groups (mocked)")
        return {
            "connected": True,
            "groups": [
                {
                    "name": "Domain Admins",
                    "scope": "Universal",
                    "category": "Security",
                    "member_count": 5,
                    "description": "Designated administrators",
                },
                {
                    "name": "IT Department",
                    "scope": "Global",
                    "category": "Security",
                    "member_count": 45,
                    "description": "IT Department staff",
                },
                {
                    "name": "Engineering",
                    "scope": "Global",
                    "category": "Security",
                    "member_count": 128,
                    "description": "Engineering team",
                },
            ],
            "total_count": 156,
        }

    async def get_devices(self) -> dict:
        """Return mocked computer/device summaries."""
        logger.info("AD: get_devices (mocked)")
        return {
            "connected": True,
            "devices": [
                {
                    "name": "DC01",
                    "dns_name": "DC01.corp.contoso.com",
                    "ip_address": "10.0.1.10",
                    "os_version": "Windows Server 2022",
                    "enabled": True,
                    "is_domain_controller": True,
                    "ou": "Domain Controllers",
                },
                {
                    "name": "DC02",
                    "dns_name": "DC02.corp.contoso.com",
                    "ip_address": "10.0.1.11",
                    "os_version": "Windows Server 2022",
                    "enabled": True,
                    "is_domain_controller": True,
                    "ou": "Domain Controllers",
                },
                {
                    "name": "FILE01",
                    "dns_name": "FILE01.corp.contoso.com",
                    "ip_address": "10.0.1.50",
                    "os_version": "Windows Server 2022",
                    "enabled": True,
                    "is_domain_controller": False,
                    "ou": "IT Department",
                },
            ],
            "total_count": 834,
            "server_count": 45,
            "workstation_count": 789,
        }

    async def get_health(self) -> dict:
        """Return mocked AD health status."""
        logger.info("AD: get_health (mocked)")
        return {
            "connected": True,
            "status": "healthy",
            "replication": {
                "status": "healthy",
                "last_sync": datetime.now(UTC).isoformat(),
                "pending_replications": 0,
                "failed_replications": 0,
            },
            "domain_controllers": [
                {
                    "name": "DC01",
                    "status": "online",
                    "site": "Default-First-Site-Name",
                    "is_global_catalog": True,
                },
                {
                    "name": "DC02",
                    "status": "online",
                    "site": "Default-First-Site-Name",
                    "is_global_catalog": True,
                },
                {
                    "name": "DC03",
                    "status": "online",
                    "site": "Branch-Site",
                    "is_global_catalog": False,
                },
            ],
            "fsmo_roles": {
                "schema_master": "DC01.corp.contoso.com",
                "naming_master": "DC01.corp.contoso.com",
                "pdc_emulator": "DC01.corp.contoso.com",
                "rid_master": "DC01.corp.contoso.com",
                "infrastructure_master": "DC01.corp.contoso.com",
            },
        }


ad_provider = MockActiveDirectoryProvider()
