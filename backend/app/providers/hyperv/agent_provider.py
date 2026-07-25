"""
Mission Control Agent Hyper-V Provider

Reads Hyper-V inventory from agent-collected remote target data
stored in Agent.inventory_json.  Implements HyperVProvider so the
existing Hyper-V pages work transparently for agent-relayed hosts.
"""

import json
import logging

from .base_provider import HyperVProvider

logger = logging.getLogger(__name__)


class AgentHyperVProvider(HyperVProvider):
    """Hyper-V provider backed by agent remote inventory data."""

    def __init__(self, inventory: dict, target_hostname: str = "") -> None:
        self._inventory = inventory
        self._hostname = target_hostname

    def _get_vm_list(self) -> list[dict]:
        raw = self._inventory.get("vms", [])
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                raw = []
        if isinstance(raw, dict):
            raw = [raw]
        return raw

    def _get_switch_list(self) -> list[dict]:
        raw = self._inventory.get("switches", [])
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                raw = []
        if isinstance(raw, dict):
            raw = [raw]
        return raw

    # ------------------------------------------------------------------ #
    # Connection / summary                                                #
    # ------------------------------------------------------------------ #

    async def test_connection(self) -> dict:
        return {
            "connected": True,
            "latency_ms": 0,
            "message": f"Agent-relayed connection to {self._hostname}",
            "hostname": self._hostname,
            "version": "agent",
        }

    async def get_summary(self) -> dict:
        vms = self._get_vm_list()
        running = sum(1 for v in vms if (v.get("state") or "").lower() == "running")
        stopped = sum(1 for v in vms if (v.get("state") or "").lower() == "off")
        paused = sum(1 for v in vms if (v.get("state") or "").lower() == "paused")
        saved = sum(1 for v in vms if (v.get("state") or "").lower() == "saved")
        total_mem = sum((v.get("memory_mb") or 0) for v in vms)
        return {
            "connected": True,
            "hostname": self._hostname,
            "total_vms": len(vms),
            "running": running,
            "stopped": stopped,
            "paused": paused,
            "saved": saved,
            "total_cpu": sum(v.get("cpu_usage", 0) for v in vms),
            "total_memory_gb": round(total_mem / 1024, 1),
            "used_memory_gb": 0,
            "total_storage_gb": 0,
            "used_storage_gb": 0,
        }

    # ------------------------------------------------------------------ #
    # VMs                                                                 #
    # ------------------------------------------------------------------ #

    async def get_vms(self) -> dict:
        vms = self._get_vm_list()
        items = []
        for v in vms:
            uptime_raw = v.get("uptime", 0)
            uptime_seconds = 0
            if isinstance(uptime_raw, (int, float)):
                uptime_seconds = int(uptime_raw)
            elif isinstance(uptime_raw, str):
                try:
                    uptime_seconds = int(float(uptime_raw))
                except (ValueError, TypeError):
                    uptime_seconds = 0
            elif isinstance(uptime_raw, dict):
                uptime_seconds = int(uptime_raw.get("TotalSeconds", 0))
            items.append({
                "id": v.get("vm_id", v.get("name", "")),
                "name": v.get("name", ""),
                "state": (v.get("state") or "unknown").lower(),
                "cpu_count": 0,
                "memory_assigned_mb": int(v.get("memory_mb") or 0),
                "memory_startup_mb": int(v.get("memory_startup_mb") or 0),
                "memory_demand_mb": 0,
                "uptime_seconds": uptime_seconds,
                "host_server": v.get("computer_name", self._hostname),
                "guest_os": "",
                "creation_time": "",
                "last_checkpoint": None,
                "status_message": v.get("status", ""),
                "integration_services_enabled": True,
                "cpu_usage_percent": float(v.get("cpu_usage") or 0),
                "disk_read_mbps": 0.0,
                "disk_write_mbps": 0.0,
                "network_receive_mbps": 0.0,
                "network_send_mbps": 0.0,
            })
        return {"connected": True, "count": len(items), "items": items}

    async def get_vm_detail(self, vm_id: str) -> dict:
        vms = self._get_vm_list()
        for v in vms:
            if v.get("vm_id") == vm_id or v.get("name") == vm_id:
                return {"connected": True, "item": v}
        return {"connected": False, "error": "VM not found in agent inventory"}

    # ------------------------------------------------------------------ #
    # VM actions (not supported via agent — read-only relay)              #
    # ------------------------------------------------------------------ #

    async def start_vm(self, vm_id: str) -> dict:
        return {"success": False, "error": "VM actions not supported via agent relay"}

    async def stop_vm(self, vm_id: str, force: bool = False) -> dict:
        return {"success": False, "error": "VM actions not supported via agent relay"}

    async def restart_vm(self, vm_id: str) -> dict:
        return {"success": False, "error": "VM actions not supported via agent relay"}

    async def pause_vm(self, vm_id: str) -> dict:
        return {"success": False, "error": "VM actions not supported via agent relay"}

    async def resume_vm(self, vm_id: str) -> dict:
        return {"success": False, "error": "VM actions not supported via agent relay"}

    # ------------------------------------------------------------------ #
    # Networks                                                            #
    # ------------------------------------------------------------------ #

    async def get_networks(self) -> dict:
        switches = self._get_switch_list()
        items = [
            {
                "id": s.get("name", str(i)),
                "name": s.get("name", ""),
                "switch_type": (s.get("type") or "").lower(),
                "allow_management_os": False,
                "status": "operational",
            }
            for i, s in enumerate(switches)
        ]
        return {"connected": True, "count": len(items), "items": items}

    # ------------------------------------------------------------------ #
    # Storage                                                             #
    # ------------------------------------------------------------------ #

    async def get_storage(self) -> dict:
        return {"connected": True, "count": 0, "items": []}

    # ------------------------------------------------------------------ #
    # Checkpoints / snapshots                                             #
    # ------------------------------------------------------------------ #

    async def get_snapshots(self, vm_id: str | None = None) -> dict:
        return await self.get_checkpoints(vm_id)

    async def get_checkpoints(self, vm_id: str | None = None) -> dict:
        return {"connected": True, "count": 0, "items": []}

    async def create_snapshot(self, vm_id: str, name: str | None = None) -> dict:
        return await self.create_checkpoint(vm_id, name)

    async def create_checkpoint(self, vm_id: str, name: str | None = None) -> dict:
        return {"success": False, "error": "Checkpoints not supported via agent relay"}

    async def delete_snapshot(self, vm_id: str, snapshot_id: str) -> dict:
        return await self.delete_checkpoint(vm_id, snapshot_id)

    async def delete_checkpoint(self, vm_id: str, checkpoint_id: str) -> dict:
        return {"success": False, "error": "Checkpoints not supported via agent relay"}

    # ------------------------------------------------------------------ #
    # Health                                                              #
    # ------------------------------------------------------------------ #

    async def get_health(self) -> dict:
        return {
            "connected": True,
            "status": "healthy",
            "hosts": [
                {
                    "name": self._hostname,
                    "status": "healthy",
                    "cpu_percent": 0,
                    "memory_percent": 0,
                    "memory_used_gb": 0,
                    "memory_total_gb": 0,
                    "uptime_seconds": 0,
                    "vm_count": len(self._get_vm_list()),
                    "version": "agent",
                }
            ],
            "cluster_summary": "Agent-relayed host",
        }
