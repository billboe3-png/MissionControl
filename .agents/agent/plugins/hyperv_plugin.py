"""Mission Control Agent - Hyper-V plugin."""

import asyncio
import json
import logging
import platform
from typing import Any

from agent.plugin import AgentPlugin

logger = logging.getLogger("mc-agent")


class HyperVPlugin(AgentPlugin):
    """Hyper-V virtualization management plugin."""

    name = "hyperv"
    version = "3.0.0-rc1"
    description = "Hyper-V virtual machine management plugin"
    platform_required = "windows"

    def __init__(self):
        self._context: dict[str, Any] = {}
        self._has_module: bool | None = None

    async def initialize(self, context: dict[str, Any]) -> bool:
        self._context = context
        self._has_module = await self._check_hyper_v()
        if not self._has_module:
            logger.warning("Hyper-V module not available on this host")
            return False
        logger.info("Hyper-V plugin initialized for %s", platform.node())
        return True

    async def collect_inventory(self) -> dict[str, Any]:
        """Collect Hyper-V inventory: VMs, switches, virtual disks."""
        vms = await self._get_vms()
        switches = await self._get_switches()
        return {
            "vm_count": len(vms),
            "vms": vms,
            "switches": switches,
        }

    async def execute_command(
        self, command: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute Hyper-V commands."""
        handlers = {
            "get-vm": self._get_vm_detail,
            "start-vm": self._start_vm,
            "stop-vm": self._stop_vm,
            "restart-vm": self._restart_vm,
            "get-vm-checkpoint": self._get_checkpoints,
            "new-vm-checkpoint": self._create_checkpoint,
            "get-vm-snapshot": self._get_checkpoints,
            "remove-vm-snapshot": self._remove_checkpoint,
            "get-vm-network": self._get_vm_nics,
            "get-vm-disk": self._get_vm_disks,
        }
        handler = handlers.get(command)
        if handler:
            return await handler(args)
        return {"success": False, "error": f"Unknown command: {command}"}

    async def _check_hyper_v(self) -> bool:
        """Check if Hyper-V PowerShell module is available."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "powershell", "-Command",
                "if (Get-Command Get-VM -ErrorAction SilentlyContinue)"
                " { exit 0 } else { exit 1 }",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await asyncio.wait_for(proc.communicate(), timeout=10)
            return proc.returncode == 0
        except Exception:
            return False

    async def _get_vms(self) -> list[dict[str, Any]]:
        """Get all VMs with status and basic info."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "powershell", "-Command",
                "Get-VM | Select-Object Name, State, "
                "CPUUsage, MemoryAssigned, MemoryStartup, "
                "Uptime, Status, Generation, "
                "VMId, ComputerName | ConvertTo-Json -Depth 3",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
            data = json.loads(stdout.decode() or "[]")
            if isinstance(data, dict):
                data = [data]
            return [
                {
                    "name": vm.get("Name", ""),
                    "state": vm.get("State", "Unknown"),
                    "cpu_usage": vm.get("CPUUsage", 0),
                    "memory_mb": round(
                        (vm.get("MemoryAssigned") or 0) / (1024 * 1024), 0
                    ),
                    "memory_startup_mb": round(
                        (vm.get("MemoryStartup") or 0) / (1024 * 1024), 0
                    ),
                    "uptime": str(vm.get("Uptime", "")),
                    "status": vm.get("Status", ""),
                    "generation": vm.get("Generation", 0),
                    "vm_id": vm.get("VMId", ""),
                    "computer_name": vm.get("ComputerName", ""),
                }
                for vm in data
            ]
        except Exception as e:
            logger.error("Failed to get VMs: %s", e)
            return []

    async def _get_switches(self) -> list[dict[str, Any]]:
        """Get virtual switches."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "powershell", "-Command",
                "Get-VMSwitch | Select-Object Name, SwitchType, "
                "NetAdapterInterfaceDescription | ConvertTo-Json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=15)
            data = json.loads(stdout.decode() or "[]")
            if isinstance(data, dict):
                data = [data]
            return [
                {
                    "name": s.get("Name", ""),
                    "type": s.get("SwitchType", ""),
                    "adapter": s.get("NetAdapterInterfaceDescription", ""),
                }
                for s in data
            ]
        except Exception:
            return []

    async def _get_vm_detail(
        self, args: dict[str, Any]
    ) -> dict[str, Any]:
        """Get detailed info for a specific VM."""
        vm_name = args.get("name", "")
        proc = await asyncio.create_subprocess_exec(
            "powershell", "-Command",
            f"Get-VM '{vm_name}' | ConvertTo-Json -Depth 5",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15)
        return {
            "success": proc.returncode == 0,
            "stdout": stdout.decode(errors="replace"),
            "stderr": stderr.decode(errors="replace"),
        }

    async def _start_vm(self, args: dict[str, Any]) -> dict[str, Any]:
        vm_name = args.get("name", "")
        proc = await asyncio.create_subprocess_exec(
            "powershell", "-Command",
            f"Start-VM -Name '{vm_name}'",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        return {
            "success": proc.returncode == 0,
            "stdout": stdout.decode(errors="replace"),
            "stderr": stderr.decode(errors="replace"),
        }

    async def _stop_vm(self, args: dict[str, Any]) -> dict[str, Any]:
        vm_name = args.get("name", "")
        force = args.get("force", False)
        cmd = f"Stop-VM -Name '{vm_name}'"
        if force:
            cmd += " -Force"
        proc = await asyncio.create_subprocess_exec(
            "powershell", "-Command", cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
        return {
            "success": proc.returncode == 0,
            "stdout": stdout.decode(errors="replace"),
            "stderr": stderr.decode(errors="replace"),
        }

    async def _restart_vm(self, args: dict[str, Any]) -> dict[str, Any]:
        vm_name = args.get("name", "")
        force = args.get("force", False)
        cmd = f"Restart-VM -Name '{vm_name}'"
        if force:
            cmd += " -Force"
        proc = await asyncio.create_subprocess_exec(
            "powershell", "-Command", cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
        return {
            "success": proc.returncode == 0,
            "stdout": stdout.decode(errors="replace"),
            "stderr": stderr.decode(errors="replace"),
        }

    async def _get_checkpoints(
        self, args: dict[str, Any]
    ) -> dict[str, Any]:
        vm_name = args.get("name", "")
        proc = await asyncio.create_subprocess_exec(
            "powershell", "-Command",
            f"Get-VMSnapshot -VMName '{vm_name}'"
            " | Select-Object Name, CreationTime, CheckpointType, "
            "ParentCheckpointName | ConvertTo-Json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15)
        return {
            "success": proc.returncode == 0,
            "stdout": stdout.decode(errors="replace"),
            "stderr": stderr.decode(errors="replace"),
        }

    async def _create_checkpoint(
        self, args: dict[str, Any]
    ) -> dict[str, Any]:
        vm_name = args.get("name", "")
        snap_name = args.get("snapshot_name", "")
        cmd = f"Checkpoint-VM -Name '{vm_name}'"
        if snap_name:
            cmd += f" -SnapshotName '{snap_name}'"
        proc = await asyncio.create_subprocess_exec(
            "powershell", "-Command", cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
        return {
            "success": proc.returncode == 0,
            "stdout": stdout.decode(errors="replace"),
            "stderr": stderr.decode(errors="replace"),
        }

    async def _remove_checkpoint(
        self, args: dict[str, Any]
    ) -> dict[str, Any]:
        vm_name = args.get("name", "")
        snap_name = args.get("snapshot_name", "")
        proc = await asyncio.create_subprocess_exec(
            "powershell", "-Command",
            f"Remove-VMSnapshot -VMName '{vm_name}'"
            f" -Name '{snap_name}'",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        return {
            "success": proc.returncode == 0,
            "stdout": stdout.decode(errors="replace"),
            "stderr": stderr.decode(errors="replace"),
        }

    async def _get_vm_nics(
        self, args: dict[str, Any]
    ) -> dict[str, Any]:
        vm_name = args.get("name", "")
        proc = await asyncio.create_subprocess_exec(
            "powershell", "-Command",
            f"Get-VMNetworkAdapter -VMName '{vm_name}'"
            " | Select-Object Name, SwitchName, "
            "MacAddress, IPAddresses, Status "
            "| ConvertTo-Json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15)
        return {
            "success": proc.returncode == 0,
            "stdout": stdout.decode(errors="replace"),
            "stderr": stderr.decode(errors="replace"),
        }

    async def _get_vm_disks(
        self, args: dict[str, Any]
    ) -> dict[str, Any]:
        vm_name = args.get("name", "")
        proc = await asyncio.create_subprocess_exec(
            "powershell", "-Command",
            f"Get-VMHardDiskDrive -VMName '{vm_name}'"
            " | Select-Object ControllerType, ControllerNumber, "
            "ControllerLocation, Path, DiskNumber "
            "| ConvertTo-Json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15)
        return {
            "success": proc.returncode == 0,
            "stdout": stdout.decode(errors="replace"),
            "stderr": stderr.decode(errors="replace"),
        }
