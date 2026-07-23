"""
Mission Control Microsoft 365 Provider (Microsoft Graph)

Production Microsoft 365 provider using Microsoft Graph API.
Read-only operations against Microsoft 365 tenant.

Sprint 2.2.0 - Microsoft 365 & Active Directory Integration.

Features:
- OAuth2 client credentials authentication via MSAL
- Tenant information retrieval
- User, group, and device enumeration
- Subscribed SKU and license summary
- Service health monitoring
- Never raises exceptions to caller
"""

import logging
import time

from app.providers.identity.base_provider import Microsoft365Provider

logger = logging.getLogger(__name__)


def _get_m365_config() -> dict:
    """Get M365 configuration from settings."""
    try:
        from app.core.config import get_settings

        settings = get_settings()
        return {
            "tenant_id": settings.m365_tenant_id,
            "client_id": settings.m365_client_id,
            "client_secret": settings.m365_client_secret,
        }
    except Exception:
        return {
            "tenant_id": "",
            "client_id": "",
            "client_secret": "",
        }


class GraphMicrosoft365Provider(Microsoft365Provider):
    """
    Production Microsoft 365 provider using Microsoft Graph API.

    Authenticates via OAuth2 client credentials and performs
    read-only operations against the Microsoft 365 tenant.
    All methods return standardized dicts and never raise exceptions.
    """

    GRAPH_BASE = "https://graph.microsoft.com/v1.0"

    def __init__(self, config: dict | None = None) -> None:
        self._token: str | None = None
        self._config_override = config

    def _is_configured(self) -> bool:
        """Check if M365 is configured."""
        config = self._config_override or _get_m365_config()
        return bool(config["tenant_id"] and config["client_id"])

    def _get_token(self) -> str | None:
        """Get OAuth2 access token via client credentials."""
        if self._token:
            return self._token

        config = self._config_override or _get_m365_config()

        try:
            import msal

            authority = (
                f"https://login.microsoftonline.com/"
                f"{config['tenant_id']}"
            )
            app = msal.ConfidentialClientApplication(
                config["client_id"],
                authority=authority,
                client_credential=config["client_secret"],
            )

            result = app.acquire_token_for_client(
                scopes=["https://graph.microsoft.com/.default"]
            )

            if "access_token" in result:
                self._token = result["access_token"]
                return self._token

            logger.warning(
                "M365: token acquisition failed: %s",
                result.get("error", "unknown"),
            )
            return None
        except Exception as e:
            logger.warning(
                "M365: token acquisition error: %s",
                type(e).__name__,
            )
            return None

    def _graph_get(self, endpoint: str) -> dict | None:
        """Execute a GET request against Microsoft Graph."""
        token = self._get_token()
        if not token:
            return None

        try:
            import requests

            url = f"{self.GRAPH_BASE}{endpoint}"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
            response = requests.get(
                url, headers=headers, timeout=30
            )

            if response.status_code == 200:
                return response.json()

            logger.warning(
                "M365: Graph GET %s returned %d",
                endpoint,
                response.status_code,
            )
            return None
        except Exception as e:
            logger.warning(
                "M365: Graph GET failed: %s", type(e).__name__
            )
            return None

    # ------------------------------------------------------------------ #
    # Standardized Interface                                              #
    # ------------------------------------------------------------------ #

    async def test_connection(self) -> dict:
        """Test connectivity to Microsoft 365 via Graph API."""
        config = _get_m365_config()

        if not config["tenant_id"]:
            return {
                "connected": False,
                "error": "M365_TENANT_ID not configured",
            }

        start = time.monotonic()
        data = self._graph_get("/organization")
        latency_ms = int((time.monotonic() - start) * 1000)

        if data and "value" in data and len(data["value"]) > 0:
            org = data["value"][0]
            return {
                "connected": True,
                "latency_ms": latency_ms,
                "message": "Graph API connection successful",
                "tenant": org.get("displayName", "Unknown"),
                "tenant_id": config["tenant_id"],
            }

        return {
            "connected": False,
            "error": "Failed to connect to Microsoft Graph",
            "latency_ms": latency_ms,
        }

    async def get_summary(self) -> dict:
        """Get tenant summary via Graph API."""
        if not self._is_configured():
            return {"connected": False, "error": "M365 not configured"}

        org = self._graph_get("/organization")
        skus = self._graph_get("/subscribedSkUs")

        if not org or "value" not in org:
            return {
                "connected": False,
                "error": "Failed to retrieve tenant info",
            }

        tenant = org["value"][0]
        domains = self._graph_get("/domains") or {"value": []}

        license_summary = []
        total_assigned = 0
        if skus and "value" in skus:
            for sku in skus["value"]:
                assigned = sku.get("prepaidUnits", {}).get(
                    "enabled", 0
                )
                total = sku.get("capabilityStatus", "Enabled")
                license_summary.append({
                    "sku": sku.get("skuPartNumber", ""),
                    "name": sku.get("skuPartNumber", ""),
                    "assigned": assigned,
                    "status": total,
                })
                total_assigned += assigned

        return {
            "connected": True,
            "tenant": {
                "id": tenant.get("id", ""),
                "display_name": tenant.get("displayName", ""),
                "verified_domains": [
                    d["id"]
                    for d in domains.get("value", [])
                ],
                "tenant_type": "AAD",
            },
            "licensed_users": total_assigned,
            "licenses": license_summary,
            "domains": [
                d["id"] for d in domains.get("value", [])
            ],
        }

    async def get_users(self) -> dict:
        """List users via Graph API."""
        if not self._is_configured():
            return {"connected": False, "error": "M365 not configured"}

        data = self._graph_get(
            "/users?$select=displayName,mail,"
            "department,jobTitle,accountEnabled"
            "&$top=100"
        )

        if not data or "value" not in data:
            return {
                "connected": False,
                "error": "Failed to retrieve users",
            }

        users = []
        for u in data["value"]:
            users.append({
                "display_name": u.get("displayName", ""),
                "email": u.get("mail"),
                "department": u.get("department", ""),
                "job_title": u.get("jobTitle", ""),
                "enabled": u.get("accountEnabled", False),
            })

        return {
            "connected": True,
            "users": users,
            "total_count": len(users),
        }

    async def get_groups(self) -> dict:
        """List groups via Graph API."""
        if not self._is_configured():
            return {"connected": False, "error": "M365 not configured"}

        data = self._graph_get(
            "/groups?$select=displayName,mail,"
            "groupTypes&$top=100"
        )

        if not data or "value" not in data:
            return {
                "connected": False,
                "error": "Failed to retrieve groups",
            }

        groups = []
        for g in data["value"]:
            groups.append({
                "display_name": g.get("displayName", ""),
                "mail": g.get("mail"),
                "type": (
                    "Unified"
                    if "Unified" in g.get("groupTypes", [])
                    else "Security"
                ),
            })

        return {
            "connected": True,
            "groups": groups,
            "total_count": len(groups),
        }

    async def get_devices(self) -> dict:
        """List managed devices via Graph API (Intune)."""
        if not self._is_configured():
            return {"connected": False, "error": "M365 not configured"}

        data = self._graph_get(
            "/deviceManagement/managedDevices"
            "?$select=deviceName,operatingSystem,"
            "osVersion,isCompliant"
            "&$top=100"
        )

        if not data or "value" not in data:
            return {
                "connected": True,
                "devices": [],
                "total_count": 0,
                "message": "Intune API not available",
            }

        devices = []
        for d in data["value"]:
            devices.append({
                "name": d.get("deviceName", ""),
                "os": d.get("operatingSystem", ""),
                "version": d.get("osVersion", ""),
                "compliant": d.get("isCompliant", False),
            })

        return {
            "connected": True,
            "devices": devices,
            "total_count": len(devices),
        }

    async def get_health(self) -> dict:
        """Get service health via Graph API."""
        if not self._is_configured():
            return {"connected": False, "error": "M365 not configured"}

        data = self._graph_get(
            "/serviceHealth?$top=5"
        )

        if not data or "value" not in data:
            return {
                "connected": True,
                "status": "unknown",
                "services": [],
                "message": "Service health API not available",
            }

        services = []
        for item in data["value"]:
            services.append({
                "name": item.get("service", "Unknown"),
                "status": item.get("status", "unknown"),
            })

        return {
            "connected": True,
            "status": "healthy",
            "services": services,
            "active_incidents": len([
                s for s in services if s["status"] != "serviceOperational"
            ]),
        }
