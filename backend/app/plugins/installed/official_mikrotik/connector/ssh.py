"""SSH connector for MikroTik RouterOS devices (netmiko based)."""

from __future__ import annotations

import contextlib
from typing import Any

from netmiko import ConnectHandler
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetmikoTimeoutException,
)

from .base import BaseConnector
from .exceptions import (
    ConnectorAuthenticationError,
    ConnectorCommandError,
    ConnectorConnectionError,
)


class SshConnector(BaseConnector):
    """RouterOS CLI access over SSH."""

    def connect(self) -> None:
        if self.is_connected:
            return

        device_params: dict[str, Any] = {
            "device_type": "mikrotik_routeros",
            "host": self.config.host,
            "username": self.config.username,
            "password": self.config.password,
            "conn_timeout": self.config.timeout,
            "banner_timeout": self.config.timeout,
            "global_delay_factor": 2,
        }
        device_params["port"] = self.config.port or 22

        try:
            self._connection = ConnectHandler(**device_params)
        except NetmikoAuthenticationException as exc:
            raise ConnectorAuthenticationError(
                f"SSH authentication failed for {self.config.username}@{self.config.host}"
            ) from exc
        except NetmikoTimeoutException as exc:
            raise ConnectorConnectionError(
                f"SSH connection to {self.config.host}:{device_params['port']} timed out"
            ) from exc
        except Exception as exc:
            raise ConnectorConnectionError(
                f"SSH connection to {self.config.host} failed: {exc}"
            ) from exc

    def disconnect(self) -> None:
        if self._connection:
            with contextlib.suppress(Exception):
                self._connection.disconnect()
            self._connection = None

    def execute(self, command: str) -> str:
        if not self.is_connected:
            raise ConnectorConnectionError("SSH connector is not connected")

        try:
            output = self._connection.send_command(
                command,
                strip_command=False,
                strip_prompt=False,
            )
            return output.strip()
        except Exception as exc:
            raise ConnectorCommandError(
                f"SSH command '{command}' failed on {self.config.host}: {exc}"
            ) from exc
