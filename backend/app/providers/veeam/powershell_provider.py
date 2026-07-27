"""
Mission Control Veeam Community Edition Provider

Connects to Veeam B&R Community Edition servers via PowerShell Remoting
over WinRM or SSH. Community Edition does not expose the REST API, so
all data is retrieved by executing Veeam PowerShell cmdlets remotely.

Configuration is injected from IntegrationProfile — never reads config.py.
"""

import asyncio
import base64
import json
import logging

from app.providers.veeam.base_provider import VeeamProvider

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
# Remote execution helpers (SSH / WinRM)                              #
# ------------------------------------------------------------------ #


async def _run_powershell_winrm(
    host: str,
    port: int,
    username: str,
    password: str,
    script: str,
    timeout: int = 30,
) -> dict:
    """Execute a PowerShell script on a remote host via WinRM."""
    import winrm

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
    except TimeoutError:
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
    import paramiko

    def _exec() -> dict:
        client = paramiko.SSHClient()
        from app.core.config import get_settings

        if get_settings().ssh_auto_add_host_keys:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        else:
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.RejectPolicy())
        try:
            client.connect(
                hostname=host,
                port=port,
                username=username,
                password=password,
                timeout=15,
            )
            encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
            ps_exe = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
            remote_cmd = f"{ps_exe} -NoProfile -NonInteractive -EncodedCommand {encoded}"
            _, stdout, stderr = client.exec_command(remote_cmd, timeout=timeout)
            out = stdout.read().decode("utf-8", errors="replace")
            err = stderr.read().decode("utf-8", errors="replace")
            exit_code = stdout.channel.recv_exit_status()
            return {
                "success": exit_code == 0,
                "stdout": out,
                "stderr": err,
                "exit_code": exit_code,
            }
        finally:
            client.close()

    try:
        loop = asyncio.get_event_loop()
        return await asyncio.wait_for(
            loop.run_in_executor(None, _exec),
            timeout=timeout + 10,
        )
    except TimeoutError:
        return {"success": False, "stdout": "", "stderr": "Command timed out", "exit_code": -1}
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e), "exit_code": -1}


def _parse_json_output(stdout: str) -> dict | list | None:
    """Extract JSON from PowerShell output (handles multiple objects)."""
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


def _parse_json_array(stdout: str) -> list[dict]:
    """Parse PowerShell JSON array output, handling multiple objects."""
    text = stdout.strip()
    if not text:
        return []

    # Try as a single JSON array first
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return [data]
    except json.JSONDecodeError:
        pass

    # PowerShell sometimes outputs one JSON object per line
    results = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("(") or line.startswith("WARNING"):
            continue
        if line.startswith("{") or line.startswith("["):
            try:
                obj = json.loads(line)
                if isinstance(obj, list):
                    results.extend(obj)
                else:
                    results.append(obj)
            except json.JSONDecodeError:
                continue
    return results


def _get_result_map() -> dict:
    return {
        "Success": "Success",
        "Warning": "Warning",
        "Failed": "Failed",
    }


# ------------------------------------------------------------------ #
# Veeam PowerShell Provider                                           #
# ------------------------------------------------------------------ #


