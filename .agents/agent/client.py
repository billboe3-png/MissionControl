"""Mission Control Agent - HTTP client for server communication."""

import asyncio
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
        max_retries: int = 3,
    ):
        self.server_url = server_url.rstrip("/")
        self.api_key = api_key
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.max_retries = max_retries
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

    async def _request_with_retry(
        self, method: str, path: str, **kwargs: Any
    ) -> dict[str, Any]:
        """Execute an HTTP request with retry and backoff."""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                client = await self._get_client()
                response = await getattr(client, method)(path, **kwargs)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code < 500:
                    raise
                last_error = e
                delay = min(2 ** attempt, 30)
                logger.warning(
                    "Server error %d on %s %s (attempt %d/%d), "
                    "retrying in %ds",
                    e.response.status_code, method, path,
                    attempt + 1, self.max_retries, delay,
                )
                await asyncio.sleep(delay)
            except (httpx.ConnectError, httpx.ConnectTimeout) as e:
                last_error = e
                delay = min(2 ** attempt, 30)
                logger.warning(
                    "Connection failed on %s %s (attempt %d/%d), "
                    "retrying in %ds",
                    method, path,
                    attempt + 1, self.max_retries, delay,
                )
                self._client = None
                await asyncio.sleep(delay)
        raise last_error

    async def post(
        self, path: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Send a POST request."""
        return await self._request_with_retry(
            "post", path, json=data or {}
        )

    async def get(
        self, path: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Send a GET request."""
        return await self._request_with_retry(
            "get", path, params=params
        )

    async def upload_file(
        self, path: str, file_path: str, file_name: str
    ) -> dict[str, Any]:
        """Upload a file to the server."""
        client = await self._get_client()
        with open(file_path, "rb") as f:
            files = {"file": (file_name, f)}
            response = await client.post(path, files=files)
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
