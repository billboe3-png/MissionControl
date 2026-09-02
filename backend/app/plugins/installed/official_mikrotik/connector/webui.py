"""RouterOS REST API connector ("Web UI" method).

MikroTik RouterOS v7 exposes a REST API over HTTP(S) with HTTP Basic
authentication. This is the preferred access method for v7 devices because it
returns structured JSON instead of screen-scraped CLI output.

Commands may be given either as RouterOS CLI syntax (``/system identity
print``) — which is translated to the equivalent REST resource for common
read-only commands — or directly as a REST path (``system/resource``).
"""

from __future__ import annotations

import contextlib
import json
from urllib.parse import urljoin

import requests
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError, Timeout

from .base import BaseConnector, ConnectorConfig
from .exceptions import (
    ConnectorAuthenticationError,
    ConnectorCommandError,
    ConnectorConnectionError,
)

# Explicit translations for common read commands. Anything not listed here
# falls through to the generic rule (see RestConnector.command_to_rest_path).
_CLI_TO_REST_OVERRIDES: dict[str, str] = {
    "/system identity print": "system/identity",
    "/system resource print": "system/resource",
    "/system resource cpu print": "system/resource/cpu",
    "/system health print": "system/health",
    "/system routerboard print": "system/routerboard",
    "/system package update print": "system/package/update",
    "/system license print": "system/license",
    "/interface print": "interface",
    "/interface ethernet print": "interface/ethernet",
    "/interface bonding print": "interface/bonding",
    "/interface vlan print": "interface/vlan",
    "/interface bridge print": "interface/bridge",
    "/ip address print": "ip/address",
    "/ip route print": "ip/route",
    "/ip neighbor print": "ip/neighbor",
    "/ip dns print": "ip/dns",
    "/user print": "user",
    "/queue simple print": "queue/simple",
}


class WebUiConnector(BaseConnector):
    """RouterOS v7 REST API connector (HTTP Basic auth, JSON responses)."""

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self._use_https = bool(config.extra.get("use_https", True))
        scheme = "https" if self._use_https else "http"
        self._base_url = f"{scheme}://{config.host}"
        if config.port:
            self._base_url = f"{self._base_url}:{config.port}"
        self._base_url = f"{self._base_url}/rest/"
        self._session = requests.Session()

    # ------------------------------------------------------------------ #
    # Connection lifecycle                                                #
    # ------------------------------------------------------------------ #

    def connect(self) -> None:
        if self.is_connected:
            return

        self._session.verify = bool(self.config.extra.get("verify_ssl", False))

        probe_path = str(self.config.extra.get("probe_path", "system/resource"))
        url = urljoin(self._base_url, probe_path)
        try:
            response = self._session.get(
                url,
                auth=(self.config.username, self.config.password),
                timeout=self.config.timeout,
            )
            response.raise_for_status()
        except HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else 0
            if status_code in (401, 403):
                raise ConnectorAuthenticationError(
                    f"REST authentication failed for {self.config.username}@{self.config.host}"
                ) from exc
            raise ConnectorConnectionError(
                f"REST endpoint {url} returned HTTP {status_code}"
            ) from exc
        except Timeout as exc:
            raise ConnectorConnectionError(
                f"REST connection to {self._base_url} timed out"
            ) from exc
        except RequestsConnectionError as exc:
            raise ConnectorConnectionError(
                f"Cannot reach REST API at {self._base_url}: {exc}"
            ) from exc

        # Mark the connector as connected (BaseConnector.is_connected checks
        # this attribute; the session itself is the live connection object).
        self._connection = self._session

    def disconnect(self) -> None:
        if self._session is not None:
            with contextlib.suppress(Exception):
                self._session.close()
            self._session = requests.Session()
            self._connection = None

    # ------------------------------------------------------------------ #
    # Command execution                                                   #
    # ------------------------------------------------------------------ #

    @staticmethod
    def command_to_rest_path(command: str) -> str:
        """Translate RouterOS CLI read syntax into a REST resource path.

        ``/interface print`` -> ``interface``
        ``/system identity print`` -> ``system/identity``
        ``system/resource`` -> ``system/resource`` (passthrough)
        """
        cmd = command.strip()
        if not cmd.startswith("/"):
            return cmd.strip("/")

        lowered = cmd.lower().strip()
        if lowered in _CLI_TO_REST_OVERRIDES:
            return _CLI_TO_REST_OVERRIDES[lowered]

        tokens = [t for t in cmd.lstrip("/").split() if t]
        if tokens and tokens[-1].lower() == "print":
            tokens = tokens[:-1]
        return "/".join(tokens)

    @property
    def base_url(self) -> str:
        return self._base_url

    def execute(self, command: str) -> str:
        if not self.is_connected:
            raise ConnectorConnectionError("REST connector is not connected")

        rest_path = self.command_to_rest_path(command)
        if not rest_path:
            raise ConnectorCommandError(f"Cannot translate command '{command}' to a REST path")

        url = urljoin(self._base_url, rest_path)
        try:
            response = self._session.get(
                url,
                auth=(self.config.username, self.config.password),
                timeout=self.config.timeout,
            )
            response.raise_for_status()

            if response.status_code == 204 or not response.content:
                return ""

            content_type = response.headers.get("Content-Type", "")
            if "application/json" in content_type:
                return json.dumps(response.json(), indent=2)
            return response.text.strip()
        except HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else 0
            if status_code in (401, 403):
                raise ConnectorAuthenticationError(
                    f"REST authentication failed for {self.config.username}@{self.config.host}"
                ) from exc
            raise ConnectorCommandError(
                f"REST request '{command}' failed on {self.config.host}: "
                f"HTTP {status_code} for {rest_path!r}"
            ) from exc
        except Timeout as exc:
            raise ConnectorCommandError(
                f"REST request '{command}' timed out on {self.config.host}"
            ) from exc
        except Exception as exc:
            raise ConnectorCommandError(
                f"REST request '{command}' failed on {self.config.host}: {exc}"
            ) from exc


# Descriptive alias; both names refer to the same implementation.
RestConnector = WebUiConnector
