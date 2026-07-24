"""Mission Control Agent - PowerShell Remoting connector."""

import asyncio
import json
import logging
from typing import Any

from .base import RemoteConnector

logger = logging.getLogger("mc-agent")


class PSRemotingConnector(RemoteConnector):
    """Connect to Windows targets via PowerShell Remoting (WSMan)."""

    async def _run_ps(self, script: str, timeout: int = 30) -> dict:
        """Run a PowerShell script on the remote host via Invoke-Command."""
        cred_ps = (
            f"$secPwd = ConvertTo-SecureString '{self.password}' "
            f"-AsPlainText -Force; "
            f"$cred = New-Object System.Management.Automation.PSCredential"
            f"('{self.username}', $secPwd)"
        )

        escaped_script = script.replace("'", "''")
        full_cmd = (
            f"powershell -NoProfile -Command "
            f"\"{cred_ps}; "
            f"Invoke-Command -ComputerName '{self.hostname}' "
            f"-Port {self.port} -Credential $cred "
            f"-ScriptBlock {{ {escaped_script} }} "
            f"-ErrorAction Stop\""
        )

        try:
            proc = await asyncio.create_subprocess_shell(
                full_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
            return {
                "success": proc.returncode == 0,
                "stdout": stdout.decode(errors="replace"),
                "stderr": stderr.decode(errors="replace"),
                "exit_code": proc.returncode,
            }
        except asyncio.TimeoutError:
            return {"success": False, "stdout": "", "stderr": "Command timed out", "exit_code": -1}
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e), "exit_code": -1}

    async def test_connection(self) -> dict:
        result = await self._run_ps("hostname", timeout=10)
        if result["success"]:
            return {"connected": True, "hostname": result["stdout"].strip(), "latency_ms": 0}
        return {"connected": False, "error": result["stderr"], "latency_ms": 0}

    async def execute(self, command: str, timeout: int = 60) -> dict:
        return await self._run_ps(command, timeout=timeout)

    async def collect_system_inventory(self) -> dict:
        script = (
            "$os = Get-CimInstance Win32_OperatingSystem; "
            "$cpu = Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average; "
            "$mem = Get-CimInstance Win32_ComputerSystem; "
            "$disks = Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' | "
            "Select-Object DeviceID, @{N='SizeGB';E={[math]::Round($_.Size/1GB,1)}}, "
            "@{N='FreeGB';E={[math]::Round($_.FreeSpace/1GB,1)}}, FileSystem; "
            "$net = Get-NetIPAddress -AddressFamily IPv4 | "
            "Select-Object InterfaceAlias, IPAddress; "
            "@{ "
            "  os = @{ name=$os.Caption; version=$os.Version; "
            "          arch=$os.OSArchitecture; "
            "          boot_time=$os.LastBootUpTime.ToString('o') }; "
            "  cpu = @{ cores=$env:NUMBER_OF_PROCESSORS; "
            "           percent=[math]::Round($cpu.Average,1) }; "
            "  memory = @{ total_gb=[math]::Round($mem.TotalPhysicalMemory/1GB,1); "
            "              free_gb=[math]::Round($os.FreePhysicalMemory/1MB,1) }; "
            "  disks = $disks | ForEach-Object { "
            "    @{ id=$_.DeviceID; size_gb=$_.SizeGB; free_gb=$_.FreeGB; "
            "       fs=$_.FileSystem } }; "
            "  network = $net | ForEach-Object { "
            "    @{ iface=$_.InterfaceAlias; ip=$_.IPAddress } } "
            "} | ConvertTo-Json -Depth 5"
        )
        result = await self._run_ps(script, timeout=30)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except json.JSONDecodeError:
                return {"raw": result["stdout"]}
        return {"error": result["stderr"]}

    async def collect_hyperv_inventory(self) -> dict | None:
        script = (
            "if (Get-Command Get-VM -ErrorAction SilentlyContinue) { "
            "  $vms = Get-VM | Select-Object Name, State, CPUUsage, "
            "    MemoryAssigned, MemoryStartup, Uptime, Status, Generation, "
            "    VMId, ComputerName | ConvertTo-Json -Depth 3; "
            "  $sw = Get-VMSwitch | Select-Object Name, SwitchType | "
            "    ConvertTo-Json; "
            "  @{ vm_count=(Get-VM).Count; vms=$vms; switches=$sw } | "
            "  ConvertTo-Json -Depth 3 "
            "} else { 'null' }"
        )
        result = await self._run_ps(script, timeout=30)
        if result["success"]:
            try:
                data = json.loads(result["stdout"])
                if data and data.get("vm_count", 0) > 0:
                    vms_raw = data.get("vms", "[]")
                    switches_raw = data.get("switches", "[]")
                    vms = json.loads(vms_raw) if isinstance(vms_raw, str) else vms_raw
                    switches = json.loads(switches_raw) if isinstance(switches_raw, str) else switches_raw
                    if isinstance(vms, dict):
                        vms = [vms]
                    if isinstance(switches, dict):
                        switches = [switches]
                    return {
                        "vm_count": data["vm_count"],
                        "vms": [
                            {
                                "name": v.get("Name", ""),
                                "state": v.get("State", "Unknown"),
                                "cpu_usage": v.get("CPUUsage", 0),
                                "memory_mb": round((v.get("MemoryAssigned") or 0) / (1024 * 1024), 0),
                                "memory_startup_mb": round((v.get("MemoryStartup") or 0) / (1024 * 1024), 0),
                                "uptime": str(v.get("Uptime", "")),
                                "status": v.get("Status", ""),
                                "generation": v.get("Generation", 0),
                                "vm_id": v.get("VMId", ""),
                                "computer_name": v.get("ComputerName", ""),
                            }
                            for v in vms
                        ],
                        "switches": [
                            {"name": s.get("Name", ""), "type": s.get("SwitchType", "")}
                            for s in switches
                        ],
                    }
            except (json.JSONDecodeError, TypeError):
                pass
        return None

    async def collect_services(self) -> list[dict]:
        script = (
            "Get-Service | Where-Object {$_.Status -eq 'Running'} | "
            "Select-Object Name, DisplayName, Status | "
            "ConvertTo-Json -Depth 2"
        )
        result = await self._run_ps(script, timeout=15)
        if result["success"]:
            try:
                data = json.loads(result["stdout"])
                if isinstance(data, dict):
                    data = [data]
                return [
                    {"name": s.get("Name", ""), "display_name": s.get("DisplayName", ""), "status": s.get("Status", "")}
                    for s in data
                ]
            except json.JSONDecodeError:
                pass
        return []

    async def disconnect(self) -> None:
        pass
