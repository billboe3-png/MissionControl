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
import time
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
        self._use_relay = False
        self._ssh_target: dict[str, Any] | None = None
        self._token: str | None = None
        self._token_expires_at: float = 0.0

    async def initialize(self, context: dict[str, Any]) -> bool:
        self._context = context
        self._use_rest = False
        self._use_relay = False
        self._has_module = None
        self._api_base = _VEEAM_API_BASE
        self._username = _VEEAM_USERNAME
        self._password = _VEEAM_PASSWORD
        self._ssh_target = None
        self._token = None
        self._token_expires_at = 0.0
        return True

    def reinitialize(self) -> None:
        """Allow agent to reload integration profiles from updated context."""
        self._configured_from_context = False
        self._token = None
        self._token_expires_at = 0.0

    def _find_remote_target_for_api_base(self) -> dict[str, Any] | None:
        """Find an SSH remote target whose hostname matches the Veeam API base."""
        remote_targets = (self._context.get("remote_targets") or [])
        if not self._api_base or not remote_targets:
            return None
        api_base = self._api_base.strip()
        if api_base.startswith("https://"):
            api_base = api_base[len("https://"):]
        if api_base.startswith("http://"):
            api_base = api_base[len("http://"):]
        hostname = api_base.split("/", 1)[0].split(":", 1)[0]
        for target in remote_targets:
            if not isinstance(target, dict):
                continue
            if target.get("hostname") == hostname and (target.get("protocol") or "").lower() == "ssh":
                return target
        return None

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
                self._ssh_target = {
                    "hostname": ssh_host,
                    "port": ssh_port,
                    "username": ssh_username or self._username,
                    "password": ssh_password or self._password,
                    "protocol": "ssh",
                }
            else:
                remote_target = self._find_remote_target_for_api_base()
                if remote_target:
                    self._ssh_target = remote_target

        system = platform.system()

        if system == "Windows":
            if self._api_base and self._username:
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
            if self._ssh_target:
                self._use_relay = True
                logger.info("Veeam plugin initialized for Linux via SSH relay (%s)", self._ssh_target.get("hostname"))
            else:
                self._use_rest = True
                logger.info("Veeam plugin initialized for Linux REST API (%s)", self._api_base)
            return

        logger.warning("Veeam plugin not supported on %s", system)

    async def collect_inventory(self) -> dict[str, Any]:
        """Collect Veeam inventory."""
        await self._ensure_configured()
        if self._use_relay:
            return await self._collect_inventory_relay()
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
        if self._use_relay:
            return await self._execute_relay(command, args)
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
    # OAuth2 / Bearer token handling
    # ------------------------------------------------------------------

    async def _ensure_token(self) -> None:
        """Acquire a bearer token from Veeam OAuth2 endpoint if needed."""
        if self._token and time.time() < (self._token_expires_at - 30):
            return
        if not self._api_base or not self._username or not self._password:
            logger.warning("Veeam token acquisition skipped: missing api_base/username/password")
            return
        token_url = f"{self._api_base.rstrip('/')}/api/oauth2/token"
        body = {
            "grant_type": "password",
            "username": self._username,
            "password": self._password or "",
        }
        try:
            import httpx
        except ImportError:
            logger.warning("httpx not installed for Veeam token acquisition")
            return
        try:
            async with httpx.AsyncClient(verify=False, timeout=20) as client:
                resp = await client.post(
                    token_url,
                    data=body,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
            if resp.status_code == 200:
                payload = resp.json()
                self._token = payload.get("access_token")
                expires_in = int(payload.get("expires_in", 900))
                self._token_expires_at = time.time() + max(expires_in, 60)
                logger.info("Veeam bearer token acquired; expires in %ss", expires_in)
            else:
                logger.warning("Veeam token acquisition failed: %s -> %s", token_url, resp.status_code)
        except Exception as exc:
            logger.warning("Veeam token acquisition error: %s", exc)

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
            await self._ensure_token()
            headers = {"x-api-version": "1.3-rev1"}
            if self._token:
                headers["Authorization"] = f"Bearer {self._token}"
            async with httpx.AsyncClient(verify=False, timeout=30) as client:
                resp = await client.get(url, headers=headers)
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
            if resp.status_code == 401:
                self._token = None
                self._token_expires_at = 0.0
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
            await self._ensure_token()
            headers = {"x-api-version": "1.3-rev1"}
            if self._token:
                headers["Authorization"] = f"Bearer {self._token}"
            async with httpx.AsyncClient(verify=False, timeout=30) as client:
                resp = await client.post(url, json=payload, headers=headers)
            return {
                "success": resp.status_code in (200, 202),
                "stdout": resp.text,
                "stderr": "" if resp.status_code in (200, 202) else resp.text,
                "exit_code": resp.status_code,
            }
        except Exception as exc:
            return {"success": False, "error": str(exc), "stdout": "", "stderr": str(exc), "exit_code": -1}

    async def _collect_inventory_rest(self) -> dict[str, Any]:
        jobs = await self._rest_get("/api/v1/jobs")
        if jobs is None:
            logger.info("Veeam REST /jobs failed, trying local PowerShell fallback on agent host")
            jobs = await self._run_collector("jobs") or []
            logger.info("Veeam local PowerShell jobs fallback returned %d jobs", len(jobs) if isinstance(jobs, list) else 0)
        sessions = await self._rest_get("/api/v1/sessions") or []
        repos = await self._rest_get("/api/v1/backupInfrastructure/repositories") or []
        managed_servers = await self._rest_get("/api/v1/backupInfrastructure/managedServers") or []
        restore_points = await self._rest_get("/api/v1/restorePoints") or []
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
                await self._ensure_token()
                headers = {"x-api-version": "1.3-rev1"}
                if self._token:
                    headers["Authorization"] = f"Bearer {self._token}"
                async with httpx.AsyncClient(verify=False, timeout=10) as client:
                    resp = await client.get(url, headers=headers)
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

    async def _collect_inventory_relay(self) -> dict[str, Any]:
        logger.info("Veeam relay inventory collection starting")
        jobs = await self._run_collector_via_relay("jobs")
        logger.info("Veeam relay jobs collected=%d", len(jobs or []))
        sessions = await self._run_collector_via_relay("sessions")
        logger.info("Veeam relay sessions collected=%d", len(sessions or []))
        repos = await self._run_collector_via_relay("repositories")
        logger.info("Veeam relay repos collected=%d", len(repos or []))
        managed_servers = await self._run_collector_via_relay("managed_servers")
        logger.info("Veeam relay managed_servers collected=%d", len(managed_servers or []))
        restore_points = await self._run_collector_via_relay("restore_points")
        logger.info("Veeam relay restore_points collected=%d", len(restore_points or []))
        license = await self._run_collector_via_relay("license")
        logger.info("Veeam relay license collected=%s", bool(license))
        return {
            "jobs": jobs or [],
            "sessions": sessions or [],
            "repositories": repos or [],
            "managed_servers": managed_servers or [],
            "restore_points": restore_points or [],
            "license": license or {},
        }

    async def _execute_relay(self, command: str, args: dict[str, Any]) -> dict[str, Any]:
        if command == "test_connection":
            result = await self._run_collector_via_relay("license")
            if result is None:
                return {"success": False, "error": "Veeam relay test failed", "available": False}
            return {"success": True, "available": True, "message": "Veeam SSH relay reachable"}
        if command == "start_job":
            script = (
                "Import-Module Veeam.Backup.PowerShell -ErrorAction SilentlyContinue; "
                f"Start-VBRJob -JobId {args.get('job_id','')} -ErrorAction Stop | ConvertTo-Json -Compress"
            )
            result = await self._run_script_via_relay(script, timeout=60)
            return {"success": result.get("success", False), "stdout": result.get("stdout", ""), "stderr": result.get("stderr", ""), "exit_code": result.get("exit_code", -1)}
        if command == "stop_job":
            script = (
                "Import-Module Veeam.Backup.PowerShell -ErrorAction SilentlyContinue; "
                f"Stop-VBRJob -JobId {args.get('job_id','')} -ErrorAction Stop | ConvertTo-Json -Compress"
            )
            result = await self._run_script_via_relay(script, timeout=60)
            return {"success": result.get("success", False), "stdout": result.get("stdout", ""), "stderr": result.get("stderr", ""), "exit_code": result.get("exit_code", -1)}
        return {"success": False, "error": f"Unknown relay command: {command}"}

    async def _run_collector_via_relay(self, collector: str) -> Any:
        script_map = {
            "jobs": (
                "Import-Module Veeam.Backup.PowerShell -ErrorAction SilentlyContinue; "
                "Get-VBRJob | ForEach-Object { $j=$_; $last=Get-VBRSession -Job $j -Last 1 | Select-Object -First 1; @{"
                "id=$j.Id.ToString(); name=$j.Name; type=$j.JobType.ToString(); "
                "state=if ($j.IsRunning) {'Running'} else {'Stopped'}; enabled=$j.Options.Enabled; "
                "schedule=if ($j.ScheduleOptions -and $j.ScheduleOptions.Enabled) {@{kind='periodic'}} else {$null}; "
                "lastRun=if ($last) @{ id=$last.Id.ToString(); state=$last.State.ToString(); result=@{result=$last.Result.ToString()}; "
                "creationTime=$last.CreationTime.ToString('o'); endTime=$last.EndTime.ToString('o'); progressPercent=$last.Progress } else {$null}; "
                "includedObjects=@{objectsInJob=if ($j.Info) {$j.Info.LinkedObjects.Count} else {0}} "
                "} | ConvertTo-Json -Compress }"
            ),
            "sessions": (
                "Import-Module Veeam.Backup.PowerShell -ErrorAction SilentlyContinue; "
                "Get-VBRSession -Last 200 | ForEach-Object { @{"
                "id=$_.Id.ToString(); jobId=$_.JobId.ToString(); name=$_.Name; sessionType=$_.SessionType.ToString(); "
                "state=$_.State.ToString(); result=@{result=$_.Result.ToString()}; creationTime=$_.CreationTime.ToString('o'); "
                "endTime=$_.EndTime.ToString('o'); progressPercent=$_.Progress "
                "} | ConvertTo-Json -Compress }"
            ),
            "repositories": (
                "Import-Module Veeam.Backup.PowerShell -ErrorAction SilentlyContinue; "
                "Get-VBRBackupRepository | ForEach-Object { @{"
                "id=$_.Id.ToString(); name=$_.Name; type=$_.GetType().Name; description=$_.Description; path=$_.Path; "
                "hostId=if ($_.HostId) {$_.HostId.ToString()} else {$null} "
                "} | ConvertTo-Json -Compress }"
            ),
            "managed_servers": (
                "Import-Module Veeam.Backup.PowerShell -ErrorAction SilentlyContinue; "
                "Get-VBRServer | ForEach-Object { @{"
                "id=$_.Id.ToString(); name=$_.Name; type=$_.GetType().Name; description=$_.Description; "
                "hostId=if ($_.HostId) {$_.HostId.ToString()} else {$null} "
                "} | ConvertTo-Json -Compress }"
            ),
            "restore_points": (
                "Import-Module Veeam.Backup.PowerShell -ErrorAction SilentlyContinue; "
                "Get-VBRRestorePoint -Result Success -MaxCount 200 | ForEach-Object { @{"
                "id=$_.Id.ToString(); jobId=$_.JobId.ToString(); creationTime=$_.CreationTime.ToString('o'); size=$_.Size "
                "} | ConvertTo-Json -Compress }"
            ),
            "license": (
                "Import-Module Veeam.Backup.PowerShell -ErrorAction SilentlyContinue; "
                "$ver=(Get-Module Veeam.Backup.PowerShell).Version; $lic=Get-VBRLicense; @{"
                "type=$lic.Edition.ToString(); status=$lic.Status.ToString(); supportId=$lic.SupportId; "
                "expirationDate=$lic.ExpirationDate.ToString('o'); edition=$lic.Edition.ToString(); "
                "moduleVersion=if ($ver) {$ver.ToString()} else {$null} "
                "} | ConvertTo-Json -Compress"
            ),
        }
        script = script_map.get(collector)
        if not script:
            return None
        result = await self._run_script_via_relay(script, timeout=120)
        if not result.get("success"):
            return None
        return self._parse_json_array(result.get("stdout", "[]")) or []

    # ------------------------------------------------------------------
    # Relay fallback for Windows backend inventory
    # ------------------------------------------------------------------

    async def _collect_jobs_via_relay(self) -> list[dict[str, Any]]:
        """Collect Veeam jobs from the Windows backend via agent SSH relay."""
        remote_manager = (self._context.get("remote_manager") or None)
        if remote_manager is None:
            logger.warning("Veeam jobs relay skipped: remote_manager not in plugin context")
            return []

        if not self._api_base:
            logger.warning("Veeam jobs relay skipped: api_base not configured")
            return []

        hostname = ""
        api_base = self._api_base.strip()
        if api_base.startswith("https://"):
            api_base = api_base[len("https://"):]
        if api_base.startswith("http://"):
            api_base = api_base[len("http://"):]
        hostname = api_base.split("/", 1)[0].split(":", 1)[0]
        if not hostname:
            return []

        target_id = None
        for tid, target in (remote_manager.targets or {}).items():
            if target.get("hostname") == hostname and (target.get("protocol") or "").lower() == "ssh":
                target_id = tid
                break
        if target_id is None:
            logger.warning("Veeam jobs relay skipped: no SSH target for host %s", hostname)
            return []

        script = (
            "Import-Module Veeam.Backup.PowerShell -ErrorAction SilentlyContinue; "
            "Get-VBRJob | ForEach-Object { "
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
        logger.info("Veeam jobs relay via SSH target %s", target_id)
        result = await self._run_script_via_relay(script, timeout=90)
        if not result.get("success"):
            return []
        return self._parse_json_array(result.get("stdout", "[]")) or []

    async def _run_script_via_relay(self, script: str, timeout: int = 60) -> dict[str, Any]:
        """Execute a PowerShell script on the Veeam Windows backend via SSH relay."""
        remote_manager = (self._context.get("remote_manager") or None)
        if remote_manager is None:
            return {"success": False, "stdout": "", "stderr": "remote_manager not configured", "exit_code": -1}

        if not self._api_base:
            return {"success": False, "stdout": "", "stderr": "Veeam API base not configured", "exit_code": -1}

        hostname = ""
        api_base = self._api_base.strip()
        if api_base.startswith("https://"):
            api_base = api_base[len("https://"):]
        if api_base.startswith("http://"):
            api_base = api_base[len("http://"):]
        hostname = api_base.split("/", 1)[0].split(":", 1)[0]
        if not hostname:
            return {"success": False, "stdout": "", "stderr": "invalid api_base", "exit_code": -1}

        target_id = None
        for tid, target in (remote_manager.targets or {}).items():
            if target.get("hostname") == hostname and (target.get("protocol") or "").lower() == "ssh":
                target_id = tid
                break
        if target_id is None:
            return {"success": False, "stdout": "", "stderr": f"no SSH target for host {hostname}", "exit_code": -1}

        encoded = self._encode_powershell(script)
        ps_command = f"powershell -NoProfile -NonInteractive -EncodedCommand {encoded}"
        logger.info("Veeam relay command -> target %s", target_id)
        return await remote_manager.execute_on_target(
            target_id=target_id,
            command=ps_command,
            timeout=timeout,
        )

    @staticmethod
    def _encode_powershell(script: str) -> str:
        """Encode a PowerShell script as base64 UTF-16LE for -EncodedCommand."""
        import base64
        encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
        return encoded

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
