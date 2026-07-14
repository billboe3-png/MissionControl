"""Mission Control Agent - HTTP client for server communication."""

import logging
from typing import Any

import httpx

logger = logging.getLogger("mc-agent")


class AgentClient:
    """HTTP client for communicating with Mission Control server."""

    def __init__(
        self,
        server_url: str,
        api_key: str = "",
        verify_ssl: bool = True,
        timeout: int = 30,
    ):
        self.server_url = server_url.rstrip("/")
        self.api_key = api_key
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["X-Agent-API-Key"] = self.api_key
            self._client = httpx.AsyncClient(
                base_url=self.server_url,
                headers=headers,
                verify=self.verify_ssl,
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client

    def set_api_key(self, api_key: str) -> None:
        """Update the API key for authentication."""
        self.api_key = api_key

    async def post(
        self, path: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Send a POST request."""
        client = await self._get_client()
        response = await client.post(path, json=data or {})
        response.raise_for_status()
        return response.json()

    async def get(
        self, path: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Send a GET request."""
        client = await self._get_client()
        response = await client.get(path, params=params)
        response.raise_for_status()
        return response.json()

    async def upload_file(
        self, path: str, file_path: str, file_name: str
    ) -> dict[str, Any]:
        """Upload a file to the server."""
        client = await self._get_client()
        with open(file_path, "rb") as f:
            files = {"file": (file_name, f)}
            response = await client.post(
                path, files=files
            )
        response.raise_for_status()
        return response.json()

    async def download_file(
        self, path: str, save_path: str
    ) -> str:
        """Download a file from the server."""
        client = await self._get_client()
        response = await client.get(path)
        response.raise_for_status()
        with open(save_path, "wb") as f:
            f.write(response.content)
        return save_path

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
