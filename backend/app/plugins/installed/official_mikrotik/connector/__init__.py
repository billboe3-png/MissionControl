"""Switch connector package.

Provides SSH, Telnet, and RouterOS REST ("Web UI") access to MikroTik
switches behind a common interface.
"""

from .base import BaseConnector, ConnectorConfig
from .exceptions import (
    CommandError,
    ConnectionError,
    ConnectorAuthenticationError,
    ConnectorCommandError,
    ConnectorConnectionError,
    SwitchConnectorError,
)
from .ssh import SshConnector
from .telnet import TelnetConnector
from .webui import RestConnector, WebUiConnector

__all__ = [
    "BaseConnector",
    "CommandError",
    "ConnectionError",
    "ConnectorAuthenticationError",
    "ConnectorCommandError",
    "ConnectorConfig",
    "ConnectorConnectionError",
    "RestConnector",
    "SshConnector",
    "SwitchConnectorError",
    "TelnetConnector",
    "WebUiConnector",
]
