"""
Mission Control Virtualization Provider — Abstract Base

Defines the common contract for all virtualization platforms.
Hyper-V, Proxmox, VMware, and KVM all implement this interface.
Every method returns a dict and never raises exceptions.
"""

from abc import ABC, abstractmethod


class VirtualizationProvider(ABC):
    """Abstract virtualization provider interface."""

    @abstractmethod
    async def test_connection(self) -> dict:
        """Test connectivity to the virtualization host."""

    @abstractmethod
    async def get_summary(self) -> dict:
        """Return aggregate virtualization statistics."""

    @abstractmethod
    async def get_vms(self) -> dict:
        """List all virtual machines."""

    @abstractmethod
    async def get_vm_detail(self, vm_id: str) -> dict:
        """Get detailed info for a single VM."""

    @abstractmethod
    async def start_vm(self, vm_id: str) -> dict:
        """Start a virtual machine."""

    @abstractmethod
    async def stop_vm(self, vm_id: str, force: bool = False) -> dict:
        """Stop a virtual machine."""

    @abstractmethod
    async def restart_vm(self, vm_id: str) -> dict:
        """Restart a virtual machine."""

    @abstractmethod
    async def pause_vm(self, vm_id: str) -> dict:
        """Pause a virtual machine (where supported)."""

    @abstractmethod
    async def resume_vm(self, vm_id: str) -> dict:
        """Resume a paused virtual machine (where supported)."""

    @abstractmethod
    async def get_networks(self) -> dict:
        """List virtual networks/switches."""

    @abstractmethod
    async def get_storage(self) -> dict:
        """List virtual storage/disks."""

    @abstractmethod
    async def get_snapshots(self, vm_id: str | None = None) -> dict:
        """List snapshots/checkpoints, optionally filtered by VM."""

    @abstractmethod
    async def create_snapshot(self, vm_id: str, name: str | None = None) -> dict:
        """Create a snapshot/checkpoint."""

    @abstractmethod
    async def delete_snapshot(self, vm_id: str, snapshot_id: str) -> dict:
        """Delete a snapshot/checkpoint."""

    @abstractmethod
    async def get_health(self) -> dict:
        """Get host/cluster health status."""
