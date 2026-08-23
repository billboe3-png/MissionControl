"""Veeam B&R REST API client (folded from app/providers/veeam/veeam_provider.py)."""

import logging
import time
from typing import Any
from urllib.parse import urlparse

import httpx

logger = logging.getLogger("plugin.veeam.rest")

API_VERSION = "1.3-rev1"
TOKEN_PATH = "/api/oauth2/token"  # noqa: S105


class VeeamRestClient:
    """OAuth2 client-credentials REST client for Veeam B&R."""

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        verify_ssl: bool = True,
        timeout: int = 30,
    ) -> None:
        parsed = urlparse(base_url)
        self.base_url = f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self._token: str | None = None
        self._token_expires: float = 0

    async def _get_token(self) -> str:
        if self._token and time.time() < self._token_expires - 30:
            return self._token
        async with httpx.AsyncClient(verify=self.verify_ssl, timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}{TOKEN_PATH}",
                data={
                    "grant_type": "password",
                    "username": self.username,
                    "password": self.password,
                },
                headers={"x-api-version": API_VERSION},
            )
            resp.raise_for_status()
            data = resp.json()
            self._token = data["access_token"]
            self._token_expires = time.time() + data.get("expires_in", 3600)
            return self._token

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
            "x-api-version": API_VERSION,
        }

    async def get(self, path: str) -> dict[str, Any]:
        await self._get_token()
        async with httpx.AsyncClient(verify=self.verify_ssl, timeout=self.timeout) as client:
            resp = await client.get(f"{self.base_url}{path}", headers=self._headers())
            resp.raise_for_status()
            return resp.json()

    async def post(self, path: str, json: dict | None = None) -> dict[str, Any]:
        await self._get_token()
        async with httpx.AsyncClient(verify=self.verify_ssl, timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}{path}", headers=self._headers(), json=json,
            )
            resp.raise_for_status()
            return resp.json() if resp.content else {"success": True}

    async def test(self) -> dict[str, Any]:
        try:
            data = await self.get("/api/v1/serverInfo")
            return {
                "connected": True,
                "version": data.get("buildVersion", ""),
                "name": data.get("name", ""),
            }
        except Exception as exc:
            logger.debug("Veeam REST test failed: %s", exc)
            return {"connected": False, "version": "", "name": "", "error": str(exc)}


def _extract_items(data: Any) -> list:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("data", [])
    return []
