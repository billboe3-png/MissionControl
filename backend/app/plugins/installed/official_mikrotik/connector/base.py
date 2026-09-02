"""Base classes for switch connectors."""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConnectorConfig:
    """Connection parameters for a single switch connector."""

    host: str
    username: str
    password: str = ""
    port: int | None = None
    timeout: int = 30
    extra: dict[str, Any] = field(default_factory=dict)


class BaseConnector(abc.ABC):
    """Common interface implemented by every switch connector."""

    def __init__(self, config: ConnectorConfig) -> None:
        self.config = config
        self._connection: Any = None

    @property
    def is_connected(self) -> bool:
        return self._connection is not None

    @property
    def connector_type(self) -> str:
        return self.__class__.__name__

    @abc.abstractmethod
    def connect(self) -> None:
        """Establish the connection. Idempotent."""

    @abc.abstractmethod
    def disconnect(self) -> None:
        """Close the connection. Safe to call when already closed."""

    @abc.abstractmethod
    def execute(self, command: str) -> str:
        """Run a read command and return its textual output."""
