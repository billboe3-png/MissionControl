"""Mission Control Agent - Microsoft 365 plugin."""

import logging
import os
from typing import Any

from agent.plugin import AgentPlugin

logger = logging.getLogger("mc-agent")


class Microsoft365Plugin(AgentPlugin):
    """Microsoft 365 data collector plugin."""

    name = "microsoft_365"
    version = "3.0.0-rc1"
    description = "Microsoft 365 data collector"
    platform_required = None

    def __init__(self):
        self._context: dict[str, Any] = {}
        self._tenant_id = ""
        self._client_id = ""
        self._client_secret = ""
        self._token = ""

    async def initialize(self, context: dict[str, Any]) -> bool:
        self._context = context
        self._tenant_id = os.environ.get("MC_M365_TENANT_ID", "")
        self._client_id = os.environ.get("MC_M365_CLIENT_ID", "")
        self._client_secret = os.environ.get("MC_M365_CLIENT_SECRET", "")
        if self._tenant_id and self._client_id and self._client_secret:
            token = await self._get_token()
            if token:
                self._token = token
                logger.info("M365 plugin authenticated")
                return True
            logger.warning("M365 plugin auth failed")
            return False
        logger.info("M365 plugin not configured (set MC_M365_TENANT_ID/CLIENT_ID/CLIENT_SECRET)")
        return False

    async def _get_token(self) -> str | None:
        try:
            import httpx
            url = f"https://login.microsoftonline.com/{self._tenant_id}/oauth2/v2.0/token"
            data = {
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "scope": "https://graph.microsoft.com/.default",
            }
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(url, data=data)
                result = resp.json()
                return result.get("access_token")
        except Exception as e:
            logger.warning("M365 token acquisition failed: %s", e)
            return None

    async def _graph_get(self, endpoint: str) -> dict | None:
        if not self._token:
            return None
        try:
            import httpx
            headers = {"Authorization": f"Bearer {self._token}"}
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(f"https://graph.microsoft.com/v1.0/{endpoint}", headers=headers)
                return resp.json()
        except Exception as e:
            logger.warning("Graph API call failed: %s", e)
            return None

    async def collect_inventory(self) -> dict[str, Any]:
        if not self._token:
            return {"available": False, "error": "Not authenticated"}

        org = await self._graph_get("organization")
        users_data = await self._graph_get("users?$select=id,displayName,userPrincipalName,accountEnabled,assignedLicenses&$top=100")
        groups_data = await self._graph_get("groups?$select=id,displayName,description,groupTypes,visibility&$top=100")
        devices_data = await self._graph_get("deviceManagement/managedDevices?$select=id,deviceName,operatingSystem,complianceState,lastSyncDateTime&$top=100")
        health_data = await self._graph_get("admin/serviceAnnouncement/healthOverviews?$top=5")

        users = (users_data or {}).get("value", [])
        groups = (groups_data or {}).get("value", [])
        devices = (devices_data or {}).get("value", [])
        health = (health_data or {}).get("value", [])

        return {
            "available": True,
            "tenant": ((org or {}).get("value") or [{}])[0].get("displayName", ""),
            "users": users,
            "groups": groups,
            "devices": devices,
            "service_health": health,
        }

    async def execute_command(self, command: str, args: dict[str, Any]) -> dict[str, Any]:
        return {"success": False, "error": f"Unknown command: {command}"}
