"""
Mission Control Proxmox Provider — Abstract Base

Extends VirtualizationProvider with Proxmox-specific methods.
"""

from abc import abstractmethod

from app.providers.virtualization.base_provider import VirtualizationProvider


class ProxmoxProvider(VirtualizationProvider):
    """Abstract Proxmox provider interface."""

    @abstractmethod
    async def get_nodes(self) -> dict:
        """List cluster nodes."""

    @abstractmethod
    async def get_lxc_containers(self) -> dict:
        """List LXC containers."""

    @abstractmethod
    async def get_lxc_detail(self, vm_id: str) -> dict:
        """Get detailed info for a single LXC container."""

    @abstractmethod
    async def start_lxc(self, vm_id: str) -> dict:
        """Start an LXC container."""

    @abstractmethod
    async def stop_lxc(self, vm_id: str) -> dict:
        """Stop an LXC container."""

    @abstractmethod
    async def get_tasks(self, node: str | None = None) -> dict:
        """List recent tasks across the cluster."""

    @abstractmethod
    async def get_lxc_templates(self, node: str | None = None) -> dict:
        """List available LXC templates (vztmpl) on storage."""

    @abstractmethod
    async def create_lxc(self, config: dict) -> dict:
        """Create a new LXC container from a template.

        Args:
            config: Dict with keys: node, vmid, ostemplate, hostname, cores,
                    memory, disk, storage, password, net, unprivileged, features, etc.
        """

    @abstractmethod
    async def delete_lxc(self, vm_id: str, purge: bool = False) -> dict:
        """Delete an LXC container."""

    @abstractmethod
    async def clone_lxc(self, vm_id: str, new_vmid: str | None = None, hostname: str | None = None) -> dict:
        """Clone an existing LXC container."""
