"""
Mission Control Remote Provider Factory

Singleton factory that returns the correct provider
based on connection type.

Sprint 2.1.0 - Remote Operations Framework.
"""

import logging

from app.providers.remote.base_provider import RemoteBaseProvider
from app.providers.remote.ssh_provider import SSHProvider
from app.providers.remote.winrm_provider import WinRMProvider

logger = logging.getLogger(__name__)

_ssh_provider: SSHProvider | None = None
_winrm_provider: WinRMProvider | None = None


def get_remote_provider(connection_type: str) -> RemoteBaseProvider:
    """
    Return the correct provider based on connection type.

    Supported types:
    - 'ssh' -> SSHProvider
    - 'winrm' -> WinRMProvider

    Raises ValueError for unsupported types.
    """
    global _ssh_provider
    global _winrm_provider

    if connection_type == "ssh":
        if _ssh_provider is None:
            _ssh_provider = SSHProvider()
            logger.info("Created singleton SSHProvider")
        return _ssh_provider

    if connection_type == "winrm":
        if _winrm_provider is None:
            _winrm_provider = WinRMProvider()
            logger.info("Created singleton WinRMProvider")
        return _winrm_provider

    raise ValueError(
        f"Unsupported connection type: {connection_type}. "
        f"Supported types: ssh, winrm"
    )
