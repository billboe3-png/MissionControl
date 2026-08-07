"""
Mission Control Agent Hyper-V Provider

Reads Hyper-V inventory from agent-collected remote target data
stored in Agent.inventory_json.  Implements HyperVProvider so the
existing Hyper-V pages work transparently for agent-relayed hosts.
Write operations (start/stop/restart/pause/resume VM, checkpoints)
dispatch commands to the agent via the server's command queue.
"""

from __future__ import annotations

import json
import logging
import re

from .base_provider import HyperVProvider

logger = logging.getLogger(__name__)

_GUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")

_HYPERV_STATE_MAP = {
    0: "other",
    1: "running",   # OtherRunning
    2: "running",   # Running
    3: "stopped",   # Off
    4: "saved",     # Saved
    5: "paused",    # Paused
    6: "running",   # RunningSaved
    7: "stopped",   # Stopping
    8: "saved",     # Saving
    9: "paused",    # Pausing
    10: "running",  # Resuming
}

_SWITCH_TYPE_MAP = {
    0: "external",
    1: "internal",
    2: "private",
}


def _vm_command(vm_id: str, cmdlet: str) -> str:
    """Build a PowerShell command that works with VM names or GUIDs."""
    if _GUID_RE.match(vm_id):
        return f"Get-VM -Id '{vm_id}' | {cmdlet}"
    return f"{cmdlet} -Name '{vm_id}'"


def _checkpoint_identity(checkpoint_id: str) -> str:
    """Return the appropriate PowerShell parameter for a checkpoint identifier."""
    if _GUID_RE.match(checkpoint_id):
        return f"-Id '{checkpoint_id}'"
    return f"-Name '{checkpoint_id}'"


_HV_CMD_START = "Start-VM {vm_id}"
_HV_CMD_STOP = "Stop-VM {vm_id}{force}"
_HV_CMD_RESTART = "Restart-VM {vm_id}"
_HV_CMD_PAUSE = "Suspend-VM {vm_id}"
_HV_CMD_RESUME = "Resume-VM {vm_id}"
_HV_CMD_CREATE_CHECKPOINT = "Checkpoint-VM {vm_id}{name}"
_HV_CMD_DELETE_CHECKPOINT = "Remove-VMCheckpoint {checkpoint_id}"


class AgentHyperVProvider(HyperVProvider):
    """Hyper-V provider backed by agent remote inventory data.

    Write operations queue commands to the managing agent for
    execution on the remote Hyper-V host.
    """

    def __init__(
        self,
        inventory: dict,
        target_hostname: str = "",
        agent_id: int | None = None,
        target_id: int | None = None,
        dispatch_cmd: callable | None = None,
    ) -> None:
        self._inventory = inventory
        self._hostname = target_hostname
        self._agent_id = agent_id
        self._target_id = target_id
        self._dispatch_cmd = dispatch_cmd

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

    async def _dispatch(self, command_str: str) -> dict:
        """Dispatch a PowerShell command to the managing agent."""
        if not self._dispatch_cmd:
            return {"success": False, "error": "No agent dispatch available for this host"}
        try:
            result = await self._dispatch_cmd(command_str)
            return result
        except Exception as e:
            logger.exception("Agent dispatch failed for target %s", self._target_id)
            return {"success": False, "error": str(e)}

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
        states = [_HYPERV_STATE_MAP.get(v.get("state"), str(v.get("state", "")).lower()) for v in vms]
        running = sum(1 for s in states if s == "running")
        stopped = sum(1 for s in states if s == "stopped")
        paused = sum(1 for s in states if s == "paused")
        saved = sum(1 for s in states if s == "saved")
        total_mem = sum((v.get("memory_mb") or 0) for v in vms)
        hostname = self._hostname
        if not hostname and vms:
            for key in ("ComputerName", "computer_name", "HostName", "hostname"):
                values = [v.get(key) for v in vms if v.get(key)]
                if values:
                    hostname = max(set(values), key=values.count)
                    break
        return {
            "connected": True,
            "hostname": hostname,
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
            uptime_seconds = 0
            uptime_raw = v.get("uptime", v.get("Uptime", 0))
            if isinstance(uptime_raw, (int, float)):
                uptime_seconds = int(uptime_raw)
            elif isinstance(uptime_raw, str):
                try:
                    uptime_seconds = int(float(uptime_raw))
                except (ValueError, TypeError):
                    uptime_seconds = 0
            elif isinstance(uptime_raw, dict):
                uptime_seconds = int(uptime_raw.get("TotalSeconds", 0))

            cpu_usage = float(v.get("cpu_usage", v.get("CPUUsage", 0)) or 0)
            memory_assigned = v.get("memory_assigned_mb") or v.get("MemoryAssigned")
            memory_startup = v.get("memory_startup_mb") or v.get("MemoryStartup")
            if memory_assigned is not None:
                memory_assigned = int(memory_assigned / (1024 * 1024))
            else:
                memory_assigned = 0
            if memory_startup is not None:
                memory_startup = int(memory_startup / (1024 * 1024))
            else:
                memory_startup = 0

            name = v.get("name", v.get("Name", ""))
            host_server = v.get("computer_name", v.get("ComputerName", self._hostname))

            items.append({
                "id": v.get("vm_id", v.get("VMId", name)),
                "name": name,
                "state": _HYPERV_STATE_MAP.get(v.get("state", v.get("State", -1)), str(v.get("state", v.get("State", "unknown"))).lower()),
                "cpu_count": 0,
                "cpu_usage_percent": cpu_usage,
                "memory_assigned_mb": memory_assigned,
                "memory_startup_mb": memory_startup,
                "memory_demand_mb": 0,
                "uptime_seconds": uptime_seconds,
                "host_server": host_server,
                "guest_os": "",
                "creation_time": "",
                "last_checkpoint": None,
                "status_message": v.get("status", v.get("Status", "")),
                "integration_services_enabled": True,
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
    # VM actions (dispatched to agent via command queue)                  #
    # ------------------------------------------------------------------ #

    async def start_vm(self, vm_id: str) -> dict:
        cmd = _vm_command(vm_id, 'Start-VM')
        return await self._dispatch(cmd)

    async def stop_vm(self, vm_id: str, force: bool = False) -> dict:
        force_flag = " -Force" if force else ""
        cmd = _vm_command(vm_id, 'Stop-VM') + force_flag
        return await self._dispatch(cmd)

    async def restart_vm(self, vm_id: str) -> dict:
        cmd = _vm_command(vm_id, 'Restart-VM')
        return await self._dispatch(cmd)

    async def pause_vm(self, vm_id: str) -> dict:
        cmd = _vm_command(vm_id, 'Suspend-VM')
        return await self._dispatch(cmd)

    async def resume_vm(self, vm_id: str) -> dict:
        cmd = _vm_command(vm_id, 'Resume-VM')
        return await self._dispatch(cmd)

    # ------------------------------------------------------------------ #
    # Networks                                                            #
    # ------------------------------------------------------------------ #

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
        name_flag = f" -SnapshotName '{name}'" if name else ""
        cmd = _vm_command(vm_id, 'Checkpoint-VM') + name_flag
        return await self._dispatch(cmd)

    async def delete_snapshot(self, vm_id: str, snapshot_id: str) -> dict:
        return await self.delete_checkpoint(vm_id, snapshot_id)

    async def delete_checkpoint(self, vm_id: str, checkpoint_id: str) -> dict:
        cmd = f"Get-VMCheckpoint -Id '{checkpoint_id}' | Remove-VMCheckpoint"
        return await self._dispatch(cmd)

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
