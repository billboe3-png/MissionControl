"""
Mission Control Hyper-V Production Provider

Connects to Hyper-V hosts via PowerShell Remoting over WinRM or SSH.
Configuration is injected from IntegrationProfile — never reads config.py.
"""

import asyncio
import base64
import json
import logging

import winrm

from .base_provider import HyperVProvider

logger = logging.getLogger(__name__)


async def _run_powershell_winrm(
    host: str,
    port: int,
    username: str,
    password: str,
    script: str,
    timeout: int = 30,
) -> dict:
    """Execute a PowerShell script on a remote host via WinRM."""
    endpoint = f"http://{host}:{port}/wsman"

    def _exec_sync():
        session = winrm.Session(
            endpoint,
            auth=(username, password),
            transport="ntlm",
            server_cert_validation="ignore",
            read_timeout_sec=timeout + 10,
            operation_timeout_sec=timeout,
        )
        return session.run_ps(script)

    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(_exec_sync),
            timeout=timeout + 10,
        )
        stdout = result.std_out or ""
        stderr = result.std_err or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        return {
            "success": result.status_code == 0,
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": result.status_code,
        }
    except asyncio.TimeoutError:
        return {"success": False, "stdout": "", "stderr": "Command timed out", "exit_code": -1}
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e), "exit_code": -1}


async def _run_powershell_ssh(
    host: str,
    port: int,
    username: str,
    password: str,
    script: str,
    timeout: int = 30,
) -> dict:
    """Execute a PowerShell script on a remote host via SSH."""
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    ps_exe = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
    remote_cmd = f"{ps_exe} -NoProfile -NonInteractive -EncodedCommand {encoded}"
    cmd = [
        "sshpass", "-p", password,
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", f"ConnectTimeout={timeout}",
        "-p", str(port),
        f"{username}@{host}",
        remote_cmd,
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={"HOME": "/tmp", "PATH": "/usr/local/bin:/usr/bin:/bin"},
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=timeout
        )
        return {
            "success": proc.returncode == 0,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "exit_code": proc.returncode,
        }
    except asyncio.TimeoutError:
        return {"success": False, "stdout": "", "stderr": "Command timed out", "exit_code": -1}
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e), "exit_code": -1}


def _parse_json_output(stdout: str) -> dict | list | None:
    """Extract JSON from PowerShell output."""
    text = stdout.strip()
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("{") or line.startswith("["):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None


