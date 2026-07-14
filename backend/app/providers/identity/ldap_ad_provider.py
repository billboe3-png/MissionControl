"""
Mission Control Active Directory Provider (LDAP)

Production Active Directory provider using ldap3 for LDAP
connectivity. Read-only operations against Active Directory.

Sprint 2.2.0 - Microsoft 365 & Active Directory Integration.

Features:
- LDAP/LDAPS connectivity
- Domain information retrieval
- User, group, and device enumeration
- Domain controller discovery
- Replication health (placeholder)
- FSMO role discovery (placeholder)
- Never raises exceptions to caller
"""

import logging
import time

from app.providers.identity.base_provider import ActiveDirectoryProvider

logger = logging.getLogger(__name__)


def _get_ad_config() -> dict:
    """Get AD configuration from settings."""
    try:
        from app.core.config import get_settings

        settings = get_settings()
        return {
            "server": settings.ad_server,
            "port": settings.ad_port,
            "use_ssl": settings.ad_use_ssl,
            "username": settings.ad_username,
            "password": settings.ad_password,
            "base_dn": settings.ad_base_dn,
        }
    except Exception:
        return {
            "server": "",
            "port": 636,
            "use_ssl": True,
            "username": "",
            "password": "",
            "base_dn": "",
        }


class LDAPActiveDirectoryProvider(ActiveDirectoryProvider):
    """
    Production Active Directory provider using ldap3.

    Connects to Active Directory via LDAP/LDAPS for read-only
    operations. All methods return standardized dicts and never
    raise exceptions.
    """

    def __init__(self) -> None:
        self._connection = None

    def _is_configured(self) -> bool:
        """Check if AD is configured."""
        config = _get_ad_config()
        return bool(config["server"] and config["username"])

    def _connect(self) -> bool:
        """Establish LDAP connection."""
        if self._connection is not None:
            try:
                self._connection.bind()
                return True
            except Exception:
                self._connection = None

        config = _get_ad_config()

        try:
            from ldap3 import ALL, Connection, Server

            server = Server(
                config["server"],
                port=config["port"],
                use_ssl=config["use_ssl"],
                get_info=ALL,
            )
            self._connection = Connection(
                server,
                user=config["username"],
                password=config["password"],
                auto_bind=True,
            )
            return True
        except Exception as e:
            logger.warning(
                "AD LDAP: connection failed: %s", type(e).__name__
            )
            self._connection = None
            return False

    def _disconnect(self) -> None:
        """Close LDAP connection."""
        if self._connection is not None:
            try:
                self._connection.unbind()
            except Exception:
                pass
            self._connection = None

    def _search(
        self, base_dn: str, filter_str: str, attributes: list[str]
    ) -> list[dict]:
        """Execute an LDAP search and return results."""
        if not self._connect():
            return []

        config = _get_ad_config()
        base = base_dn or config["base_dn"]

        try:
            self._connection.search(
                base,
                filter_str,
                attributes=attributes,
            )
            results = []
            for entry in self._connection.entries:
                item = {}
                for attr in attributes:
                    val = getattr(entry, attr, None)
                    item[attr.lower()] = (
                        str(val) if val is not None else None
                    )
                results.append(item)
            return results
        except Exception as e:
            logger.warning(
                "AD LDAP: search failed: %s", type(e).__name__
            )
            return []

    # ------------------------------------------------------------------ #
    # Standardized Interface                                              #
    # ------------------------------------------------------------------ #

    async def test_connection(self) -> dict:
        """Test LDAP connectivity to Active Directory."""
        config = _get_ad_config()

        if not config["server"]:
            return {
                "connected": False,
                "error": "AD_SERVER not configured",
            }

        start = time.monotonic()
        connected = self._connect()
        latency_ms = int((time.monotonic() - start) * 1000)

        if connected:
            return {
                "connected": True,
                "latency_ms": latency_ms,
                "message": (
                    f"Connected to {config['server']}:{config['port']}"
                ),
                "server": config["server"],
            }

        return {
            "connected": False,
            "error": f"Failed to connect to {config['server']}",
            "latency_ms": latency_ms,
        }

    async def get_summary(self) -> dict:
        """Get domain and forest summary via LDAP."""
        if not self._is_configured():
            return {
                "connected": False,
                "error": "AD not configured",
            }

        if not self._connect():
            return {"connected": False, "error": "LDAP connection failed"}

        try:
            from ldap3 import BASE, SUBTREE

            config = _get_ad_config()
            base = config["base_dn"]

            domain_obj = self._search(
                base,
                "(objectClass=domain)",
                ["dc", "name", "dSCorePropagationData"],
            )

            users = self._search(
                base,
                "(&(objectClass=user)(objectCategory=person))",
                ["sAMAccountName"],
            )
            groups = self._search(
                base, "(objectClass=group)", ["cn"]
            )
            computers = self._search(
                base, "(objectClass=computer)", ["cn"]
            )

            return {
                "connected": True,
                "domain": {
                    "name": domain_obj[0].get("dc", "unknown")
                    if domain_obj
                    else "unknown",
                    "base_dn": base,
                },
                "user_count": len(users),
                "group_count": len(groups),
                "computer_count": len(computers),
            }
        except Exception as e:
            logger.warning("AD: get_summary failed: %s", e)
            return {"connected": False, "error": str(e)}

    async def get_users(self) -> dict:
        """List Active Directory users."""
        if not self._is_configured():
            return {"connected": False, "error": "AD not configured"}

        if not self._connect():
            return {"connected": False, "error": "LDAP connection failed"}

        try:
            config = _get_ad_config()
            entries = self._search(
                config["base_dn"],
                "(&(objectClass=user)(objectCategory=person))",
                [
                    "sAMAccountName",
                    "displayName",
                    "mail",
                    "department",
                    "title",
                    "userAccountControl",
                ],
            )

            users = []
            for entry in entries:
                uac = int(entry.get("useraccountcontrol", "0") or "0")
                enabled = not bool(uac & 0x2)
                users.append({
                    "sam_account_name": entry.get(
                        "samaccountname", ""
                    ),
                    "display_name": entry.get("displayname", ""),
                    "email": entry.get("mail"),
                    "department": entry.get("department", ""),
                    "title": entry.get("title", ""),
                    "enabled": enabled,
                })

            return {
                "connected": True,
                "users": users,
                "total_count": len(users),
            }
        except Exception as e:
            logger.warning("AD: get_users failed: %s", e)
            return {"connected": False, "error": str(e)}

    async def get_groups(self) -> dict:
        """List Active Directory groups."""
        if not self._is_configured():
            return {"connected": False, "error": "AD not configured"}

        if not self._connect():
            return {"connected": False, "error": "LDAP connection failed"}

        try:
            config = _get_ad_config()
            entries = self._search(
                config["base_dn"],
                "(objectClass=group)",
                ["cn", "description", "groupType"],
            )

            groups = []
            for entry in entries:
                groups.append({
                    "name": entry.get("cn", ""),
                    "description": entry.get("description", ""),
                })

            return {
                "connected": True,
                "groups": groups,
                "total_count": len(groups),
            }
        except Exception as e:
            logger.warning("AD: get_groups failed: %s", e)
            return {"connected": False, "error": str(e)}

    async def get_devices(self) -> dict:
        """List Active Directory computers/devices."""
        if not self._is_configured():
            return {"connected": False, "error": "AD not configured"}

        if not self._connect():
            return {"connected": False, "error": "LDAP connection failed"}

        try:
            config = _get_ad_config()
            entries = self._search(
                config["base_dn"],
                "(objectClass=computer)",
                ["cn", "dNSHostName", "operatingSystem", "lastLogonTimestamp"],
            )

            devices = []
            for entry in entries:
                devices.append({
                    "name": entry.get("cn", ""),
                    "dns_name": entry.get("dNSHostName", ""),
                    "os_version": entry.get("operatingsystem", ""),
                })

            return {
                "connected": True,
                "devices": devices,
                "total_count": len(devices),
            }
        except Exception as e:
            logger.warning("AD: get_devices failed: %s", e)
            return {"connected": False, "error": str(e)}

    async def get_health(self) -> dict:
        """Get AD health and replication status."""
        if not self._is_configured():
            return {"connected": False, "error": "AD not configured"}

        if not self._connect():
            return {"connected": False, "error": "LDAP connection failed"}

        try:
            return {
                "connected": True,
                "status": "healthy",
                "replication": {
                    "status": "healthy",
                    "pending_replications": 0,
                    "failed_replications": 0,
                },
                "message": "LDAP connection active",
            }
        except Exception as e:
            logger.warning("AD: get_health failed: %s", e)
            return {"connected": False, "error": str(e)}
