"""
Mission Control Remote Provider Base

Abstract base class defining the contract for all remote connection providers.
Each provider implements SSH or WinRM connection logic.

Sprint 2.1.0 - Remote Operations Framework.
"""

from abc import ABC
from abc import abstractmethod


class RemoteBaseProvider(ABC):
    """
    Abstract base class for remote connection providers.

    Each concrete provider (SSH, WinRM) must implement:
    - test_connection: Verify connectivity to a remote host
    - execute_command: Run a command on a remote host
    """

    @abstractmethod
    async def test_connection(
        self,
        hostname: str,
        port: int,
        username: str,
        password: str | None,
        ssh_key: str | None,
        ip_address: str | None,
    ) -> dict:
        """
        Test connectivity to a remote host.

        Returns a dict with:
            - success: bool
            - latency_ms: int
            - message: str
        """
        ...

    @abstractmethod
    async def execute_command(
        self,
        hostname: str,
        port: int,
        username: str,
        password: str | None,
        ssh_key: str | None,
        command: str,
        shell: str,
        ip_address: str | None,
    ) -> dict:
        """
        Execute a command on a remote host.

        Returns a dict with:
            - stdout: str
            - stderr: str
            - exit_code: int
            - duration_ms: int
        """
        ...
