"""
Mission Control Active Directory Provider (Mocked)

Returns mocked Active Directory data for development and testing.
No LDAP connections. No PowerShell execution.

Sprint 2.2.1 - Identity Platform Foundation.
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

    async def get_domain_controllers(self) -> dict:
        """Return mocked domain controller data."""
        logger.info("AD: get_domain_controllers (mocked)")
        return {
            "success": True,
            "domain_controllers": [
                {
                    "name": "DC01",
                    "ip_address": "10.0.1.10",
                    "os_version": "Windows Server 2022",
                    "site": "Default-First-Site-Name",
                    "is_global_catalog": True,
                    "is_fsmo": True,
                    "status": "online",
                    "last_replication": datetime.now(UTC).isoformat(),
                },
                {
                    "name": "DC02",
                    "ip_address": "10.0.1.11",
                    "os_version": "Windows Server 2022",
                    "site": "Default-First-Site-Name",
                    "is_global_catalog": True,
                    "is_fsmo": False,
                    "status": "online",
                    "last_replication": datetime.now(UTC).isoformat(),
                },
                {
                    "name": "DC03",
                    "ip_address": "10.0.2.10",
                    "os_version": "Windows Server 2019",
                    "site": "Branch-Site",
                    "is_global_catalog": False,
                    "is_fsmo": False,
                    "status": "online",
                    "last_replication": datetime.now(UTC).isoformat(),
                },
            ],
            "total_count": 3,
        }

    async def get_forest(self) -> dict:
        """Return mocked forest information."""
        logger.info("AD: get_forest (mocked)")
        return {
            "success": True,
            "forest": {
                "name": "corp.contoso.com",
                "functional_level": "Windows Server 2022",
                "domain_count": 2,
                "domains": ["corp.contoso.com", "child.corp.contoso.com"],
                "global_catalog_count": 2,
                "site_count": 2,
                "sites": ["Default-First-Site-Name", "Branch-Site"],
                "schema_master": "DC01.corp.contoso.com",
                "naming_master": "DC01.corp.contoso.com",
            },
        }

    async def get_domain(self) -> dict:
        """Return mocked domain information."""
        logger.info("AD: get_domain (mocked)")
        return {
            "success": True,
            "domain": {
                "name": "corp.contoso.com",
                "netbios_name": "CORP",
                "functional_level": "Windows Server 2022",
                "sid": "S-1-5-21-1234567890-1234567890-1234567890",
                "pdc_emulator": "DC01.corp.contoso.com",
                "rid_master": "DC01.corp.contoso.com",
                "infrastructure_master": "DC01.corp.contoso.com",
                "domain_controllers": 3,
                "user_count": 1247,
                "computer_count": 834,
                "group_count": 156,
                "ou_count": 42,
                "password_policy": {
                    "min_length": 14,
                    "max_age_days": 90,
                    "history_count": 24,
                    "complexity_required": True,
                    "lockout_threshold": 5,
                    "lockout_duration_minutes": 30,
                },
            },
        }

    async def get_organizational_units(self) -> dict:
        """Return mocked organizational unit data."""
        logger.info("AD: get_organizational_units (mocked)")
        return {
            "success": True,
            "organizational_units": [
                {
                    "name": "Corporate",
                    "distinguished_name": "OU=Corporate,DC=corp,DC=contoso,DC=com",
                    "path": "corp.contoso.com/Corporate",
                    "user_count": 856,
                    "computer_count": 612,
                    "group_count": 89,
                    "child_ou_count": 8,
                    "gpo_count": 12,
                },
                {
                    "name": "IT Department",
                    "distinguished_name": (
                        "OU=IT Department,OU=Corporate,"
                        "DC=corp,DC=contoso,DC=com"
                    ),
                    "path": "corp.contoso.com/Corporate/IT Department",
                    "user_count": 45,
                    "computer_count": 78,
                    "group_count": 12,
                    "child_ou_count": 3,
                    "gpo_count": 5,
                },
                {
                    "name": "Branch Offices",
                    "distinguished_name": "OU=Branch Offices,DC=corp,DC=contoso,DC=com",
                    "path": "corp.contoso.com/Branch Offices",
                    "user_count": 391,
                    "computer_count": 222,
                    "group_count": 55,
                    "child_ou_count": 6,
                    "gpo_count": 8,
                },
                {
                    "name": "Service Accounts",
                    "distinguished_name": (
                        "OU=Service Accounts,"
                        "DC=corp,DC=contoso,DC=com"
                    ),
                    "path": "corp.contoso.com/Service Accounts",
                    "user_count": 23,
                    "computer_count": 0,
                    "group_count": 8,
                    "child_ou_count": 0,
                    "gpo_count": 2,
                },
            ],
            "total_count": 42,
        }

    async def get_users(self) -> dict:
        """Return mocked user summary data."""
        logger.info("AD: get_users (mocked)")
        return {
            "success": True,
            "users": [
                {
                    "sam_account_name": "jbarnes",
                    "display_name": "Robert Barnes",
                    "email": "rbarnes@corp.contoso.com",
                    "department": "IT",
                    "title": "Systems Administrator",
                    "enabled": True,
                    "locked_out": False,
                    "password_expired": False,
                    "last_logon": datetime.now(UTC).isoformat(),
                    "created_at": "2019-03-15T00:00:00Z",
                    "ou": "IT Department",
                },
                {
                    "sam_account_name": "asmith",
                    "display_name": "Alice Smith",
                    "email": "asmith@corp.contoso.com",
                    "department": "Engineering",
                    "title": "Senior Engineer",
                    "enabled": True,
                    "locked_out": False,
                    "password_expired": False,
                    "last_logon": datetime.now(UTC).isoformat(),
                    "created_at": "2020-07-22T00:00:00Z",
                    "ou": "Corporate",
                },
                {
                    "sam_account_name": "svc_backup",
                    "display_name": "Backup Service Account",
                    "email": None,
                    "department": "IT",
                    "title": "Service Account",
                    "enabled": True,
                    "locked_out": False,
                    "password_expired": False,
                    "last_logon": "2025-12-01T03:00:00Z",
                    "created_at": "2018-01-10T00:00:00Z",
                    "ou": "Service Accounts",
                },
                {
                    "sam_account_name": "mjones",
                    "display_name": "Mike Jones",
                    "email": "mjones@corp.contoso.com",
                    "department": "Sales",
                    "title": "Account Executive",
                    "enabled": False,
                    "locked_out": False,
                    "password_expired": True,
                    "last_logon": "2025-06-15T14:30:00Z",
                    "created_at": "2021-11-03T00:00:00Z",
                    "ou": "Corporate",
                },
            ],
            "total_count": 1247,
            "enabled_count": 1198,
            "disabled_count": 49,
            "locked_out_count": 2,
            "password_expired_count": 15,
        }

    async def get_groups(self) -> dict:
        """Return mocked group summary data."""
        logger.info("AD: get_groups (mocked)")
        return {
            "success": True,
            "groups": [
                {
                    "name": "Domain Admins",
                    "sam_account_name": "Domain Admins",
                    "scope": "Universal",
                    "category": "Security",
                    "member_count": 5,
                    "description": "Designated administrators of the domain",
                    "is_domain_local": False,
                    "managed_by": "jbarnes",
                },
                {
                    "name": "Enterprise Admins",
                    "sam_account_name": "Enterprise Admins",
                    "scope": "Universal",
                    "category": "Security",
                    "member_count": 3,
                    "description": "Designated administrators of the enterprise",
                    "is_domain_local": False,
                    "managed_by": "jbarnes",
                },
                {
                    "name": "IT Department",
                    "sam_account_name": "IT Department",
                    "scope": "Global",
                    "category": "Security",
                    "member_count": 45,
                    "description": "IT Department staff",
                    "is_domain_local": False,
                    "managed_by": "jbarnes",
                },
                {
                    "name": "Engineering",
                    "sam_account_name": "Engineering",
                    "scope": "Global",
                    "category": "Security",
                    "member_count": 128,
                    "description": "Engineering team",
                    "is_domain_local": False,
                    "managed_by": "asmith",
                },
                {
                    "name": "Remote Desktop Users",
                    "sam_account_name": "Remote Desktop Users",
                    "scope": "DomainLocal",
                    "category": "Security",
                    "member_count": 312,
                    "description": "Users who can access via Remote Desktop",
                    "is_domain_local": True,
                    "managed_by": None,
                },
            ],
            "total_count": 156,
        }

    async def get_computers(self) -> dict:
        """Return mocked computer summary data."""
        logger.info("AD: get_computers (mocked)")
        return {
            "success": True,
            "computers": [
                {
                    "name": "DC01",
                    "dns_name": "DC01.corp.contoso.com",
                    "ip_address": "10.0.1.10",
                    "os_version": "Windows Server 2022",
                    "enabled": True,
                    "last_logon": datetime.now(UTC).isoformat(),
                    "password_last_changed": "2025-01-15T00:00:00Z",
                    "ou": "Domain Controllers",
                    "is_domain_controller": True,
                },
                {
                    "name": "DC02",
                    "dns_name": "DC02.corp.contoso.com",
                    "ip_address": "10.0.1.11",
                    "os_version": "Windows Server 2022",
                    "enabled": True,
                    "last_logon": datetime.now(UTC).isoformat(),
                    "password_last_changed": "2025-01-15T00:00:00Z",
                    "ou": "Domain Controllers",
                    "is_domain_controller": True,
                },
                {
                    "name": "FILE01",
                    "dns_name": "FILE01.corp.contoso.com",
                    "ip_address": "10.0.1.50",
                    "os_version": "Windows Server 2022",
                    "enabled": True,
                    "last_logon": datetime.now(UTC).isoformat(),
                    "password_last_changed": "2025-06-01T00:00:00Z",
                    "ou": "IT Department",
                    "is_domain_controller": False,
                },
                {
                    "name": "WEB01",
                    "dns_name": "WEB01.corp.contoso.com",
                    "ip_address": "10.0.1.60",
                    "os_version": "Windows Server 2022",
                    "enabled": True,
                    "last_logon": datetime.now(UTC).isoformat(),
                    "password_last_changed": "2025-03-20T00:00:00Z",
                    "ou": "Corporate",
                    "is_domain_controller": False,
                },
            ],
            "total_count": 834,
            "enabled_count": 801,
            "disabled_count": 33,
            "server_count": 45,
            "workstation_count": 789,
        }

    async def get_gpos(self) -> dict:
        """Return mocked Group Policy Object data."""
        logger.info("AD: get_gpos (mocked)")
        return {
            "success": True,
            "gpos": [
                {
                    "name": "Default Domain Policy",
                    "guid": "31B2F340-016D-11D2-945F-00C04FB984F9",
                    "description": "Default Group Policy for the domain",
                    "version": 47,
                    "enabled": True,
                    "linked_ous": ["corp.contoso.com"],
                    "computer_count": 834,
                    "user_count": 1247,
                    "created_at": "2018-01-01T00:00:00Z",
                    "modified_at": datetime.now(UTC).isoformat(),
                },
                {
                    "name": "Workstation Security",
                    "guid": "A1B2C3D4-E5F6-7890-ABCD-EF1234567890",
                    "description": "Security settings for workstation computers",
                    "version": 12,
                    "enabled": True,
                    "linked_ous": ["OU=Corporate,DC=corp,DC=contoso,DC=com"],
                    "computer_count": 789,
                    "user_count": 0,
                    "created_at": "2020-03-15T00:00:00Z",
                    "modified_at": "2025-09-01T00:00:00Z",
                },
                {
                    "name": "Server Hardening",
                    "guid": "B2C3D4E5-F6A7-8901-BCDE-F12345678901",
                    "description": "Security hardening for server infrastructure",
                    "version": 8,
                    "enabled": True,
                    "linked_ous": [
                        "OU=IT Department,OU=Corporate,"
                        "DC=corp,DC=contoso,DC=com"
                    ],
                    "computer_count": 45,
                    "user_count": 0,
                    "created_at": "2021-06-01T00:00:00Z",
                    "modified_at": "2025-11-15T00:00:00Z",
                },
                {
                    "name": "Branch Office Policy",
                    "guid": "C3D4E5F6-A7B8-9012-CDEF-123456789012",
                    "description": "Policy for branch office computers and users",
                    "version": 5,
                    "enabled": True,
                    "linked_ous": ["OU=Branch Offices,DC=corp,DC=contoso,DC=com"],
                    "computer_count": 222,
                    "user_count": 391,
                    "created_at": "2022-01-10T00:00:00Z",
                    "modified_at": "2025-08-20T00:00:00Z",
                },
            ],
            "total_count": 27,
            "enabled_count": 25,
            "disabled_count": 2,
        }

    async def get_fsmo_roles(self) -> dict:
        """Return mocked FSMO role holder data."""
        logger.info("AD: get_fsmo_roles (mocked)")
        return {
            "success": True,
            "forest_roles": {
                "schema_master": {
                    "role": "Schema Master",
                    "holder": "DC01.corp.contoso.com",
                    "status": "online",
                },
                "naming_master": {
                    "role": "Domain Naming Master",
                    "holder": "DC01.corp.contoso.com",
                    "status": "online",
                },
            },
            "domain_roles": {
                "pdc_emulator": {
                    "role": "PDC Emulator",
                    "holder": "DC01.corp.contoso.com",
                    "status": "online",
                },
                "rid_master": {
                    "role": "RID Master",
                    "holder": "DC01.corp.contoso.com",
                    "status": "online",
                },
                "infrastructure_master": {
                    "role": "Infrastructure Master",
                    "holder": "DC01.corp.contoso.com",
                    "status": "online",
                },
            },
            "all_roles_held_by_single_dc": True,
        }

    async def get_dns_health(self) -> dict:
        """Return mocked DNS health data."""
        logger.info("AD: get_dns_health (mocked)")
        return {
            "success": True,
            "dns_health": {
                "status": "healthy",
                "servers": [
                    {
                        "name": "DC01",
                        "ip_address": "10.0.1.10",
                        "status": "healthy",
                        "zones_count": 5,
                        "records_count": 2847,
                        "forwarders": ["8.8.8.8", "8.8.4.4"],
                        "response_time_ms": 2,
                    },
                    {
                        "name": "DC02",
                        "ip_address": "10.0.1.11",
                        "status": "healthy",
                        "zones_count": 5,
                        "records_count": 2847,
                        "forwarders": ["8.8.8.8", "8.8.4.4"],
                        "response_time_ms": 3,
                    },
                    {
                        "name": "DC03",
                        "ip_address": "10.0.2.10",
                        "status": "healthy",
                        "zones_count": 3,
                        "records_count": 1203,
                        "forwarders": ["8.8.8.8", "8.8.4.4"],
                        "response_time_ms": 5,
                    },
                ],
                "total_zones": 8,
                "total_records": 6897,
                "dnssec_enabled": True,
            },
        }

    async def get_dhcp_health(self) -> dict:
        """Return mocked DHCP health data."""
        logger.info("AD: get_dhcp_health (mocked)")
        return {
            "success": True,
            "dhcp_health": {
                "status": "healthy",
                "servers": [
                    {
                        "name": "DC01",
                        "ip_address": "10.0.1.10",
                        "status": "healthy",
                        "scopes_count": 3,
                        "total_addresses": 750,
                        "used_addresses": 512,
                        "available_addresses": 238,
                        "utilization_percent": 68.3,
                    },
                    {
                        "name": "DC02",
                        "ip_address": "10.0.1.11",
                        "status": "healthy",
                        "scopes_count": 3,
                        "total_addresses": 750,
                        "used_addresses": 498,
                        "available_addresses": 252,
                        "utilization_percent": 66.4,
                    },
                ],
                "total_scopes": 6,
                "total_addresses": 1500,
                "total_used": 1010,
                "total_available": 490,
                "overall_utilization_percent": 67.3,
                "authorized": True,
            },
        }


ad_provider = MockActiveDirectoryProvider()
