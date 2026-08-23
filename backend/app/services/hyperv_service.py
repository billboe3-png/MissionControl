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
        provider = self._get_provider(db, host_id)
        data = await provider.get_summary()
        if data.get("connected") is False:
            agent_data = self._try_agent_summary(db)
            if agent_data:
                return agent_data
        return data

    async def get_vms(self, db: Session | None = None, host_id: int | None = None) -> dict:
        data = await self._get_provider(db, host_id).get_vms()
        items = data.get("items") if isinstance(data, dict) else None
        if items is not None and len(items) == 0:
            agent_data = self._try_agent_vms(db)
            if agent_data:
                return agent_data
        return data

    def _try_agent_vms(self, db: Session | None) -> dict | None:
        """Fallback VM list built from latest agent-pushed Hyper-V inventory."""
        if db is None:
            return None
        try:
            import asyncio

            from app.models.db.agent import Agent
            from app.providers.hyperv.agent_provider import AgentHyperVProvider

            agent = (
                db.query(Agent)
                .filter(Agent.status != "offline", Agent.inventory_json.isnot(None))
                .order_by(Agent.id.asc())
                .first()
            )
            if agent is None:
                return None

            full_inv = {}
            try:
                import json
                full_inv = json.loads(agent.inventory_json) if agent.inventory_json else {}
            except (TypeError, ValueError):
                return None

            hyperv = full_inv.get("plugins", {}).get("hyperv")
            if not hyperv or hyperv.get("vm_count", 0) <= 0:
                return None

            provider = AgentHyperVProvider(
                hyperv,
                target_hostname=agent.name or full_inv.get("system", {}).get("hostname", "Agent"),
                agent_id=agent.id,
                target_id=agent.id,
                dispatch_cmd=lambda command_str: {"success": False, "error": "Agent offline for commands"},
            )
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            return loop.run_until_complete(provider.get_vms())
        except Exception as exc:
            logger.debug("Agent-backed Hyper-V VM fallback failed: %s", exc)
            return None

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

    async def get_replication(self, db: Session | None = None, host_id: int | None = None) -> dict:
        return await self._get_provider(db, host_id).get_replication()

    def _try_agent_summary(self, db: Session | None) -> dict | None:
        """Fallback summary built from latest agent-pushed Hyper-V inventory."""
        if db is None:
            return None
        try:
            import asyncio

            from app.models.db.agent import Agent
            from app.providers.hyperv.agent_provider import AgentHyperVProvider

            agent = (
                db.query(Agent)
                .filter(Agent.status != "offline", Agent.inventory_json.isnot(None))
                .order_by(Agent.id.asc())
                .first()
            )
            if agent is None:
                return None

            full_inv = {}
            try:
                import json
                full_inv = json.loads(agent.inventory_json) if agent.inventory_json else {}
            except (TypeError, ValueError):
                return None

            hyperv = full_inv.get("plugins", {}).get("hyperv")
            if not hyperv or hyperv.get("vm_count", 0) <= 0:
                return None

            provider = AgentHyperVProvider(
                hyperv,
                target_hostname=agent.name or full_inv.get("system", {}).get("hostname", "Agent"),
                agent_id=agent.id,
                target_id=agent.id,
                dispatch_cmd=lambda command_str: {"success": False, "error": "Agent offline for commands"},
            )
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            return loop.run_until_complete(provider.get_summary())
        except Exception as exc:
            logger.debug("Agent-backed Hyper-V summary fallback failed: %s", exc)
            return None


hyperv_service = HyperVService()
