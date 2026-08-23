"""
Zabbix Plugin API Client

Async HTTP client wrapping Zabbix JSON-RPC API.
Handles authentication, retries, and session management.
"""

import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger("plugin.zabbix.api")

SEVERITY_MAP: dict[int, str] = {
    0: "not_classified",
    1: "information",
    2: "warning",
    3: "average",
    4: "high",
    5: "disaster",
}


class ZabbixApiClient:
    """Async Zabbix JSON-RPC client."""

    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        verify_ssl: bool = True,
        timeout: int = 30,
        retries: int = 3,
    ) -> None:
        self._url = url.rstrip("/")
        self._username = username
        self._password = password
        self._verify_ssl = verify_ssl
        self._timeout = timeout
        self._retries = retries
        self._auth_token: str | None = None
        self._request_id = 0
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                verify=self._verify_ssl,
                timeout=httpx.Timeout(self._timeout),
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    async def _call(
        self, method: str, params: dict[str, Any] | None = None, auth: bool = True
    ) -> Any:
        """Execute a JSON-RPC call with retries."""
        client = await self._get_client()
        url = f"{self._url}/api_jsonrpc.php"
        payload: dict[str, Any] = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": self._next_id(),
        }
        headers: dict[str, str] = {"Content-Type": "application/json-rpc"}
        if auth and self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"

        last_error: Exception | None = None
        for attempt in range(1, self._retries + 1):
            try:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                result = resp.json()
                if "error" in result:
                    code = result["error"].get("code")
                    data = result["error"].get("data")
                    logger.warning("JSON-RPC error %s: %s", code, data)
                    raise RuntimeError(f"Zabbix API error {code}: {data}")
                return result.get("result")
            except (httpx.HTTPError, RuntimeError) as exc:
                last_error = exc
                logger.debug("Attempt %d/%d failed: %s", attempt, self._retries, exc)
                if attempt < self._retries:
                    await asyncio.sleep(1)
        raise RuntimeError(
            f"Zabbix API call '{method}' failed after {self._retries} attempts: {last_error}"
        )

    # ------------------------------------------------------------------ #
    # Auth                                                                #
    # ------------------------------------------------------------------ #

    async def login(self) -> str:
        """Authenticate and return auth token."""
        token = await self._call(
            "user.login",
            {"username": self._username, "password": self._password},
            auth=False,
        )
        self._auth_token = token
        return token

    async def ensure_auth(self) -> str:
        """Ensure we have a valid token, logging in if needed."""
        if self._auth_token:
            return self._auth_token
        return await self.login()

    # ------------------------------------------------------------------ #
    # Read operations                                                     #
    # ------------------------------------------------------------------ #

    async def api_version(self) -> str:
        return await self._call("apiinfo.version", auth=False)

    async def get_hosts(self) -> list[dict[str, Any]]:
        """Fetch all monitored hosts."""
        await self.ensure_auth()
        return await self._call(
            "host.get",
            {
                "output": ["hostid", "host", "name", "status", "available"],
                "selectInterfaces": ["ip"],
                "selectGroups": ["name"],
                "selectParentTemplates": ["name"],
                "sortfield": "host",
            },
        )

    async def get_problems(self, limit: int = 100) -> list[dict[str, Any]]:
        """Fetch current problems (active trigger events)."""
        await self.ensure_auth()
        return await self._call(
            "event.get",
            {
                "output": ["eventid", "name", "severity", "acknowledged", "clock"],
                "selectHosts": ["hostid", "host"],
                "sortfield": "eventid",
                "sortorder": "DESC",
                "limit": limit,
                "value": 1,
            },
        )

    async def get_events(self, limit: int = 100) -> list[dict[str, Any]]:
        """Fetch recent events."""
        await self.ensure_auth()
        return await self._call(
            "event.get",
            {
                "output": ["eventid", "name", "severity", "value", "clock"],
                "selectHosts": ["hostid", "host"],
                "sortfield": "eventid",
                "sortorder": "DESC",
                "limit": limit,
            },
        )

    async def get_triggers(self, limit: int = 100) -> list[dict[str, Any]]:
        """Fetch triggers."""
        await self.ensure_auth()
        return await self._call(
            "trigger.get",
            {
                "output": ["triggerid", "description", "status", "priority", "value"],
                "selectHosts": ["hostid", "host"],
                "sortfield": "priority",
                "sortorder": "DESC",
                "limit": limit,
            },
        )

    async def test_connection(self) -> dict[str, Any]:
        """Test connectivity without side effects."""
        try:
            version = await self.api_version()
            return {"connected": True, "version": version}
        except Exception as exc:
            return {"connected": False, "error": str(exc)}

    # ------------------------------------------------------------------ #
    # Synchronous wrappers (for use from background threads)               #
    # ------------------------------------------------------------------ #

    def _call_sync(
        self, method: str, params: dict[str, Any] | None = None, auth: bool = True
    ) -> Any:
        """Execute a JSON-RPC call synchronously with retries."""
        url = f"{self._url}/api_jsonrpc.php"
        payload: dict[str, Any] = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": self._next_id(),
        }
        headers: dict[str, str] = {"Content-Type": "application/json-rpc"}
        if auth and self._auth_token:
            headers["Authorization"] = f"Bearer {self._auth_token}"

        import time
        last_error: Exception | None = None
        with httpx.Client(
            verify=self._verify_ssl,
            timeout=httpx.Timeout(self._timeout),
        ) as client:
            for attempt in range(1, self._retries + 1):
                try:
                    resp = client.post(url, json=payload, headers=headers)
                    resp.raise_for_status()
                    result = resp.json()
                    if "error" in result:
                        code = result["error"].get("code")
                        data = result["error"].get("data")
                        raise RuntimeError(f"Zabbix API error {code}: {data}")
                    return result.get("result")
                except (httpx.HTTPError, RuntimeError) as exc:
                    last_error = exc
                    if attempt < self._retries:
                        time.sleep(1)
        raise RuntimeError(
            f"Zabbix API call '{method}' failed after {self._retries} attempts: {last_error}"
        )

    def login_sync(self) -> str:
        token = self._call_sync(
            "user.login",
            {"username": self._username, "password": self._password},
            auth=False,
        )
        self._auth_token = token
        return token

    def ensure_auth_sync(self) -> str:
        if self._auth_token:
            return self._auth_token
        return self.login_sync()

    def get_hosts_sync(self) -> list[dict[str, Any]]:
        self.ensure_auth_sync()
        return self._call_sync(
            "host.get",
            {
                "output": [
                    "hostid", "host", "name", "status",
                    "active_available", "passive_available",
                ],
                "selectInterfaces": ["ip"],
                "selectGroups": ["name"],
                "selectParentTemplates": ["name"],
                "sortfield": "host",
            },
        )

    def get_problems_sync(self, limit: int = 100) -> list[dict[str, Any]]:
        self.ensure_auth_sync()
        return self._call_sync(
            "event.get",
            {
                "output": ["eventid", "name", "severity", "acknowledged", "clock"],
                "selectHosts": ["hostid", "host"],
                "sortfield": "eventid",
                "sortorder": "DESC",
                "limit": limit,
                "value": 1,
            },
        )

    def get_events_sync(self, limit: int = 100) -> list[dict[str, Any]]:
        self.ensure_auth_sync()
        return self._call_sync(
            "event.get",
            {
                "output": ["eventid", "name", "severity", "value", "clock"],
                "selectHosts": ["hostid", "host"],
                "sortfield": "eventid",
                "sortorder": "DESC",
                "limit": limit,
            },
        )
