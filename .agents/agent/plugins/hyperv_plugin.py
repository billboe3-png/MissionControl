"""Mission Control Agent - Hyper-V plugin."""

import asyncio
import base64
import json
import logging
import platform
from typing import Any

from agent.plugin import AgentPlugin

logger = logging.getLogger("mc-agent")


class HyperVPlugin(AgentPlugin):
    """Hyper-V virtualization management plugin with SSH relay support."""

    name = "hyperv"
    version = "3.0.0-rc1"
    description = "Hyper-V virtual machine management plugin"
    platform_required = "windows"

    def __init__(self):
        self._context: dict[str, Any] = {}
        self._has_module: bool | None = None
        self._api_base: str = ""
        self._username: str = ""
        self._password: str = ""
        self._use_relay: bool = False
        self._ssh_target: dict[str, Any] | None = None

    async def initialize(self, context: dict[str, Any]) -> bool:
        self._context = context or {}
        self._has_module = await self._check_hyper_v()
        self._use_relay = False
        self._ssh_target = None
        if not self._has_module:
            logger.warning("Hyper-V module not available on this host")
            return False
        await self._ensure_configured()
        target = self._ssh_target
        if target:
            logger.info(
                "Hyper-V plugin initialized for %s via %s (%s)",
                platform.node(),
                target.get("protocol"),
                target.get("hostname"),
            )
        else:
            logger.info("Hyper-V plugin initialized for %s", platform.node())
        return True

    def reinitialize(self) -> None:
        self._configured_from_context = False
        self._use_relay = False
        self._ssh_target = None

    async def collect_inventory(self) -> dict[str, Any]:
        await self._ensure_configured()
        if self._use_relay and self._ssh_target:
            return await self._collect_inventory_relay()
        vms = await self._get_vms()
        switches = await self._get_switches()
        return {
            "vm_count": len(vms),
            "vms": vms,
            "switches": switches,
        }

    async def execute_command(self, command: str, args: dict[str, Any]) -> dict[str, Any]:
        await self._ensure_configured()
        if self._use_relay and self._ssh_target:
            return await self._execute_relay(command, args)
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

    async def _ensure_configured(self) -> None:
        if getattr(self, "_configured_from_context", False):
            return
        self._configured_from_context = True
        self._api_base = ""
        self._username = ""
        self._password = ""
        self._use_relay = False
        self._ssh_target = None

        profiles = (
            self._context.get("integration_profiles")
            or self._context.get("integration_profile")
            or []
        )
        if isinstance(profiles, dict):
            profiles = [profiles]

        hv_profile = None
        for p in profiles:
            if not isinstance(p, dict):
                continue
            if (p.get("integration_type") or "").lower() == "hyperv":
                hv_profile = p
                break

        if hv_profile:
            self._api_base = hv_profile.get("base_url") or self._api_base
            self._username = hv_profile.get("username") or self._username
            self._password = hv_profile.get("password") or self._password
            ssh_host = hv_profile.get("ssh_host")
            ssh_port = hv_profile.get("ssh_port") or 5985
            ssh_username = hv_profile.get("ssh_username") or self._username
            ssh_password = hv_profile.get("password") or self._password
            if ssh_host:
                self._ssh_target = {
                    "id": hv_profile.get("id"),
                    "name": hv_profile.get("name") or ssh_host,
                    "hostname": ssh_host,
                    "port": ssh_port,
                    "username": ssh_username,
                    "password": ssh_password,
                    "protocol": "ssh",
                }
                self._use_relay = True
                logger.info("Hyper-V plugin using integration profile SSH relay (%s)", ssh_host)
                return

        remote_targets = self._context.get("remote_targets") or []
        for target in remote_targets:
            if not isinstance(target, dict):
                continue
            if (target.get("protocol") or "").lower() == "ssh":
                self._ssh_target = target
                self._use_relay = True
                logger.info(
                    "Hyper-V plugin using existing SSH target (%s)",
                    target.get("hostname"),
                )
                return

    # ------------------------------------------------------------------ #
    # Relay helpers
    # ------------------------------------------------------------------ #

    async def _collect_inventory_relay(self) -> dict[str, Any]:
        remote_manager = self._context.get("remote_manager")
        if not remote_manager or not self._ssh_target:
            logger.warning("Hyper-V relay blocked: missing remote_manager or ssh_target")
            return {"vm_count": 0, "vms": [], "switches": []}
        target_id = self._ssh_target.get("id")
        if target_id is None:
            logger.warning("Hyper-V relay blocked: missing target id")
            return {"vm_count": 0, "vms": [], "switches": []}

        vms_script = (
            "Get-VM | ForEach-Object { "
            "[PSCustomObject]@{"
            "Name=$_.Name; State=$_.State.ToString(); "
            "CPUUsage=$_.CPUUsage; MemoryAssigned=$_.MemoryAssigned; "
            "MemoryStartup=$_.MemoryStartup; Uptime=$_.Uptime; "
            "ComputerName=$_.ComputerName; Generation=$_.Generation; "
            "VMId=$_.VMId.ToString() } } | ConvertTo-Json -Depth 3"
        )
        switches_script = (
            "Get-VMSwitch | ForEach-Object { "
            "[PSCustomObject]@{"
            "Name=$_.Name; SwitchType=$_.SwitchType.ToString(); "
            "NetAdapterInterfaceDescription=$_.NetAdapterInterfaceDescription } } "
            "| ConvertTo-Json"
        )

        vms: list[dict[str, Any]] = []
        switches: list[dict[str, Any]] = []

        vms_result = await remote_manager.execute_on_target(
            target_id=target_id,
            command=f"powershell -NoProfile -NonInteractive -EncodedCommand {self._encode(vms_script)}",
            timeout=60,
        )
        if vms_result.get("success"):
            raw_vms = vms_result.get("stdout") or "[]"
            parsed = self._parse_json_array(raw_vms)
            if parsed is not None:
                vms = parsed
            else:
                logger.warning("Hyper-V VM relay returned non-JSON stdout: %r", raw_vms[:500])
        else:
            logger.warning("Hyper-V VM relay failed: %s", vms_result.get("stderr") or vms_result.get("stdout"))

        switches_result = await remote_manager.execute_on_target(
            target_id=target_id,
            command=f"powershell -NoProfile -NonInteractive -EncodedCommand {self._encode(switches_script)}",
            timeout=60,
        )
        if switches_result.get("success"):
            raw_switches = switches_result.get("stdout") or "[]"
            parsed = self._parse_json_array(raw_switches)
            if parsed is not None:
                switches = parsed
            else:
                logger.warning("Hyper-V switch relay returned non-JSON stdout: %r", raw_switches[:500])
        else:
            logger.warning("Hyper-V switch relay failed: %s", switches_result.get("stderr") or switches_result.get("stdout"))

        result = {
            "vm_count": len(vms),
            "vms": vms,
            "switches": switches,
        }
        logger.info("Hyper-V relay inventory result: %s", result)
        return result

    async def _execute_relay(self, command: str, args: dict[str, Any]) -> dict[str, Any]:
        remote_manager = self._context.get("remote_manager")
        if not remote_manager or not self._ssh_target:
            return {"success": False, "error": "No relay target configured"}
        target_id = self._ssh_target.get("id")
        if target_id is None:
            return {"success": False, "error": "Missing target id for relay"}

        script = self._build_relay_script(command, args)
        if script is None:
            return {"success": False, "error": f"Unsupported relay command: {command}"}

        result = await remote_manager.execute_on_target(
            target_id=target_id,
            command=f"powershell -NoProfile -NonInteractive -EncodedCommand {self._encode(script)}",
            timeout=120,
        )
        return {
            "success": result.get("success", False),
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
            "exit_code": result.get("exit_code", -1),
        }

    @staticmethod
    def _encode(script: str) -> str:
        return base64.b64encode(script.encode("utf-16-le")).decode("ascii")

    @staticmethod
    def _parse_json_array(raw: str) -> list[dict[str, Any]] | None:
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                return [data]
            if isinstance(data, list):
                return data
        except (json.JSONDecodeError, TypeError):
            pass
        return None

    def _build_relay_script(self, command: str, args: dict[str, Any]) -> str | None:
        vm_name = args.get("name", "")
        vm_id = args.get("vm_id", "")
        force = bool(args.get("force", False))
        snap_name = args.get("snapshot_name", "")

        if command == "get-vm":
            if vm_id:
                return f"Get-VM -Id '{vm_id}' | ConvertTo-Json -Depth 5"
            if vm_name:
                return f"Get-VM -Name '{vm_name}' | ConvertTo-Json -Depth 5"
            return "Get-VM | ConvertTo-Json -Depth 3"

        if command == "start-vm":
            if vm_id:
                return f"Get-VM -Id '{vm_id}' | Start-VM -PassThru | Select-Object Name,State | ConvertTo-Json"
            if vm_name:
                return f"Start-VM -Name '{vm_name}' | ConvertTo-Json"
            return "Start-VM -Name '' | ConvertTo-Json"

        if command == "stop-vm":
            flag = "-Force" if force else ""
            if vm_id:
                return f"Get-VM -Id '{vm_id}' | Stop-VM {flag} | ConvertTo-Json"
            if vm_name:
                return f"Stop-VM -Name '{vm_name}' {flag} | ConvertTo-Json"
            return "Stop-VM -Name '' | ConvertTo-Json"

        if command == "restart-vm":
            flag = "-Force" if force else ""
            if vm_id:
                return f"Get-VM -Id '{vm_id}' | Restart-VM {flag} | ConvertTo-Json"
            if vm_name:
                return f"Restart-VM -Name '{vm_name}' {flag} | ConvertTo-Json"
            return "Restart-VM -Name '' | ConvertTo-Json"

        if command in ("get-vm-checkpoint", "get-vm-snapshot"):
            if vm_id:
                return (
                    f"Get-VMCheckpoint -VMId '{vm_id}' | "
                    "Select-Object Name,CreationTime,CheckpointType | ConvertTo-Json"
                )
            if vm_name:
                return (
                    f"Get-VMSnapshot -VMName '{vm_name}' | "
                    "Select-Object Name,CreationTime,CheckpointType | ConvertTo-Json"
                )
            return "Get-VMSnapshot | Select-Object Name,CreationTime,CheckpointType | ConvertTo-Json"

        if command == "new-vm-checkpoint":
            name_flag = f" -SnapshotName '{snap_name}'" if snap_name else ""
            if vm_id:
                return f"Checkpoint-VM -Id '{vm_id}'{name_flag} | ConvertTo-Json"
            if vm_name:
                return f"Checkpoint-VM -Name '{vm_name}'{name_flag} | ConvertTo-Json"
            return "Checkpoint-VM -Name '' | ConvertTo-Json"

        if command == "remove-vm-snapshot":
            if vm_id and snap_name:
                return f"Remove-VMSnapshot -Id '{vm_id}' -Name '{snap_name}' -Confirm:$false | ConvertTo-Json"
            if vm_name and snap_name:
                return f"Remove-VMSnapshot -VMName '{vm_name}' -Name '{snap_name}' -Confirm:$false | ConvertTo-Json"
            return "Remove-VMSnapshot -Name '' -Confirm:$false | ConvertTo-Json"

        if command == "get-vm-network":
            if vm_id:
                return (
                    f"Get-VMNetworkAdapter -VMId '{vm_id}' | "
                    "Select-Object Name,SwitchName,MacAddress,Status | ConvertTo-Json"
                )
            if vm_name:
                return (
                    f"Get-VMNetworkAdapter -VMName '{vm_name}' | "
                    "Select-Object Name,SwitchName,MacAddress,Status | ConvertTo-Json"
                )
            return "Get-VMNetworkAdapter | Select-Object Name,SwitchName,MacAddress,Status | ConvertTo-Json"

        if command == "get-vm-disk":
            if vm_id:
                return (
                    f"Get-VMHardDiskDrive -VMId '{vm_id}' | "
                    "Select-Object ControllerType,ControllerNumber,ControllerLocation,Path | ConvertTo-Json"
                )
            if vm_name:
                return (
                    f"Get-VMHardDiskDrive -VMName '{vm_name}' | "
                    "Select-Object ControllerType,ControllerNumber,ControllerLocation,Path | ConvertTo-Json"
                )
            return "Get-VMHardDiskDrive | Select-Object ControllerType,ControllerNumber,ControllerLocation,Path | ConvertTo-Json"

        return None

    # ------------------------------------------------------------------ #
    # Local Hyper-V collectors
    # ------------------------------------------------------------------ #

    async def _check_hyper_v(self) -> bool:
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

    async def _get_vm_detail(self, args: dict[str, Any]) -> dict[str, Any]:
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

    async def _get_checkpoints(self, args: dict[str, Any]) -> dict[str, Any]:
        vm_name = args.get("name", "")
        proc = await asyncio.create_subprocess_exec(
            "powershell", "-Command",
            f"Get-VMSnapshot -VMName '{vm_name}'"
            " | Select-Object Name, CreationTime, CheckpointType | ConvertTo-Json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15)
        return {
            "success": proc.returncode == 0,
            "stdout": stdout.decode(errors="replace"),
            "stderr": stderr.decode(errors="replace"),
        }

    async def _create_checkpoint(self, args: dict[str, Any]) -> dict[str, Any]:
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

    async def _remove_checkpoint(self, args: dict[str, Any]) -> dict[str, Any]:
        vm_name = args.get("name", "")
        snap_name = args.get("snapshot_name", "")
        proc = await asyncio.create_subprocess_exec(
            "powershell", "-Command",
            f"Remove-VMSnapshot -VMName '{vm_name}' -Name '{snap_name}'",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        return {
            "success": proc.returncode == 0,
            "stdout": stdout.decode(errors="replace"),
            "stderr": stderr.decode(errors="replace"),
        }

    async def _get_vm_nics(self, args: dict[str, Any]) -> dict[str, Any]:
        vm_name = args.get("name", "")
        proc = await asyncio.create_subprocess_exec(
            "powershell", "-Command",
            f"Get-VMNetworkAdapter -VMName '{vm_name}'"
            " | Select-Object Name, SwitchName, MacAddress, IPAddresses, Status "
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

    async def _get_vm_disks(self, args: dict[str, Any]) -> dict[str, Any]:
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
