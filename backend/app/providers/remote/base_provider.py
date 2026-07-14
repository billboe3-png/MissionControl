"""
Mission Control Remote Provider Base

Abstract base class defining the contract for all remote connection providers.
Each provider implements SSH or WinRM connection logic.

Sprint 2.1.6 - Real WinRM Command Execution.
"""

from abc import ABC, abstractmethod
from collections.abc import Generator


class RemoteBaseProvider(ABC):
    """
    Abstract base class for remote connection providers.

    Each concrete provider (SSH, WinRM) must implement:
    - test_connection: Verify connectivity to a remote host
    - execute_command: Run a command on a remote host

    execute_command returns a dict with:
        - stdout: str
        - stderr: str
        - exit_code: int
        - success: bool
        - duration_ms: int
        - started_at: str (ISO 8601)
        - completed_at: str (ISO 8601)
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
        """Test connectivity to a remote host."""
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
        """Execute a command on a remote host."""
        ...

    def stream_command(
        self,
        hostname: str,
        port: int,
        username: str,
        password: str | None,
        ssh_key: str | None,
        command: str,
        shell: str,
        ip_address: str | None,
    ) -> Generator[dict, None, None]:
        """
        Stream command output line by line.

        Internal generator for future WebSocket support.
        Yields dicts with {type, data} where type is
        'stdout', 'stderr', 'exit_code', or 'error'.

        Default implementation runs execute_command and yields
        the complete output. Subclasses may override for real
        streaming support.
        """
        import asyncio

        result = asyncio.get_event_loop().run_until_complete(
            self.execute_command(
                hostname=hostname,
                port=port,
                username=username,
                password=password,
                ssh_key=ssh_key,
                command=command,
                shell=shell,
                ip_address=ip_address,
            )
        )

        if result["stdout"]:
            yield {"type": "stdout", "data": result["stdout"]}
        if result["stderr"]:
            yield {"type": "stderr", "data": result["stderr"]}
        yield {"type": "exit_code", "data": result["exit_code"]}
