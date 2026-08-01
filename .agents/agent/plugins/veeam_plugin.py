"""
Mission Control Agent - Veeam Backup & Replication plugin.

Cross-platform implementation:
- Windows: prefers remote Veeam REST API when configured, falls back to local PowerShell
- Linux: uses Veeam REST API over HTTPS
"""

import asyncio
import json
import logging
import os
import platform
from typing import Any

from agent.plugin import AgentPlugin

logger = logging.getLogger("mc-agent")

_VEEAM_API_BASE = os.environ.get("MC_VEEAM_API_BASE", "")
_VEEAM_USERNAME = os.environ.get("MC_VEEAM_USERNAME", "")
_VEEAM_PASSWORD = os.environ.get("MC_VEEAM_PASSWORD", "")


class VeeamPlugin(AgentPlugin):
    """Veeam B&R management plugin - cross-platform."""

    name = "veeam"
    version = "3.0.0-rc1"
    description = "Veeam Backup & Replication management plugin"
    platform_required = None  # cross-platform

    def __init__(self) -> None:
        self._context: dict[str, Any] = {}
        self._has_module: bool | None = None
        self._api_base = _VEEAM_API_BASE
        self._username = _VEEAM_USERNAME
        self._password = _VEEAM_PASSWORD
        self._use_rest = False
        self._ssh_target: dict[str, Any] | None = None

    async def initialize(self, context: dict[str, Any]) -> bool:
        self._context = context
        self._use_rest = False
        self._has_module = None
        self._api_base = _VEEAM_API_BASE
        self._username = _VEEAM_USERNAME
        self._password = _VEEAM_PASSWORD
        self._ssh_target = None
        return True

    def reinitialize(self) -> None:
        """Allow agent to reload integration profiles from updated context."""
        self._configured_from_context = False

    async def _configure_from_context(self) -> None:
        """Load or reload integration profile settings."""
        profiles = (
            self._context.get("integration_profiles")
            or self._context.get("integration_profile")
            or []
        )
        if isinstance(profiles, dict):
            profiles = [profiles]

        veeam_profile = None
        for p in profiles:
            if not isinstance(p, dict):
                continue
            if (p.get("integration_type") or "").lower() == "veeam":
                veeam_profile = p
                break

        if veeam_profile:
            self._api_base = veeam_profile.get("base_url") or self._api_base
            self._username = veeam_profile.get("username") or self._username
            self._password = veeam_profile.get("password") or self._password
            ssh_host = veeam_profile.get("ssh_host")
            ssh_port = veeam_profile.get("ssh_port") or 22
            ssh_username = veeam_profile.get("ssh_username") or ""
            ssh_password = veeam_profile.get("password") or ""
            if ssh_host:
                self._api_base = f"https://{ssh_host}:9419"
                self._username = ssh_username or self._username
                self._password = ssh_password or self._password

        system = platform.system()

        if system == "Windows":
            if self._api_base and self._username and not self._ssh_target:
                self._use_rest = True
                logger.info("Veeam plugin initialized for Windows REST API (%s)", self._api_base)
                return
            self._has_module = await self._check_veeam()
            if not self._has_module:
                logger.warning("Veeam PowerShell module not available on this host")
                return
            logger.info("Veeam plugin initialized for Windows (%s)", platform.node())
            return

        if system == "Linux":
            if not self._api_base or not self._username:
                logger.warning(
                    "Veeam REST API not configured (set MC_VEEAM_API_BASE, MC_VEEAM_USERNAME)"
                )
                return
            self._use_rest = True
            logger.info("Veeam plugin initialized for Linux REST API (%s)", self._api_base)
            return

        logger.warning("Veeam plugin not supported on %s", system)

    async def collect_inventory(self) -> dict[str, Any]:
        """Collect Veeam inventory."""
        await self._ensure_configured()
        if self._use_rest:
            return await self._collect_inventory_rest()
        if platform.system() == "Windows":
            return await self._collect_inventory_windows()
        if platform.system() == "Linux":
            return await self._collect_inventory_linux()
        return {"error": f"Unsupported platform: {platform.system()}"}

    async def execute_command(self, command: str, args: dict[str, Any]) -> dict[str, Any]:
        """Execute Veeam commands."""
        await self._ensure_configured()
        if self._use_rest:
            return await self._execute_rest(command, args)
        if platform.system() == "Windows":
            return await self._execute_windows(command, args)
        if platform.system() == "Linux":
            return await self._execute_linux(command, args)
        return {"success": False, "error": f"Unsupported platform: {platform.system()}"}

    async def _ensure_configured(self) -> None:
        """Refresh integration-profile settings if they were updated after init."""
        if getattr(self, "_configured_from_context", False):
            return
        await self._configure_from_context()
        self._configured_from_context = True

    # ------------------------------------------------------------------
    # REST API helpers (used by both Linux and Windows remote paths)
    # ------------------------------------------------------------------

    async def _rest_get(self, path: str) -> Any:
        if not self._api_base:
            return None
        try:
            import httpx
        except ImportError:
            logger.warning("httpx not installed for Veeam REST calls")
            return None
        url = f"{self._api_base.rstrip('/')}{path}"
        try:
            async with httpx.AsyncClient(verify=False, timeout=30) as client:
                resp = await client.get(
                    url,
                    auth=(self._username, self._password or ""),
                )
            logger.info("Veeam REST %s -> %s", url, resp.status_code)
            if resp.status_code == 200:
                try:
                    parsed = resp.json()
                    if isinstance(parsed, dict):
                        logger.info("Veeam REST %s data keys=%s count=%s", url, sorted(parsed.keys()), len(parsed.get("data", parsed)) if isinstance(parsed.get("data"), list) else "n/a")
                    elif isinstance(parsed, list):
                        logger.info("Veeam REST %s items=%s", url, len(parsed))
                    return parsed
                except Exception:
                    logger.info("Veeam REST %s text=%s", url, resp.text[:200])
                    return resp.text
            logger.warning("Veeam REST %s body=%s", url, resp.text[:500])
            return None
        except Exception as exc:
            logger.warning("Veeam REST %s failed: %s", url, exc)
            return None

    async def _rest_post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self._api_base:
            return {"success": False, "error": "Veeam API base URL not configured"}
        try:
            import httpx
        except ImportError:
            return {"success": False, "error": "httpx not installed"}
        url = f"{self._api_base.rstrip('/')}{path}"
        try:
            async with httpx.AsyncClient(verify=False, timeout=30) as client:
                resp = await client.post(
                    url,
                    json=payload,
                    auth=(self._username, self._password or ""),
                )
            return {
                "success": resp.status_code in (200, 202),
                "stdout": resp.text,
                "stderr": "" if resp.status_code in (200, 202) else resp.text,
                "exit_code": resp.status_code,
            }
        except Exception as exc:
            return {"success": False, "error": str(exc), "stdout": "", "stderr": str(exc), "exit_code": -1}

    async def _collect_inventory_rest(self) -> dict[str, Any]:
        jobs = await self._rest_get("/api/v1/jobs") or []
        sessions = await self._rest_get("/api/v1/sessions") or []
        repos = await self._rest_get("/api/v1/repositories") or []
        managed_servers = await self._rest_get("/api/v1/servers") or []
        restore_points = []
        license = await self._rest_get("/api/v1/license") or {}
        return {
            "jobs": jobs,
            "sessions": sessions,
            "repositories": repos,
            "managed_servers": managed_servers,
            "restore_points": restore_points,
            "license": license,
        }

    async def _execute_rest(self, command: str, args: dict[str, Any]) -> dict[str, Any]:
        if command == "test_connection":
            try:
                import httpx
            except ImportError:
                return {"success": False, "error": "httpx not installed"}
            url = f"{self._api_base.rstrip('/')}/api/v1/license"
            try:
                async with httpx.AsyncClient(verify=False, timeout=10) as client:
                    resp = await client.get(
                        url,
                        auth=(self._username, self._password or ""),
                    )
                if resp.status_code == 200:
                    return {"success": True, "available": True, "message": "Veeam REST API reachable"}
                return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text}", "available": False}
            except Exception as exc:
                return {"success": False, "error": str(exc), "available": False}
        if command == "start_job":
            return await self._rest_post(f"/api/v1/jobs/{args.get('job_id','')}/start", {})
        if command == "stop_job":
            return await self._rest_post(f"/api/v1/jobs/{args.get('job_id','')}/stop", {})
        return {"success": False, "error": f"Unknown REST command: {command}"}

    # ------------------------------------------------------------------
    # Windows / PowerShell backend
    # ------------------------------------------------------------------

    async def _check_veeam(self) -> bool:
        try:
            scripts = [
                "if (Get-Command Get-VBRJob -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }",
                "if (Get-Command Get-VBRSession -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }",
            ]
            for script in scripts:
                proc = await asyncio.create_subprocess_exec(
                    "powershell",
                    "-Command",
                    script,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                try:
                    await asyncio.wait_for(proc.communicate(), timeout=10)
                except asyncio.TimeoutError:
                    return False
                if proc.returncode == 0:
                    return True
            return False
        except Exception:
            return False

    async def _run_script(self, script: str, timeout: int = 60) -> dict[str, Any]:
        try:
            proc = await asyncio.create_subprocess_exec(
                "powershell",
                "-Command",
                script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            stdout_text = stdout.decode("utf-8", errors="replace").strip() if stdout else ""
            stderr_text = stderr.decode("utf-8", errors="replace").strip() if stderr else ""
            data = None
            if stdout_text:
                try:
                    data = json.loads(stdout_text)
                except json.JSONDecodeError:
                    data = None
            return {
                "success": proc.returncode == 0,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "exit_code": proc.returncode,
                "data": data,
            }
        except asyncio.TimeoutError:
            return {"success": False, "stdout": "", "stderr": "timeout", "exit_code": -1, "data": None}
        except Exception as exc:
            return {"success": False, "stdout": "", "stderr": str(exc), "exit_code": -1, "data": None}

    async def _collect_inventory_windows(self) -> dict[str, Any]:
        """Collect Veeam inventory from local PowerShell."""
        if not self._has_module:
            return {"error": "Veeam module not available"}

        jobs = await self._run_collector("jobs")
        sessions = await self._run_collector("sessions")
        repos = await self._run_collector("repositories")
        servers = await self._run_collector("managed_servers")
        restore_points = await self._run_collector("restore_points")
        license = await self._run_collector("license")

        return {
            "jobs": jobs,
            "sessions": sessions,
            "repositories": repos,
            "managed_servers": servers,
            "restore_points": restore_points,
            "license": license,
        }

    async def _execute_windows(self, command: str, args: dict[str, Any]) -> dict[str, Any]:
        """Execute Veeam commands on Windows."""
        handlers = {
            "test_connection": self._test_connection_windows,
            "start_job": self._start_job,
            "stop_job": self._stop_job,
        }
        handler = handlers.get(command)
        if handler:
            return await handler(args)
        return {"success": False, "error": f"Unknown command: {command}"}

    async def _test_connection_windows(self, args: dict[str, Any]) -> dict[str, Any]:
        """Test Veeam PowerShell module availability on Windows."""
        if not self._has_module:
            return {"success": False, "error": "Veeam PowerShell module not available on this host"}

        script = (
            "Import-Module Veeam.Backup.PowerShell -ErrorAction SilentlyContinue; "
            "$ver = (Get-Module Veeam.Backup.PowerShell).Version; "
            "$jobCount = (Get-VBRJob -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count); "
            "if ($ver) { "
            "  @{"
            "    available=$true; "
            "    moduleVersion=$ver.ToString(); "
            "    jobCount=[int]$jobCount; "
            "    edition='Enterprise' "
            "  } | ConvertTo-Json -Compress "
            "} else { @{available=$false; error='Module not loaded'} | ConvertTo-Json -Compress }"
        )
        result = await self._run_script(script, timeout=30)
        if not result["success"]:
            return {"success": False, "error": result["stderr"], "stdout": result["stdout"], "exit_code": result["exit_code"]}

        payload = result["data"]
        if isinstance(payload, list):
            payload = payload[0] if payload else {}
        if not isinstance(payload, dict):
            payload = {}
        return {
            "success": True,
            "available": payload.get("available", True),
            "message": "Veeam PowerShell module is available and responding",
            "data": payload,
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "exit_code": result["exit_code"],
        }

    async def _start_job(self, args: dict[str, Any]) -> dict[str, Any]:
        job_id = args.get("job_id", "")
        script = f"Start-VBRJob -Job {job_id}"
        return await self._run_script(script, timeout=120)

    async def _stop_job(self, args: dict[str, Any]) -> dict[str, Any]:
        job_id = args.get("job_id", "")
        script = f"Stop-VBRJob -Job {job_id}"
        return await self._run_script(script, timeout=120)

    # ------------------------------------------------------------------
    # Linux / REST backend
    # ------------------------------------------------------------------

    async def _collect_inventory_linux(self) -> dict[str, Any]:
        return await self._collect_inventory_rest()

    async def _execute_linux(self, command: str, args: dict[str, Any]) -> dict[str, Any]:
        return await self._execute_rest(command, args)

    # ------------------------------------------------------------------
    # Shared collectors
    # ------------------------------------------------------------------

    async def _run_collector(self, collector: str) -> Any:
        prefix = "Import-Module Veeam.Backup.PowerShell -ErrorAction SilentlyContinue; "

        if collector == "jobs":
            script = (
                prefix
                + "Get-VBRJob | ForEach-Object { "
                "  $j = $_; "
                "  $last = Get-VBRSession -Job $j -Last 1 | Select-Object -First 1; "
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
                "    includedObjects=@{objectsInJob=if ($j.Info) {$j.Info.LinkedObjects.Count} else {0}} "
                "  } | ConvertTo-Json -Compress "
                "}"
            )
            result = await self._run_script(script, timeout=90)
            if not result["success"]:
                return []
            return self._parse_json_array(result["stdout"])

        if collector == "sessions":
            script = (
                prefix
                + "Get-VBRSession -Last 200 | ForEach-Object { "
                "  @{"
                "    id=$_.Id.ToString(); "
                "    jobId=$_.JobId.ToString(); "
                "    name=$_.Name; "
                "    sessionType=$_.SessionType.ToString(); "
                "    state=$_.State.ToString(); "
                "    result=@{result=$_.Result.ToString()}; "
                "    creationTime=$_.CreationTime.ToString('o'); "
                "    endTime=$_.EndTime.ToString('o'); "
                "    progressPercent=$_.Progress "
                "  } | ConvertTo-Json -Compress "
                "}"
            )
            result = await self._run_script(script, timeout=120)
            if not result["success"]:
                return []
            return self._parse_json_array(result["stdout"])

        if collector == "repositories":
            script = (
                prefix
                + "Get-VBRBackupRepository | ForEach-Object { "
                "  @{"
                "    id=$_.Id.ToString(); "
                "    name=$_.Name; "
                "    type=$_.GetType().Name; "
                "    description=$_.Description; "
                "    path=$_.Path; "
                "    hostId=if ($_.HostId) {$_.HostId.ToString()} else {$null} "
                "  } | ConvertTo-Json -Compress "
                "}"
            )
            result = await self._run_script(script, timeout=60)
            if not result["success"]:
                return []
            return self._parse_json_array(result["stdout"])

        if collector == "managed_servers":
            script = (
                prefix
                + "Get-VBRServer | ForEach-Object { "
                "  @{"
                "    id=$_.Id.ToString(); "
                "    name=$_.Name; "
                "    type=$_.GetType().Name; "
                "    description=$_.Description; "
                "    hostId=if ($_.HostId) {$_.HostId.ToString()} else {$null} "
                "  } | ConvertTo-Json -Compress "
                "}"
            )
            result = await self._run_script(script, timeout=60)
            if not result["success"]:
                return []
            return self._parse_json_array(result["stdout"])

        if collector == "restore_points":
            script = (
                prefix
                + "Get-VBRRestorePoint -Result Success -MaxCount 200 | ForEach-Object { "
                "  @{"
                "    id=$_.Id.ToString(); "
                "    jobId=$_.JobId.ToString(); "
                "    creationTime=$_.CreationTime.ToString('o'); "
                "    size=$_.Size "
                "  } | ConvertTo-Json -Compress "
                "}"
            )
            result = await self._run_script(script, timeout=120)
            if not result["success"]:
                return []
            return self._parse_json_array(result["stdout"])

        if collector == "license":
            script = (
                prefix
                + "$ver = (Get-Module Veeam.Backup.PowerShell).Version; "
                "$jobCount = (Get-VBRJob -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count); "
                "if ($ver) { "
                "  @{"
                "    moduleVersion=$ver.ToString(); "
                "    jobCount=[int]$jobCount; "
                "    edition='Enterprise'; "
                "    available=$true "
                "  } | ConvertTo-Json -Compress "
                "} else { @{available=$false} | ConvertTo-Json -Compress }"
            )
            result = await self._run_script(script, timeout=30)
            if not result["success"]:
                return []
            return self._parse_json_array(result["stdout"]) or result["data"]

        return []

    @staticmethod
    def _parse_json_array(raw: str) -> list[dict[str, Any]]:
        if not raw:
            return []
        text = raw.strip()
        if not text:
            return []
        if text.startswith("[") and text.endswith("]"):
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict):
                return [parsed]
        except json.JSONDecodeError:
            pass
        return []
