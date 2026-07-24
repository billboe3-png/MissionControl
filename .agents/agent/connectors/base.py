"""Mission Control Agent - Abstract remote connector."""

from abc import ABC, abstractmethod
from typing import Any


class RemoteConnector(ABC):
    """Base class for remote target connectors."""

    def __init__(self, target: dict[str, Any]):
        self.target = target
        self.hostname = target["hostname"]
        self.port = target.get("port", 22)
        self.username = target.get("username", "")
        self.password = target.get("password")
        self.ssh_key = target.get("ssh_key")

    @abstractmethod
    async def test_connection(self) -> dict:
        """Test connectivity to the target."""

    @abstractmethod
    async def execute(self, command: str, timeout: int = 60) -> dict:
        """Execute a command on the target. Returns stdout/stderr/exit_code."""

    @abstractmethod
    async def collect_system_inventory(self) -> dict:
        """Collect system info: OS, CPU, memory, disks, network."""

    @abstractmethod
    async def collect_hyperv_inventory(self) -> dict | None:
        """Collect Hyper-V VM data if available. Returns None if not Hyper-V."""

    @abstractmethod
    async def collect_services(self) -> list[dict]:
        """Collect running services."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Close any open connections."""
