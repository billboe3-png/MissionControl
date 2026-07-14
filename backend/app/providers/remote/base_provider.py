"""
Mission Control Remote Provider Base

Abstract base class defining the contract for all remote connection providers.
Each provider implements SSH or WinRM connection logic.

Sprint 2.1.8 - Remote Operations Finalization.
"""

from abc import ABC, abstractmethod
from collections.abc import Generator


class RemoteBaseProvider(ABC):
    """
    Abstract base class for remote connection providers.

    Each concrete provider (SSH, WinRM) must implement:
    - test_connection: Verify connectivity to a remote host
    - execute_command: Run a command on a remote host
    - upload_file: Upload a file to the remote host
    - download_file: Download a file from the remote host
    - list_directory: List contents of a remote directory
    - create_directory: Create a directory on the remote host
    - delete_file: Delete a file on the remote host
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

    @abstractmethod
    async def upload_file(
        self,
        hostname: str,
        port: int,
        username: str,
        password: str | None,
        ssh_key: str | None,
        remote_path: str,
        content: bytes,
        ip_address: str | None,
    ) -> dict:
        """Upload a file to the remote host."""
        ...

    @abstractmethod
    async def download_file(
        self,
        hostname: str,
        port: int,
        username: str,
        password: str | None,
        ssh_key: str | None,
        remote_path: str,
        ip_address: str | None,
    ) -> dict:
        """Download a file from the remote host."""
        ...

    @abstractmethod
    async def list_directory(
        self,
        hostname: str,
        port: int,
        username: str,
        password: str | None,
        ssh_key: str | None,
        remote_path: str,
        ip_address: str | None,
    ) -> dict:
        """List contents of a remote directory."""
        ...

    @abstractmethod
    async def create_directory(
        self,
        hostname: str,
        port: int,
        username: str,
        password: str | None,
        ssh_key: str | None,
        remote_path: str,
        ip_address: str | None,
    ) -> dict:
        """Create a directory on the remote host."""
        ...

    @abstractmethod
    async def delete_file(
        self,
        hostname: str,
        port: int,
        username: str,
        password: str | None,
        ssh_key: str | None,
        remote_path: str,
        ip_address: str | None,
    ) -> dict:
        """Delete a file on the remote host."""
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
