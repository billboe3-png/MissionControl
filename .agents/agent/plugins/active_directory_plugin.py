"""Mission Control Agent - Active Directory plugin."""

import logging
import os
from typing import Any

from agent.plugin import AgentPlugin

logger = logging.getLogger("mc-agent")


class ActiveDirectoryPlugin(AgentPlugin):
    """Active Directory data collector plugin."""

    name = "active_directory"
    version = "3.0.0-rc1"
    description = "Active Directory data collector"
    platform_required = None

    def __init__(self):
        self._context: dict[str, Any] = {}
        self._server = ""
        self._username = ""
        self._password = ""
        self._base_dn = ""

    async def initialize(self, context: dict[str, Any]) -> bool:
        self._context = context
        self._server = os.environ.get("MC_AD_SERVER", "")
        self._username = os.environ.get("MC_AD_USERNAME", "")
        self._password = os.environ.get("MC_AD_PASSWORD", "")
        self._base_dn = os.environ.get("MC_AD_BASE_DN", "")
        if self._server and self._username and self._password:
            logger.info("AD plugin configured for %s", self._server)
            return True
        logger.info("AD plugin not configured (set MC_AD_SERVER/USERNAME/PASSWORD)")
        return False

    async def collect_inventory(self) -> dict[str, Any]:
        if not self._server:
            return {"available": False}

        try:
            import ldap3
            server = ldap3.Server(self._server, get_info=ldap3.ALL)
            conn = ldap3.Connection(server, self._username, self._password, auto_bind=True)
            base_dn = self._base_dn or server.info.other.get("defaultNamingContext", [""])[0]

            conn.search(base_dn, "(objectClass=user)", attributes=["sAMAccountName", "displayName", "userAccountControl", "mail", "department"], size_limit=500)
            users = [{"sam": str(e.entry_dn), **{a: str(v) for a, v in e.entry_attributes_as_dict.items()}} for e in conn.entries]

            conn.search(base_dn, "(objectClass=group)", attributes=["sAMAccountName", "description", "member"], size_limit=200)
            groups = [{"sam": str(e.entry_dn), **{a: str(v) for a, v in e.entry_attributes_as_dict.items()}} for e in conn.entries]

            conn.search(base_dn, "(objectClass=computer)", attributes=["sAMAccountName", "operatingSystem"], size_limit=200)
            devices = [{"sam": str(e.entry_dn), **{a: str(v) for a, v in e.entry_attributes_as_dict.items()}} for e in conn.entries]

            conn.unbind()
            return {
                "available": True,
                "domain": base_dn,
                "forest": str(server.info.other.get("rootDomainNamingContext", [""])[0]),
                "users": users,
                "groups": groups,
                "devices": devices,
            }
        except Exception as e:
            logger.warning("AD inventory collection failed: %s", e)
            return {"available": False, "error": str(e)}

    async def execute_command(self, command: str, args: dict[str, Any]) -> dict[str, Any]:
        return {"success": False, "error": f"Unknown command: {command}"}
