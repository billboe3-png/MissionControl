"""
Mission Control Hyper-V Provider — Abstract Base

Extends VirtualizationProvider with Hyper-V specific methods.
"""

from abc import abstractmethod

from app.providers.virtualization.base_provider import VirtualizationProvider


class HyperVProvider(VirtualizationProvider):
    """Abstract Hyper-V provider interface."""

    async def get_replication(self) -> dict:
        """VM replication status.

        Concrete providers override this with real data; the default
        keeps the /hyperv/replication endpoint schema-valid for any
        provider that does not support it (instead of a 500).
        """
        return {
            "connected": False,
            "replicating": 0,
            "total": 0,
            "items": [],
            "error": "Replication status is not available for this host",
        }

    @abstractmethod
    async def get_checkpoints(self, vm_id: str | None = None) -> dict:
        """List checkpoints (Hyper-V specific alias for get_snapshots)."""

    @abstractmethod
    async def create_checkpoint(self, vm_id: str, name: str | None = None) -> dict:
        """Create a checkpoint (Hyper-V specific alias for create_snapshot)."""

    @abstractmethod
    async def delete_checkpoint(self, vm_id: str, checkpoint_id: str) -> dict:
        """Delete a checkpoint (Hyper-V specific alias for delete_snapshot)."""
