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
    "Running": "running",
    "Off": "stopped",
    "Stopped": "stopped",
    "Paused": "paused",
    "Saved": "saved",
    "Stopping": "stopped",
    "Saving": "saved",
    "Pausing": "paused",
}

_SWITCH_TYPE_MAP = {
    0: "external",
    1: "internal",
    2: "private",
}


def _switch_type_name(value) -> str:
    """Map a switch type to a lowercase name.

    Accepts Hyper-V int codes (0=external, 1=internal, 2=private) and
    PascalCase/lowercase strings (``"External"``, ``"internal"``, ...).
    """
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("external", "internal", "private"):
            return lowered
        return lowered
    return _SWITCH_TYPE_MAP.get(value, str(value).lower())


def _uptime_seconds(raw) -> int:
    """Parse an uptime value into seconds.

    Handles plain numbers, TimeSpan dicts, and the string repr of a
    TimeSpan dict (e.g. ``"{'TotalSeconds': 174822.92, ...}"``).
    """
    if isinstance(raw, dict):
        total = raw.get("TotalSeconds")
        return int(total) if isinstance(total, (int, float)) else 0
    if isinstance(raw, (int, float)):
        return int(raw)
    if isinstance(raw, str):
        match = re.search(r"TotalSeconds['\"]?\s*:\s*([0-9.]+)", raw)
        if match:
            return int(float(match.group(1)))
        try:
            return int(float(raw.strip()))
        except (ValueError, TypeError):
            return 0
    return 0


def _most_common_hostname(vms: list[dict], fallback: str = "") -> str:
    """Return the most common ComputerName among VMs, else the fallback."""
    for key in ("ComputerName", "computer_name", "HostName", "hostname"):
        values = [v.get(key) for v in vms if v.get(key)]
        if values:
            return max(set(values), key=values.count)
    return fallback


def _vm_memory_bytes(vm: dict) -> tuple[float, float]:
    """Return (configured, assigned) memory in bytes for a VM record.

    The agent relays ``MemoryStartup``/``MemoryAssigned`` as bytes, but
    older/plugin records may carry ``*_mb`` fields in MB.  MB values are
    treated as MB (< 1e6) and converted; byte values pass through.
    """
    startup = vm.get("MemoryStartup") or vm.get("memory_startup_mb") or 0
    assigned = vm.get("MemoryAssigned") or vm.get("memory_assigned_mb") or 0
    if startup and startup < 1e6:
        startup *= 1024 * 1024
    if assigned and assigned < 1e6:
        assigned *= 1024 * 1024
    return float(startup), float(assigned)


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
        states = []
        total_bytes = 0.0
        used_bytes = 0.0
        for v in vms:
            state = v.get("state", v.get("State", ""))
            states.append(_HYPERV_STATE_MAP.get(state, str(state).lower()))
            startup, assigned = _vm_memory_bytes(v)
            total_bytes += startup
            used_bytes += assigned
        running = sum(1 for s in states if s == "running")
        stopped = sum(1 for s in states if s == "stopped")
        paused = sum(1 for s in states if s == "paused")
        saved = sum(1 for s in states if s == "saved")
        hostname = _most_common_hostname(vms, self._hostname)
        return {
            "connected": True,
            "hostname": hostname,
            "total_vms": len(vms),
            "running": running,
            "stopped": stopped,
            "paused": paused,
            "saved": saved,
            "total_cpu": sum(v.get("cpu_usage", v.get("CPUUsage", 0)) for v in vms),
            "total_memory_gb": round(total_bytes / (1024 ** 3), 1),
            "used_memory_gb": round(used_bytes / (1024 ** 3), 1),
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
            state = v.get("state", v.get("State", -1))

            items.append({
                "id": v.get("vm_id", v.get("VMId", name)),
                "name": name,
                "state": _HYPERV_STATE_MAP.get(state, str(state).lower()),
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
        items = []
        for i, s in enumerate(switches):
            name = s.get("Name", s.get("name", ""))
            items.append({
                "id": s.get("Id", s.get("VMId", name or str(i))),
                "name": name,
                "switch_type": _switch_type_name(s.get("SwitchType", s.get("type", -1))),
                "allow_management_os": bool(s.get("AllowManagementOS", s.get("allow_management_os", False))),
                "net_adapter": s.get("NetAdapterInterfaceDescription", s.get("adapter")),
                "status": "operational",
            })
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
        vms = self._get_vm_list()
        hostname = _most_common_hostname(vms, self._hostname)
        total_bytes = 0.0
        used_bytes = 0.0
        cpu_usage = 0.0
        uptime = 0
        for v in vms:
            startup, assigned = _vm_memory_bytes(v)
            total_bytes += startup
            used_bytes += assigned
            state = v.get("state", v.get("State", ""))
            if _HYPERV_STATE_MAP.get(state) == "running":
                cpu_usage = max(cpu_usage, float(v.get("CPUUsage", v.get("cpu_usage", 0)) or 0))
                uptime = max(uptime, _uptime_seconds(v.get("Uptime", v.get("uptime", 0))))
        total_gb = total_bytes / (1024 ** 3)
        used_gb = used_bytes / (1024 ** 3)
        mem_percent = round(used_gb / total_gb * 100, 1) if total_gb > 0 else 0.0
        return {
            "connected": True,
            "status": "healthy",
            "hosts": [
                {
                    "name": hostname,
                    "status": "healthy",
                    "cpu_percent": round(cpu_usage, 1),
                    "memory_percent": mem_percent,
                    "memory_used_gb": round(used_gb, 1),
                    "memory_total_gb": round(total_gb, 1),
                    "uptime_seconds": uptime,
                    "vm_count": len(vms),
                    "version": "agent",
                }
            ],
            "cluster_summary": "Agent-relayed host",
        }
