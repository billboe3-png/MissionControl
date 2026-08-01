"""
Mission Control Agent Hyper-V Provider (read-only local host path)

Reads Hyper-V inventory directly from the local agent's collected
plugin inventory stored in Agent.inventory_json, with no WinRM/SSH hop.
Write operations are not supported for the local host through this path.
"""

import json
import logging
import platform

from .base_provider import HyperVProvider

logger = logging.getLogger(__name__)


class LocalAgentHyperVProvider(HyperVProvider):
    """Hyper-V provider for the agent's own local host.

    Uses inventory collected by the local Hyper-V plugin so the UI can
    display VMs/switches without a self-referencing WinRM connection.
    Write operations are intentionally disabled for this local path.
    """

    def __init__(self, inventory: dict, hostname: str = "") -> None:
        self._inventory = inventory
        self._hostname = hostname

    # ------------------------------------------------------------------ #
    # Read-only data accessors                                             #
    # ------------------------------------------------------------------ #

    async def test_connection(self) -> dict:
        return {
            "connected": True,
            "latency_ms": 0,
            "message": f"Local agent Hyper-V on {self._hostname or 'this host'}",
            "hostname": self._hostname or platform.node(),
            "version": "local-agent",
        }

    async def get_summary(self) -> dict:
        vms = self._get_vm_list()
        states = [_STATE_MAP.get(v.get("state"), str(v.get("state", "")).lower()) for v in vms]
        running = sum(1 for s in states if s == "running")
        stopped = sum(1 for s in states if s == "stopped")
        paused = sum(1 for s in states if s == "paused")
        saved = sum(1 for s in states if s == "saved")
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
                "state": _STATE_MAP.get(v.get("state", -1), str(v.get("state", "unknown")).lower()),
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
        for v in self._get_vm_list():
            if v.get("vm_id") == vm_id or v.get("name") == vm_id:
                return {"connected": True, "item": v}
        return {"connected": False, "error": "VM not found in agent inventory"}

    async def get_networks(self) -> dict:
        switches = self._get_switch_list()
        items = [
            {
                "id": s.get("name", str(i)),
                "name": s.get("name", ""),
                "switch_type": _SWITCH_TYPE_MAP.get(s.get("type", -1), str(s.get("type", "")).lower()),
                "allow_management_os": False,
                "status": "operational",
            }
            for i, s in enumerate(switches)
        ]
        return {"connected": True, "count": len(items), "items": items}

    async def get_storage(self) -> dict:
        return {"connected": True, "count": 0, "items": []}

    async def get_checkpoints(self, vm_id: str | None = None) -> dict:
        return {"connected": True, "count": 0, "items": []}

    async def get_health(self) -> dict:
        vms = self._get_vm_list()
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
                    "vm_count": len(vms),
                    "version": "local-agent",
                }
            ],
            "cluster_summary": "Agent-local host",
        }

    # ------------------------------------------------------------------ #
    # Write operations not supported for local read-only path             #
    # ------------------------------------------------------------------ #

    async def start_vm(self, vm_id: str) -> dict:
        return {"success": False, "error": "Local host operations are read-only; use an IntegrationProfile for remote management."}

    async def stop_vm(self, vm_id: str, force: bool = False) -> dict:
        return {"success": False, "error": "Local host operations are read-only; use an IntegrationProfile for remote management."}

    async def restart_vm(self, vm_id: str) -> dict:
        return {"success": False, "error": "Local host operations are read-only; use an IntegrationProfile for remote management."}

    async def pause_vm(self, vm_id: str) -> dict:
        return {"success": False, "error": "Local host operations are read-only; use an IntegrationProfile for remote management."}

    async def resume_vm(self, vm_id: str) -> dict:
        return {"success": False, "error": "Local host operations are read-only; use an IntegrationProfile for remote management."}

    async def create_checkpoint(self, vm_id: str, name: str | None = None) -> dict:
        return {"success": False, "error": "Local host operations are read-only; use an IntegrationProfile for remote management."}

    async def delete_checkpoint(self, vm_id: str, checkpoint_id: str) -> dict:
        return {"success": False, "error": "Local host operations are read-only; use an IntegrationProfile for remote management."}

    async def create_snapshot(self, vm_id: str, name: str | None = None) -> dict:
        return {"success": False, "error": "Local host operations are read-only; use an IntegrationProfile for remote management."}

    async def delete_snapshot(self, vm_id: str, snapshot_id: str) -> dict:
        return {"success": False, "error": "Local host operations are read-only; use an IntegrationProfile for remote management."}

    async def get_snapshots(self, vm_id: str | None = None) -> dict:
        return {"connected": True, "count": 0, "items": []}

    # ------------------------------------------------------------------ #
    # Helpers                                                             #
    # ------------------------------------------------------------------ #

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


_STATE_MAP = {
    0: "other",
    1: "running",
    2: "running",
    3: "stopped",
    4: "saved",
    5: "paused",
    6: "running",
    7: "stopped",
    8: "saved",
    9: "paused",
    10: "running",
}

_SWITCH_TYPE_MAP = {
    0: "external",
    1: "internal",
    2: "private",
}
