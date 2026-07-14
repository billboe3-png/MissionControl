"""
Mission Control Hyper-V Provider — Abstract Base

Extends VirtualizationProvider with Hyper-V specific methods.
"""

from abc import abstractmethod

from app.providers.virtualization.base_provider import VirtualizationProvider


class HyperVProvider(VirtualizationProvider):
    """Abstract Hyper-V provider interface."""

    @abstractmethod
    async def get_checkpoints(self, vm_id: str | None = None) -> dict:
        """List checkpoints (Hyper-V specific alias for get_snapshots)."""

    @abstractmethod
    async def create_checkpoint(self, vm_id: str, name: str | None = None) -> dict:
        """Create a checkpoint (Hyper-V specific alias for create_snapshot)."""

    @abstractmethod
    async def delete_checkpoint(self, vm_id: str, checkpoint_id: str) -> dict:
        """Delete a checkpoint (Hyper-V specific alias for delete_snapshot)."""
