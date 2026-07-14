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

    def _get_provider(self, db: Session | None = None):
        from app.providers.hyperv.provider_factory import get_hyperv_provider

        return get_hyperv_provider(db)

    async def get_summary(self, db: Session | None = None) -> dict:
        return await self._get_provider(db).get_summary()

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

    async def get_checkpoints(self, vm_id: str | None = None, db: Session | None = None) -> dict:
        return await self._get_provider(db).get_checkpoints(vm_id)

    async def create_checkpoint(self, vm_id: str, name: str | None = None, db: Session | None = None) -> dict:
        return await self._get_provider(db).create_checkpoint(vm_id, name)

    async def delete_checkpoint(self, vm_id: str, checkpoint_id: str, db: Session | None = None) -> dict:
        return await self._get_provider(db).delete_checkpoint(vm_id, checkpoint_id)

    async def get_health(self, db: Session | None = None) -> dict:
        return await self._get_provider(db).get_health()

    async def test_connection(self, db: Session | None = None) -> dict:
        return await self._get_provider(db).test_connection()


hyperv_service = HyperVService()
