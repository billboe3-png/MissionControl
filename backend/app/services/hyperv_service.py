"""
Mission Control Hyper-V Service

Business logic for Hyper-V operations.
Delegates to the Hyper-V provider for all data access.
Configuration comes from IntegrationProfile — never from config.py.
"""

import logging

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class HyperVService:
    """Thin service layer over the Hyper-V provider."""

    def _get_provider(self, db: Session | None = None, host_id: int | None = None):
        from app.providers.hyperv.provider_factory import get_hyperv_provider

        return get_hyperv_provider(db, host_id)

    async def get_summary(self, db: Session | None = None, host_id: int | None = None) -> dict:
        return await self._get_provider(db, host_id).get_summary()

    async def get_vms(self, db: Session | None = None, host_id: int | None = None) -> dict:
        return await self._get_provider(db, host_id).get_vms()

    async def get_vm_detail(self, vm_id: str, db: Session | None = None, host_id: int | None = None) -> dict:
        return await self._get_provider(db, host_id).get_vm_detail(vm_id)

    async def start_vm(self, vm_id: str, db: Session | None = None, host_id: int | None = None) -> dict:
        return await self._get_provider(db, host_id).start_vm(vm_id)

    async def stop_vm(self, vm_id: str, force: bool = False, db: Session | None = None, host_id: int | None = None) -> dict:
        return await self._get_provider(db, host_id).stop_vm(vm_id, force)

    async def restart_vm(self, vm_id: str, db: Session | None = None, host_id: int | None = None) -> dict:
        return await self._get_provider(db, host_id).restart_vm(vm_id)

    async def pause_vm(self, vm_id: str, db: Session | None = None, host_id: int | None = None) -> dict:
        return await self._get_provider(db, host_id).pause_vm(vm_id)

    async def resume_vm(self, vm_id: str, db: Session | None = None, host_id: int | None = None) -> dict:
        return await self._get_provider(db, host_id).resume_vm(vm_id)

    async def get_networks(self, db: Session | None = None, host_id: int | None = None) -> dict:
        return await self._get_provider(db, host_id).get_networks()

    async def get_storage(self, db: Session | None = None, host_id: int | None = None) -> dict:
        return await self._get_provider(db, host_id).get_storage()

    async def get_checkpoints(self, vm_id: str | None = None, db: Session | None = None, host_id: int | None = None) -> dict:
        return await self._get_provider(db, host_id).get_checkpoints(vm_id)

    async def create_checkpoint(self, vm_id: str, name: str | None = None, db: Session | None = None, host_id: int | None = None) -> dict:
        return await self._get_provider(db, host_id).create_checkpoint(vm_id, name)

    async def delete_checkpoint(self, vm_id: str, checkpoint_id: str, db: Session | None = None, host_id: int | None = None) -> dict:
        return await self._get_provider(db, host_id).delete_checkpoint(vm_id, checkpoint_id)

    async def get_health(self, db: Session | None = None, host_id: int | None = None) -> dict:
        return await self._get_provider(db, host_id).get_health()

    async def test_connection(self, db: Session | None = None, host_id: int | None = None) -> dict:
        return await self._get_provider(db, host_id).test_connection()


hyperv_service = HyperVService()