class VeeamPowerShellProvider(VeeamProvider):
    """Veeam B&R Community Edition provider using PowerShell remoting.

    Executes Veeam PowerShell cmdlets (Snapin: VeeamPSSnapIn) remotely
    via WinRM or SSH. Used when Community Edition is detected (no REST API).
    """

    def __init__(
        self,
        host: str,
        port: int = 5985,
        username: str = "",
        password: str = "",
        timeout: int = 60,
        transport: str = "winrm",
        ssh_port: int = 22,
        db_type: str = "postgresql",
        column_case: str = "pascal",
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._timeout = timeout
        self._transport = transport
        self._ssh_port = ssh_port
        self.db_type = db_type
        self.column_case = column_case

    async def _exec(self, script: str, timeout: int | None = None) -> dict:
        t = timeout or self._timeout
        if self._transport == "ssh":
            return await _run_powershell_ssh(
                self._host, self._ssh_port, self._username,
                self._password, script, t,
            )
        return await _run_powershell_winrm(
            self._host, self._port, self._username,
            self._password, script, t,
        )

    def _ps_prefix(self) -> str:
        """Veeam PowerShell module import prefix."""
        return "Import-Module Veeam.Backup.PowerShell -ErrorAction SilentlyContinue; "

    async def test_connection(self) -> dict:
        script = (
            self._ps_prefix() +
            "$srv = Get-VBRServer; "
            "if ($srv) { "
            "  @{connected=$true; name=$srv.Name; version=$srv.Info; type='Community Edition'} | ConvertTo-Json -Compress "
            "} else { "
            "  @{connected=$false; error='Veeam server not found'} | ConvertTo-Json -Compress "
            "}"
        )
        result = await self._exec(script)
        if result["success"]:
            data = _parse_json_output(result["stdout"])
            if data and data.get("connected"):
                return {
                    "connected": True,
                    "latency_ms": 0,
                    "version": data.get("version", ""),
                    "name": data.get("name", ""),
                    "error": None,
                }

        # PS module not available — fall back to SSH+DB bridge test
        if self._has_ssh():
            from app.providers.veeam.db_bridge import run_db_query
            if self.db_type == "mssql":
                test_sql = "SELECT TOP 1 name FROM sys.databases WHERE name = 'VeeamBackup'"
            else:
                test_sql = "SELECT 1"
            try:
                db_result = await run_db_query(
                    sql=test_sql,
                    ssh_host=self._host,
                    ssh_port=self._ssh_port,
                    ssh_username=self._username,
                    ssh_password=self._password,
                    db_type=self.db_type,
                )
                if db_result.get("success") and db_result.get("output", "").strip():
                    return {
                        "connected": True,
                        "latency_ms": 0,
                        "version": f"Veeam DB ({self.db_type})",
                        "name": self._host,
                        "error": None,
                    }
                return {
                    "connected": False,
                    "latency_ms": 0,
                    "error": db_result.get("error") or db_result.get("stderr") or "Database query failed",
                    "name": "",
                }
            except Exception as exc:
                return {"connected": False, "error": str(exc), "latency_ms": 0}

        return {
            "connected": data.get("connected", False) if data else False,
            "latency_ms": 0,
            "version": data.get("version", "") if data else "",
            "name": data.get("name", "") if data else "",
            "error": data.get("error") if data else "No SSH bridge configured",
        }

    async def get_summary(self) -> dict:
        script = (
            self._ps_prefix() +            "$jobs = Get-VBRJob; "
            "$sessions = Get-VBRSession -Last 100; "
            "$repos = Get-VBRRepository; "
            "$servers = Get-VBRServer; "
            "$running = ($jobs | Where-Object {$_.IsRunning}).Count; "
            "$success = ($sessions | Where-Object {$_.Result -eq 'Success'}).Count; "
            "$warning = ($sessions | Where-Object {$_.Result -eq 'Warning'}).Count; "
            "$failed = ($sessions | Where-Object {$_.Result -eq 'Failed'}).Count; "
            "$totalSpace = ($repos | Measure-Object -Property QuotaBytes -Sum).Sum; "
            "$usedSpace = ($repos | Measure-Object -Property UsedSpace -Sum).Sum; "
            "if (-not $totalSpace) { $totalSpace = 0 }; "
            "if (-not $usedSpace) { $usedSpace = 0 }; "
            "@{"
            "  version=(Get-VBRLicense | Select-Object -First 1).Edition; "
            "  name=($servers | Select-Object -First 1).Name; "
            "  total_jobs=$jobs.Count; "
            "  running_jobs=$running; "
            "  total_repositories=$repos.Count; "
            "  total_space_bytes=$totalSpace; "
            "  used_space_bytes=$usedSpace; "
            "  recent_sessions=$sessions.Count; "
            "  sessions_success=$success; "
            "  sessions_warning=$warning; "
            "  sessions_failed=$failed "
            "} | ConvertTo-Json -Compress"
        )
        result = await self._exec(script, timeout=60)
        if not result["success"]:
            return {"success": False, "error": result["stderr"]}
        data = _parse_json_output(result["stdout"])
        if data is None:
            return {"success": False, "error": "Invalid response"}
        return {
            "success": True,
            "version": data.get("version", "Community Edition"),
            "name": data.get("name", ""),
            "total_jobs": data.get("total_jobs", 0),
            "running_jobs": data.get("running_jobs", 0),
            "total_repositories": data.get("total_repositories", 0),
            "total_space_bytes": data.get("total_space_bytes", 0),
            "used_space_bytes": data.get("used_space_bytes", 0),
            "recent_sessions": data.get("recent_sessions", 0),
            "sessions_success": data.get("sessions_success", 0),
            "sessions_warning": data.get("sessions_warning", 0),
            "sessions_failed": data.get("sessions_failed", 0),
        }

    async def get_jobs(self) -> dict:
        script = (
            self._ps_prefix() +            "Get-VBRJob | ForEach-Object { "
            "  $j = $_; "
            "  $last = Get-VBRSession -Job $j -Last 1 | Select-Object -First 1; "
            "  $info = $j.Info; "
            "  @{"
            "    id=$j.Id.ToString(); "
            "    name=$j.Name; "
            "    type=$j.JobType.ToString(); "
            "    state=if ($j.IsRunning) {'Running'} else {'Stopped'}; "
            "    enabled=$j.Options.Enabled; "
            "    schedule=if ($j.ScheduleOptions -and $j.ScheduleOptions.Enabled) {@{kind='periodic'}} else {$null}; "
            "    lastRun=if ($last) @{"
            "      id=$last.Id.ToString(); "
            "      state=$last.State.ToString(); "
            "      result=@{result=$last.Result.ToString()}; "
            "      creationTime=$last.CreationTime.ToString('o'); "
            "      endTime=$last.EndTime.ToString('o'); "
            "      progressPercent=$last.Progress "
            "    } else {$null}; "
            "    includedObjects=@{objectsInJob=if ($info) {$info.LinkedObjects.Count} else {0}} "
            "  } | ConvertTo-Json -Compress "
            "}"
        )
        result = await self._exec(script, timeout=90)
        if not result["success"]:
            return {"success": False, "error": result["stderr"], "jobs": []}
        jobs = _parse_json_array(result["stdout"])
        normalized = []
        for j in jobs:
            normalized.append({
                "id": j.get("id", ""),
                "name": j.get("name", ""),
                "type": j.get("type", "Backup"),
                "state": j.get("state", "Unknown"),
                "enabled": j.get("enabled", True),
                "schedule": j.get("schedule"),
                "lastRun": j.get("lastRun"),
                "includedObjects": j.get("includedObjects"),
            })
        return {"success": True, "jobs": normalized, "count": len(normalized)}

    async def get_job_detail(self, job_id: str) -> dict:
        script = (
            self._ps_prefix() +            f"$job = Get-VBRJob -Id '{job_id}'; "
            "if ($job) { $job | Select-Object * | ConvertTo-Json -Depth 5 -Compress } "
            "else { @{error='Job not found'} | ConvertTo-Json -Compress }"
        )
        result = await self._exec(script)
        if not result["success"]:
            return {"success": False, "error": result["stderr"]}
        data = _parse_json_output(result["stdout"])
        if data is None:
            return {"success": False, "error": "Job not found"}
        return {"success": True, "job": data}

    async def get_sessions(self) -> dict:
        script = (
            self._ps_prefix() +            "Get-VBRSession -Last 200 | ForEach-Object { "
            "  $s = $_; "
            "  @{"
            "    id=$s.Id.ToString(); "
            "    jobId=$s.JobId.ToString(); "
            "    name=$s.Name; "
            "    sessionType=$s.JobType.ToString(); "
            "    state=$s.State.ToString(); "
            "    result=@{result=$s.Result.ToString()}; "
            "    creationTime=$s.CreationTime.ToString('o'); "
            "    endTime=$s.EndTime.ToString('o'); "
            "    progressPercent=$s.Progress "
            "  } | ConvertTo-Json -Compress "
            "}"
        )
        result = await self._exec(script, timeout=90)
        if not result["success"]:
            return {"success": False, "error": result["stderr"], "sessions": []}
        sessions = _parse_json_array(result["stdout"])
        return {"success": True, "sessions": sessions, "count": len(sessions)}

    async def get_repositories(self) -> dict:
        script = (
            self._ps_prefix() +            "Get-VBRRepository | ForEach-Object { "
            "  $r = $_; "
            "  @{"
            "    id=$r.Id.ToString(); "
            "    name=$r.Name; "
            "    type=$r.Type.ToString(); "
            "    description=$r.Description; "
            "    repository=@{"
            "      path=$r.Path; "
            "      capacityBytes=$r.QuotaBytes; "
            "      usedSpaceBytes=$r.UsedSpace; "
            "      freeSpaceBytes=if ($r.QuotaBytes -gt 0) {$r.QuotaBytes - $r.UsedSpace} else {0} "
            "    }; "
            "    hostId=$r.HostId.ToString() "
            "  } | ConvertTo-Json -Compress "
            "}"
        )
        result = await self._exec(script, timeout=60)
        if not result["success"]:
            return {"success": False, "error": result["stderr"], "repositories": []}
        repos = _parse_json_array(result["stdout"])
        return {"success": True, "repositories": repos, "count": len(repos)}

    async def get_managed_servers(self) -> dict:
        script = (
            self._ps_prefix() +            "Get-VBRServer | ForEach-Object { "
            "  $s = $_; "
            "  $desc = ''; "
            "  try { $desc = [string]$s.Info } catch { $desc = '' }; "
            "  @{"
            "    id=$s.Id.ToString(); "
            "    name=$s.Name; "
            "    type=$s.Type.ToString(); "
            "    description=$desc; "
            "    status='Available' "
            "  } | ConvertTo-Json -Compress "
            "}"
        )
        result = await self._exec(script, timeout=60)
        if not result["success"]:
            return {"success": False, "error": result["stderr"], "servers": []}
        servers = _parse_json_array(result["stdout"])
        normalized = []
        for s in servers:
            desc = s.get("description", "")
            if not isinstance(desc, str):
                desc = str(desc) if desc else ""
            normalized.append({
                "id": s.get("id", ""),
                "name": s.get("name", ""),
                "type": s.get("type", ""),
                "description": desc,
                "status": s.get("status", "Available"),
            })
        return {"success": True, "servers": normalized, "count": len(normalized)}

    async def get_restore_points(self, vm_id: str | None = None) -> dict:
        script = (
            self._ps_prefix() +            "Get-VBRRestorePoint | ForEach-Object { "
            "  $rp = $_; "
            "  @{"
            "    id=$rp.Id.ToString(); "
            "    vmId=$rp.VmId.ToString(); "
            "    name=$rp.Name; "
            "    creationTime=$rp.CreationTime.ToString('o'); "
            "    type=$rp.Type.ToString(); "
            "    backupId=$rp.BackupId.ToString() "
            "  } | ConvertTo-Json -Compress "
            "}"
        )
        result = await self._exec(script, timeout=60)
        if not result["success"]:
            return {"success": False, "error": result["stderr"], "restore_points": []}
        points = _parse_json_array(result["stdout"])
        if vm_id:
            points = [p for p in points if p.get("vmId", "") == vm_id]
        return {"success": True, "restore_points": points, "count": len(points)}

    async def get_license(self) -> dict:
        script = (
            self._ps_prefix() +            "$lic = Get-VBRLicense | Select-Object -First 1; "
            "if ($lic) { "
            "  @{"
            "    edition=$lic.Edition; "
            "    type=$lic.Type.ToString(); "
            "    expirationDate=$lic.ExpirationDate.ToString('o'); "
            "    licenseId=$lic.LicenseId.ToString(); "
            "    editionType=$lic.EditionType.ToString() "
            "  } | ConvertTo-Json -Compress "
            "} else { @{error='No license found'} | ConvertTo-Json -Compress }"
        )
        result = await self._exec(script)
        if not result["success"]:
            return {"success": False, "error": result["stderr"]}
        data = _parse_json_output(result["stdout"])
        if data is None:
            return {"success": False, "error": "Invalid license response"}
        return {"success": True, "license": data}

    async def get_capacity_tier(self) -> dict:
        script = (
            self._ps_prefix() +            "Get-VBRCapacityTierExtent | ForEach-Object { "
            "  $e = $_; "
            "  @{"
            "    id=$e.Id.ToString(); "
            "    name=$e.Name; "
            "    type=$e.Type.ToString(); "
            "    repositoryName=$e.Repository.Name "
            "  } | ConvertTo-Json -Compress "
            "}"
        )
        result = await self._exec(script, timeout=60)
        if not result["success"]:
            return {"success": True, "object_storages": [], "count": 0}
        items = _parse_json_array(result["stdout"])
        return {"success": True, "object_storages": items, "count": len(items)}

    async def start_job(self, job_id: str) -> dict:
        script = (
            self._ps_prefix() +            f"Start-VBRJob -Id '{job_id}' | Select-Object Name | ConvertTo-Json"
        )
        result = await self._exec(script)
        if not result["success"]:
            return {"success": False, "error": result["stderr"]}
        return {"success": True, "message": "Job started"}

    async def stop_job(self, job_id: str) -> dict:
        script = (
            self._ps_prefix() +            f"Stop-VBRJob -Id '{job_id}' -Force | Select-Object Name | ConvertTo-Json"
        )
        result = await self._exec(script)
        if not result["success"]:
            return {"success": False, "error": result["stderr"]}
        return {"success": True, "message": "Job stopped"}

    async def get_health(self) -> dict:
        script = (
            self._ps_prefix() +            "$srv = Get-VBRServer | Select-Object -First 1; "
            "@{"
            "  healthy=($srv -ne $null); "
            "  version=if ($srv) {$srv.Info} else {'unknown'}; "
            "  name=if ($srv) {$srv.Name} else {'unknown'} "
            "} | ConvertTo-Json -Compress"
        )
        result = await self._exec(script)
        if not result["success"]:
            return {"healthy": False, "error": result["stderr"]}
        data = _parse_json_output(result["stdout"])
        if data is None:
            return {"healthy": False, "error": "Invalid health response"}
        return {
            "healthy": data.get("healthy", False),
            "version": data.get("version", ""),
            "name": data.get("name", ""),
        }

    async def get_session_stats(self) -> dict:
        """Get session transfer statistics.

        Community Edition does not expose backupjobsessions table via REST,
        but the Veeam PowerShell cmdlets do expose some transfer data.
        """
        if not self._has_ssh():
            return {
                "success": True,
                "stats": [],
                "ssh_available": False,
                "message": "SSH bridge not configured",
            }
        return await self._get_session_stats_via_ssh()

    async def _get_session_stats_via_ssh(self) -> dict:
        from app.providers.veeam.sql_queries import session_stats_sql
        sql = session_stats_sql(db_type=self.db_type, column_case=self.column_case)
        result = await self._run_pg_query(sql)
        if not result.get("success"):
            return {
                "success": False,
                "stats": [],
                "ssh_available": False,
                "error": result.get("stderr") or result.get("error", "PostgreSQL query failed"),
            }
        stats = []
        output = result.get("output", "").strip()
        for line in output.split("\n"):
            line = line.strip()
            if not line or line.startswith("(") or line.startswith("WARNING"):
                continue
            parts = line.split("|")
            if len(parts) >= 11:
                stats.append({
                    "session_id": parts[0].strip(),
                    "job_id": parts[1].strip(),
                    "job_name": parts[2].strip(),
                    "state": parts[3].strip(),
                    "creation_time": parts[4].strip(),
                    "end_time": parts[5].strip(),
                    "result": parts[6].strip(),
                    "processed_bytes": int(parts[8].strip() or 0),
                    "read_bytes": int(parts[9].strip() or 0),
                    "transferred_bytes": int(parts[10].strip() or 0),
                })
        return {
            "success": True,
            "stats": stats,
            "ssh_available": True,
            "count": len(stats),
        }

    async def get_job_stats(self) -> dict:
        from app.providers.veeam.sql_queries import job_stats_sql
        if not self._has_ssh():
            return {
                "success": True,
                "jobs": [],
                "ssh_available": False,
                "message": "SSH bridge not configured",
            }
        sql = job_stats_sql(db_type=self.db_type, column_case=self.column_case)
        result = await self._run_pg_query(sql)
        if not result.get("success"):
            return {
                "success": False,
                "jobs": [],
                "ssh_available": False,
                "error": result.get("stderr") or result.get("error", "PostgreSQL query failed"),
            }
        jobs = []
        output = result.get("output", "").strip()
        for line in output.split("\n"):
            line = line.strip()
            if not line or line.startswith("(") or line.startswith("WARNING"):
                continue
            parts = line.split("|")
            if len(parts) >= 11:
                jobs.append({
                    "job_name": parts[0].strip(),
                    "session_count": int(parts[1].strip() or 0),
                    "total_bytes": int(parts[2].strip() or 0),
                    "processed_bytes": int(parts[3].strip() or 0),
                    "read_bytes": int(parts[4].strip() or 0),
                    "stored_bytes": int(parts[5].strip() or 0),
                    "avg_speed": int(float(parts[6].strip() or 0)),
                    "last_run": parts[7].strip(),
                    "success_count": int(parts[8].strip() or 0),
                    "warning_count": int(parts[9].strip() or 0),
                    "failed_count": int(parts[10].strip() or 0),
                })
        return {
            "success": True,
            "jobs": jobs,
            "ssh_available": True,
            "count": len(jobs),
        }

    async def get_job_stats_daily(self, days: int = 7) -> dict:
        from app.providers.veeam.sql_queries import job_stats_daily_sql
        if not self._has_ssh():
            return {
                "success": True,
                "jobs": [],
                "dates": [],
                "ssh_available": False,
                "message": "SSH bridge not configured",
            }
        sql = job_stats_daily_sql(days=days, db_type=self.db_type, column_case=self.column_case)
        result = await self._run_pg_query(sql)
        if not result.get("success"):
            return {
                "success": False,
                "jobs": [],
                "dates": [],
                "ssh_available": False,
                "error": result.get("stderr") or result.get("error", "PostgreSQL query failed"),
            }
        job_map: dict[str, dict[str, dict]] = {}
        dates_set: set[str] = set()
        output = result.get("output", "").strip()
        for line in output.split("\n"):
            line = line.strip()
            if not line or line.startswith("(") or line.startswith("WARNING"):
                continue
            parts = line.split("|")
            if len(parts) >= 9:
                job_name = parts[0].strip()
                run_date = parts[1].strip()
                processed = int(parts[2].strip() or 0)
                read_bytes = int(parts[3].strip() or 0)
                stored = int(parts[4].strip() or 0)
                session_count = int(parts[5].strip() or 0)
                success = int(parts[6].strip() or 0)
                warning = int(parts[7].strip() or 0)
                failed = int(parts[8].strip() or 0)
                if failed > 0:
                    result_status = "Failed"
                elif warning > 0:
                    result_status = "Warning"
                else:
                    result_status = "Success"
                dates_set.add(run_date)
                if job_name not in job_map:
                    job_map[job_name] = {}
                job_map[job_name][run_date] = {
                    "processed_bytes": processed,
                    "read_bytes": read_bytes,
                    "stored_bytes": stored,
                    "session_count": session_count,
                    "success_count": success,
                    "warning_count": warning,
                    "failed_count": failed,
                    "result": result_status,
                }
        jobs = []
        for job_name, daily in job_map.items():
            jobs.append({"job_name": job_name, "daily": daily})
        dates = sorted(dates_set, reverse=True)
        return {
            "success": True,
            "jobs": jobs,
            "dates": dates,
            "ssh_available": True,
            "count": len(jobs),
        }

    # ------------------------------------------------------------------ #
    # SSH + PostgreSQL Bridge (for transfer statistics)                   #
    # ------------------------------------------------------------------ #

    def _has_ssh(self) -> bool:
        return self._transport == "ssh" and bool(self._host and self._username)

    async def _run_pg_query(self, sql: str) -> dict:
        from app.providers.veeam.db_bridge import run_db_query
        if not self._has_ssh():
            return {"success": False, "error": "SSH bridge not configured", "output": ""}
        return await run_db_query(
            sql=sql,
            ssh_host=self._host,
            ssh_port=self._ssh_port,
            ssh_username=self._username,
            ssh_password=self._password,
            db_type=self.db_type,
        )
