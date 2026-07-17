"""
Mission Control Proxmox Service

Business logic for Proxmox operations.
Delegates to the Proxmox provider for all data access.
Configuration comes from IntegrationProfile — never from config.py.
"""

import logging

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ProxmoxService:
    """Thin service layer over the Proxmox provider."""

    def _get_provider(self, db: Session | None = None):
        from app.providers.proxmox.provider_factory import get_proxmox_provider

        return get_proxmox_provider(db)

    async def get_summary(self, db: Session | None = None) -> dict:
        return await self._get_provider(db).get_summary()

    async def get_nodes(self, db: Session | None = None) -> dict:
        return await self._get_provider(db).get_nodes()

    async def get_vms(self, db: Session | None = None) -> dict:
        return await self._get_provider(db).get_vms()

    async def get_vm_detail(self, vm_id: str, db: Session | None = None) -> dict:
        return await self._get_provider(db).get_vm_detail(vm_id)

    async def start_vm(self, vm_id: str, db: Session | None = None) -> dict:
        return await self._get_provider(db).start_vm(vm_id)

    async def stop_vm(self, vm_id: str, force: bool = False, db: Session | None = None) -> dict:
        return await self._get_provider(db).stop_vm(vm_id, force)

    async def restart_vm(self, vm_id: str, db: Session | None = None) -> dict:
        return await self._get_provider(db).restart_vm(vm_id)

    async def pause_vm(self, vm_id: str, db: Session | None = None) -> dict:
        return await self._get_provider(db).pause_vm(vm_id)

    async def resume_vm(self, vm_id: str, db: Session | None = None) -> dict:
        return await self._get_provider(db).resume_vm(vm_id)

    async def get_networks(self, db: Session | None = None) -> dict:
        return await self._get_provider(db).get_networks()

    async def get_storage(self, db: Session | None = None) -> dict:
        return await self._get_provider(db).get_storage()

    async def get_snapshots(self, vm_id: str | None = None, db: Session | None = None) -> dict:
        return await self._get_provider(db).get_snapshots(vm_id)

    async def create_snapshot(self, vm_id: str, name: str | None = None, db: Session | None = None) -> dict:
        return await self._get_provider(db).create_snapshot(vm_id, name)

    async def delete_snapshot(self, vm_id: str, snapshot_id: str, db: Session | None = None) -> dict:
        return await self._get_provider(db).delete_snapshot(vm_id, snapshot_id)

    async def get_health(self, db: Session | None = None) -> dict:
        return await self._get_provider(db).get_health()

    async def test_connection(self, db: Session | None = None) -> dict:
        return await self._get_provider(db).test_connection()

    async def get_tasks(self, node: str | None = None, db: Session | None = None) -> dict:
        return await self._get_provider(db).get_tasks(node)

    async def get_lxc_containers(self, db: Session | None = None) -> dict:
        return await self._get_provider(db).get_lxc_containers()

    async def get_lxc_detail(self, vm_id: str, db: Session | None = None) -> dict:
        return await self._get_provider(db).get_lxc_detail(vm_id)

    async def start_lxc(self, vm_id: str, db: Session | None = None) -> dict:
        return await self._get_provider(db).start_lxc(vm_id)

    async def stop_lxc(self, vm_id: str, db: Session | None = None) -> dict:
        return await self._get_provider(db).stop_lxc(vm_id)

    async def get_lxc_templates(self, node: str | None = None, db: Session | None = None) -> dict:
        return await self._get_provider(db).get_lxc_templates(node)

    async def create_lxc(self, config: dict, db: Session | None = None) -> dict:
        return await self._get_provider(db).create_lxc(config)

    async def delete_lxc(self, vm_id: str, purge: bool = False, db: Session | None = None) -> dict:
        return await self._get_provider(db).delete_lxc(vm_id, purge)

    async def clone_lxc(self, vm_id: str, new_vmid: str | None = None, hostname: str | None = None, db: Session | None = None) -> dict:
        return await self._get_provider(db).clone_lxc(vm_id, new_vmid, hostname)


proxmox_service = ProxmoxService()