class HyperVPowerShellProvider(HyperVProvider):
    """Production Hyper-V provider using PowerShell remoting over WinRM or SSH.

    Configuration is injected from IntegrationProfile fields:
      - base_url: Hyper-V host address
      - username: WinRM/SSH username
      - encrypted_secret: password (decrypted before injection)
      - timeout: operation timeout
      - domain: transport type ("winrm" or "ssh")
    """

    def __init__(
        self,
        host: str,
        port: int = 5985,
        username: str = "",
        password: str = "",
        timeout: int = 30,
        transport: str = "winrm",
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._timeout = timeout
        self._transport = transport

    async def _exec(self, script: str, timeout: int | None = None) -> dict:
        t = timeout or self._timeout
        if self._transport == "ssh":
            return await _run_powershell_ssh(
                self._host, self._port, self._username,
                self._password, script, t,
            )
        return await _run_powershell_winrm(
            self._host, self._port, self._username,
            self._password, script, t,
        )

    async def test_connection(self) -> dict:
        result = await self._exec(
            "Get-ComputerInfo | Select-Object CsName, WindowsVersion | ConvertTo-Json -Compress"
        )
        if not result["success"]:
            return {"connected": False, "error": result["stderr"], "latency_ms": 0}
        data = _parse_json_output(result["stdout"])
        if data is None:
            return {"connected": False, "error": "Invalid response from host", "latency_ms": 0}
        return {
            "connected": True,
            "latency_ms": 0,
            "message": f"Connected to {data.get('CsName', 'unknown')}",
            "hostname": data.get("CsName", "unknown"),
            "version": data.get("WindowsVersion", "unknown"),
        }

    async def get_summary(self) -> dict:
        script = (
            "$vms = Get-VM; "
            "$running = ($vms | Where-Object {$_.State -eq 'Running'}).Count; "
            "$stopped = ($vms | Where-Object {$_.State -eq 'Off'}).Count; "
            "$paused = ($vms | Where-Object {$_.State -eq 'Paused'}).Count; "
            "$saved = ($vms | Where-Object {$_.State -eq 'Saved'}).Count; "
            "$totalMem = ($vms | Measure-Object -Property MemoryAssigned -Sum).Sum / 1GB; "
            "$totalCpu = ($vms | Measure-Object -Property ProcessorCount -Sum).Sum; "
            "Write-Output (@{total_vms=$vms.Count;running=$running;stopped=$stopped;paused=$paused;saved=$saved;total_cpu=$totalCpu;total_memory_gb=[math]::Round($totalMem,1)} | ConvertTo-Json -Compress)"
        )
        result = await self._exec(script)
        if not result["success"]:
            return {"connected": False, "error": result["stderr"], "total_vms": 0, "running": 0, "stopped": 0, "paused": 0, "total_cpu": 0, "total_memory_gb": 0, "used_memory_gb": 0, "total_storage_gb": 0, "used_storage_gb": 0}
        data = _parse_json_output(result["stdout"])
        if data is None:
            return {"connected": False, "error": "Invalid response", "total_vms": 0, "running": 0, "stopped": 0, "paused": 0, "total_cpu": 0, "total_memory_gb": 0, "used_memory_gb": 0, "total_storage_gb": 0, "used_storage_gb": 0}
        return {
            "connected": True,
            "hostname": self._host,
            "total_vms": data.get("total_vms", 0),
            "running": data.get("running", 0),
            "stopped": data.get("stopped", 0),
            "paused": data.get("paused", 0),
            "saved": data.get("saved", 0),
            "total_cpu": data.get("total_cpu", 0),
            "total_memory_gb": data.get("total_memory_gb", 0),
            "used_memory_gb": 0,
            "total_storage_gb": 0,
            "used_storage_gb": 0,
        }

    async def get_vms(self) -> dict:
        script = (
            "Get-VM | ForEach-Object { "
            "[PSCustomObject]@{"
            "Id=$_.Id; Name=$_.Name; State=$_.State.ToString(); "
            "ProcessorCount=$_.ProcessorCount; MemoryAssigned=$_.MemoryAssigned; "
            "MemoryStartup=$_.MemoryStartup; MemoryDemand=$_.MemoryDemand; "
            "Uptime=$_.Uptime; ComputerName=$_.ComputerName; "
            "Generation=$_.Generation; CreationTime=$_.CreationTime; "
            "Notes=$_.Notes} } | ConvertTo-Json -Compress"
        )
        result = await self._exec(script)
        if not result["success"]:
            return {"connected": False, "error": result["stderr"], "count": 0, "items": []}
        data = _parse_json_output(result["stdout"])
        if data is None:
            return {"connected": True, "count": 0, "items": []}
        if isinstance(data, dict):
            data = [data]
        items = [
            {
                "id": v.get("Id", ""),
                "name": v.get("Name", ""),
                "state": v.get("State", "Unknown").lower(),
                "cpu_count": v.get("ProcessorCount", 0),
                "memory_assigned_mb": round(v.get("MemoryAssigned", 0) / 1048576),
                "memory_startup_mb": round(v.get("MemoryStartup", 0) / 1048576),
                "memory_demand_mb": round(v.get("MemoryDemand", 0) / 1048576),
                "uptime_seconds": int(v.get("Uptime", {}).get("TotalSeconds", 0)) if isinstance(v.get("Uptime"), dict) else 0,
                "host_server": v.get("ComputerName", ""),
                "guest_os": "",
                "creation_time": v.get("CreationTime", ""),
                "last_checkpoint": None,
                "status_message": v.get("Notes", ""),
                "integration_services_enabled": True,
                "cpu_usage_percent": 0.0,
                "disk_read_mbps": 0.0,
                "disk_write_mbps": 0.0,
                "network_receive_mbps": 0.0,
                "network_send_mbps": 0.0,
            }
            for v in data
        ]
        return {"connected": True, "count": len(items), "items": items}

    async def get_vm_detail(self, vm_id: str) -> dict:
        result = await self._exec(f"Get-VM -Id '{vm_id}' | Select-Object * | ConvertTo-Json -Compress")
        if not result["success"]:
            return {"connected": False, "error": result["stderr"]}
        data = _parse_json_output(result["stdout"])
        if data is None:
            return {"connected": False, "error": "VM not found"}
        return {"connected": True, "item": data}

    async def start_vm(self, vm_id: str) -> dict:
        result = await self._exec(f"Start-VM -Id '{vm_id}' -PassThru | Select-Object Name,State | ConvertTo-Json")
        if not result["success"]:
            return {"success": False, "error": result["stderr"]}
        return {"success": True, "message": "VM started"}

    async def stop_vm(self, vm_id: str, force: bool = False) -> dict:
        flag = "-Force" if force else ""
        result = await self._exec(f"Stop-VM -Id '{vm_id}' {flag} -PassThru | Select-Object Name,State | ConvertTo-Json")
        if not result["success"]:
            return {"success": False, "error": result["stderr"]}
        return {"success": True, "message": "VM stopped"}

    async def restart_vm(self, vm_id: str) -> dict:
        result = await self._exec(f"Restart-VM -Id '{vm_id}' -PassThru | Select-Object Name,State | ConvertTo-Json")
        if not result["success"]:
            return {"success": False, "error": result["stderr"]}
        return {"success": True, "message": "VM restarted"}

    async def pause_vm(self, vm_id: str) -> dict:
        result = await self._exec(f"Suspend-VM -Id '{vm_id}' -PassThru | Select-Object Name,State | ConvertTo-Json")
        if not result["success"]:
            return {"success": False, "error": result["stderr"]}
        return {"success": True, "message": "VM paused"}

    async def resume_vm(self, vm_id: str) -> dict:
        result = await self._exec(f"Resume-VM -Id '{vm_id}' -PassThru | Select-Object Name,State | ConvertTo-Json")
        if not result["success"]:
            return {"success": False, "error": result["stderr"]}
        return {"success": True, "message": "VM resumed"}

    async def get_networks(self) -> dict:
        script = (
            "Get-VMSwitch | ForEach-Object { "
            "[PSCustomObject]@{"
            "Id=$_.Id; Name=$_.Name; SwitchType=$_.SwitchType.ToString(); "
            "AllowManagementOS=$_.AllowManagementOS; "
            "Notes=$_.Notes} } | ConvertTo-Json -Compress"
        )
        result = await self._exec(script)
        if not result["success"]:
            return {"connected": False, "error": result["stderr"], "count": 0, "items": []}
        data = _parse_json_output(result["stdout"])
        if data is None:
            return {"connected": True, "count": 0, "items": []}
        if isinstance(data, dict):
            data = [data]
        items = [
            {
                "id": n.get("Id", ""),
                "name": n.get("Name", ""),
                "switch_type": str(n.get("SwitchType", "")).lower(),
                "allow_management_os": n.get("AllowManagementOS", False),
                "status": "operational",
            }
            for n in data
        ]
        return {"connected": True, "count": len(items), "items": items}

    async def get_storage(self) -> dict:
        script = (
            "Get-VHD | ForEach-Object { "
            "[PSCustomObject]@{"
            "VhdType=$_.VhdType.ToString(); Path=$_.Path; "
            "FileSize=$_.FileSize; Size=$_.Size; "
            "ComputerName=$_.ComputerName} } | ConvertTo-Json -Compress"
        )
        result = await self._exec(script)
        if not result["success"]:
            return {"connected": False, "error": result["stderr"], "count": 0, "items": []}
        data = _parse_json_output(result["stdout"])
        if data is None:
            return {"connected": True, "count": 0, "items": []}
        if isinstance(data, dict):
            data = [data]
        items = [
            {
                "id": f"disk-{i}",
                "name": s.get("Path", "").split("\\")[-1] if s.get("Path") else "",
                "path": s.get("Path", ""),
                "size_bytes": s.get("Size", 0),
                "used_bytes": s.get("FileSize", 0),
                "type": "vhdx",
                "attached": True,
            }
            for i, s in enumerate(data)
        ]
        return {"connected": True, "count": len(items), "items": items}

    async def get_snapshots(self, vm_id: str | None = None) -> dict:
        return await self.get_checkpoints(vm_id)

    async def get_checkpoints(self, vm_id: str | None = None) -> dict:
        vm_flag = f"-VMId '{vm_id}'" if vm_id else ""
        script = (
            f"Get-VMCheckpoint {vm_flag} | ForEach-Object {{ "
            f"[PSCustomObject]@{{"
            f"Id=$_.Id; Name=$_.Name; CheckpointType=$_.CheckpointType.ToString(); "
            f"CreationTime=$_.CreationTime; ParentCheckpointId=$_.ParentCheckpointId; "
            f"Notes=$_.Notes}} }} | ConvertTo-Json -Compress"
        )
        result = await self._exec(script)
        if not result["success"]:
            return {"connected": False, "error": result["stderr"], "count": 0, "items": []}
        data = _parse_json_output(result["stdout"])
        if data is None:
            return {"connected": True, "count": 0, "items": []}
        if isinstance(data, dict):
            data = [data]
        return {"connected": True, "count": len(data), "items": data}

    async def create_snapshot(self, vm_id: str, name: str | None = None) -> dict:
        return await self.create_checkpoint(vm_id, name)

    async def create_checkpoint(self, vm_id: str, name: str | None = None) -> dict:
        name_flag = f"-Name '{name}'" if name else ""
        result = await self._exec(
            f"Checkpoint-VM -Id '{vm_id}' {name_flag} -PassThru | ConvertTo-Json"
        )
        if not result["success"]:
            return {"success": False, "error": result["stderr"]}
        return {"success": True, "message": "Checkpoint created"}

    async def delete_snapshot(self, vm_id: str, snapshot_id: str) -> dict:
        return await self.delete_checkpoint(vm_id, snapshot_id)

    async def delete_checkpoint(self, vm_id: str, checkpoint_id: str) -> dict:
        result = await self._exec(
            f"Remove-VMCheckpoint -Id '{checkpoint_id}' -Confirm:$false"
        )
        if not result["success"]:
            return {"success": False, "error": result["stderr"]}
        return {"success": True, "message": "Checkpoint deleted"}

    async def get_health(self) -> dict:
        script = (
            "$cpu = (Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average).Average; "
            "$os = Get-CimInstance Win32_OperatingSystem; "
            "$memTotal = [math]::Round($os.TotalVisibleMemorySize / 1MB, 1); "
            "$memFree = [math]::Round($os.FreePhysicalMemory / 1MB, 1); "
            "$memUsed = [math]::Round($memTotal - $memFree, 1); "
            "$memPct = if ($memTotal -gt 0) { [math]::Round(($memUsed / $memTotal) * 100) } else { 0 }; "
            "$uptime = (Get-Date) - $os.LastBootUpTime; "
            "$vmCount = (Get-VM).Count; "
            "$cs = Get-ComputerInfo -ErrorAction SilentlyContinue; "
            "@{"
            "Name=$env:COMPUTERNAME; "
            "State='Up'; "
            "CpuPercent=[int]$cpu; "
            "MemoryPercent=[int]$memPct; "
            "MemoryUsedGB=$memUsed; "
            "MemoryTotalGB=$memTotal; "
            "UptimeSeconds=[int]$uptime.TotalSeconds; "
            "VMCount=$vmCount; "
            "Version=$cs.WindowsVersion; "
            "} | ConvertTo-Json -Compress"
        )
        result = await self._exec(script)
        if not result["success"]:
            return {"connected": False, "error": result["stderr"], "status": "unavailable"}
        data = _parse_json_output(result["stdout"])
        if data is None:
            return {"connected": False, "error": "Invalid response", "status": "unavailable"}
        if not isinstance(data, list):
            data = [data]
        mapped = [
            {
                "name": h.get("Name", "unknown"),
                "status": "healthy" if h.get("State", "").lower() in ("up", "online") else "warning",
                "cpu_percent": float(h.get("CpuPercent", 0)),
                "memory_percent": float(h.get("MemoryPercent", 0)),
                "memory_used_gb": float(h.get("MemoryUsedGB", 0)),
                "memory_total_gb": float(h.get("MemoryTotalGB", 0)),
                "uptime_seconds": int(h.get("UptimeSeconds", 0)),
                "vm_count": int(h.get("VMCount", 0)),
                "version": h.get("Version"),
            }
            for h in data
        ]
        return {
            "connected": True,
            "status": "healthy",
            "hosts": mapped,
            "cluster_summary": "Single host mode" if len(mapped) <= 1 else f"Cluster with {len(mapped)} nodes",
        }

    async def get_replication(self) -> dict:
        """Get Hyper-V VM replication status from all VMs."""
        script = (
            "$repl = Get-VMReplication -ErrorAction SilentlyContinue; "
            "if (-not $repl) { "
            "  Write-Output (@{connected=$true;replicating=0;total=0;items=@()} | ConvertTo-Json -Compress); "
            "  return "
            "} "
            "$items = $repl | ForEach-Object { "
            "  $health = 'Unknown'; "
            "  try { $health = $_.ReplicationHealth.ToString() } catch {} "
            "  $state = 'Unknown'; "
            "  try { $state = $_.State.ToString() } catch {} "
            "  $freq = 0; "
            "  try { $freq = $_.ReplicationFrequencySec } catch {} "
            "  $lastTime = ''; "
            "  try { $lastTime = $_.LastReplicationTime.ToString('yyyy-MM-dd HH:mm:ss') } catch {} "
            "  $resultCode = 0; "
            "  try { $resultCode = $_.LastReplicationResultCode } catch {} "
            "  $bytesSent = 0; "
            "  try { $bytesSent = $_.ReplicationBytesSent } catch {} "
            "  $bytesReceived = 0; "
            "  try { $bytesReceived = $_.ReplicationBytesReceived } catch {} "
            "  [PSCustomObject]@{ "
            "    VMName=$_.VMName; "
            "    ReplicaServer=$_.ReplicaServer; "
            "    ReplicaServerPort=$_.ReplicaServerPort; "
            "    State=$state; "
            "    Health=$health; "
            "    ReplicationFrequencySec=$freq; "
            "    LastReplicationTime=$lastTime; "
            "    LastReplicationResultCode=$resultCode; "
            "    ReplicationBytesSent=$bytesSent; "
            "    ReplicationBytesReceived=$bytesReceived; "
            "  } "
            "} "
            "$replicating = ($repl | Where-Object { $_.State -eq 'Replicating' }).Count; "
            "Write-Output (@{connected=$true;replicating=$replicating;total=$repl.Count;items=$items} | ConvertTo-Json -Compress)"
        )
        result = await self._exec(script)
        if not result["success"]:
            return {"connected": False, "error": result["stderr"], "replicating": 0, "total": 0, "items": []}
        data = _parse_json_output(result["stdout"])
        if data is None:
            return {"connected": True, "replicating": 0, "total": 0, "items": []}
        items = []
        for r in data.get("items", []):
            if isinstance(r, dict):
                health = r.get("Health", "Unknown")
                items.append({
                    "vm_name": r.get("VMName", ""),
                    "replica_server": r.get("ReplicaServer", ""),
                    "replica_port": r.get("ReplicaServerPort", 443),
                    "state": r.get("State", "Unknown"),
                    "health": health,
                    "frequency_seconds": r.get("ReplicationFrequencySec", 0),
                    "last_replication_time": r.get("LastReplicationTime", ""),
                    "last_result_code": r.get("LastReplicationResultCode", 0),
                    "bytes_sent": r.get("ReplicationBytesSent", 0),
                    "bytes_received": r.get("ReplicationBytesReceived", 0),
                })
        return {
            "connected": True,
            "replicating": data.get("replicating", 0),
            "total": data.get("total", 0),
            "items": items,
        }
