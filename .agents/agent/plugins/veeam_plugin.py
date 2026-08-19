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
import tempfile
import time
from pathlib import Path
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
        remote_targets = self._context.get("remote_targets") or []
        if not self._api_base or not remote_targets:
            return None
        api_base = self._api_base.strip()
        if api_base.startswith("https://"):
            api_base = api_base[len("https://") :]
        if api_base.startswith("http://"):
            api_base = api_base[len("http://") :]
        hostname = api_base.split("/", 1)[0].split(":", 1)[0]
        for target in remote_targets:
            if not isinstance(target, dict):
                continue
            if (
                target.get("hostname") == hostname
                and (target.get("protocol") or "").lower() == "ssh"
            ):
                return target
        return None

    def _find_remote_target_for_plugin(self) -> dict[str, Any] | None:
        """Find the first remote target configured with the Veeam plugin enabled."""
        remote_targets = self._context.get("remote_targets") or []
        for target in remote_targets:
            if not isinstance(target, dict):
                continue
            target_plugins = (target.get("target_plugins") or "").strip()
            if not target_plugins:
                continue
            plugins = {p.strip() for p in target_plugins.split(",") if p.strip()}
            if "veeam" in plugins:
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

        # If still not configured, try to derive from a remote target tagged with veeam plugin
        if not self._api_base or not self._username:
            target = self._find_remote_target_for_plugin()
            if target:
                hostname = target.get("hostname") or target.get("name") or ""
                port = target.get("port") or 9419
                username = target.get("username") or ""
                password = target.get("password") or ""
                ssh_key = target.get("ssh_key") or ""
                self._api_base = f"https://{hostname}:{port}"
                self._username = username or self._username
                self._password = password or self._password
                self._ssh_target = {
                    "hostname": hostname,
                    "port": port,
                    "username": username or self._username,
                    "password": password or self._password,
                    "ssh_key": ssh_key or None,
                    "protocol": target.get("protocol") or "ssh",
                }
                logger.info(
                    "Veeam plugin configured from remote target %s", hostname
                )

        system = platform.system()

        if system == "Windows":
            if self._api_base and self._username:
                # Check if this Veeam server is also an SSH remote target
                if not self._ssh_target:
                    self._ssh_target = self._find_remote_target_for_api_base()
                if (
                    self._ssh_target
                    and (self._ssh_target.get("protocol") or "").lower() == "ssh"
                ):
                    self._use_relay = True
                    self._use_rest = False
                    logger.info(
                        "Veeam plugin initialized for Windows via SSH relay (%s)",
                        self._ssh_target.get("hostname"),
                    )
                    return
                self._use_rest = True
                self._use_relay = False
                logger.info(
                    "Veeam plugin initialized for Windows REST API (%s)", self._api_base
                )
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
                logger.info(
                    "Veeam plugin initialized for Linux via SSH relay (%s)",
                    self._ssh_target.get("hostname"),
                )
            else:
                self._use_rest = True
                logger.info(
                    "Veeam plugin initialized for Linux REST API (%s)", self._api_base
                )
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

    async def execute_command(
        self, command: str, args: dict[str, Any]
    ) -> dict[str, Any]:
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
        await self._configure_from_context()

    # ------------------------------------------------------------------
    # OAuth2 / Bearer token handling
    # ------------------------------------------------------------------

    async def _ensure_token(self) -> None:
        """Acquire a bearer token from Veeam OAuth2 endpoint if needed."""
        if self._token and time.time() < (self._token_expires_at - 30):
            return
        if not self._api_base or not self._username or not self._password:
            logger.warning(
                "Veeam token acquisition skipped: missing api_base/username/password"
            )
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
                logger.warning(
                    "Veeam token acquisition failed: %s -> %s",
                    token_url,
                    resp.status_code,
                )
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
                        logger.info(
                            "Veeam REST %s data keys=%s count=%s",
                            url,
                            sorted(parsed.keys()),
                            len(parsed.get("data", parsed))
                            if isinstance(parsed.get("data"), list)
                            else "n/a",
                        )
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
            return {
                "success": False,
                "error": str(exc),
                "stdout": "",
                "stderr": str(exc),
                "exit_code": -1,
            }

    async def _collect_inventory_rest(self) -> dict[str, Any]:
        jobs = await self._rest_get("/api/v1/jobs")
        logger.info(
            "Veeam REST /jobs returned type=%s value=%s",
            type(jobs).__name__,
            str(jobs)[:200],
        )
        if jobs is None:
            logger.info(
                "Veeam REST /jobs failed, trying local PowerShell fallback on agent host"
            )
            jobs = await self._run_collector("jobs") or []
            logger.info(
                "Veeam local PowerShell jobs fallback returned %d jobs",
                len(jobs) if isinstance(jobs, list) else 0,
            )
        elif isinstance(jobs, list) and len(jobs) == 0:
            logger.info(
                "Veeam REST /jobs returned empty list, trying local PowerShell fallback"
            )
            local_jobs = await self._run_collector("jobs") or []
            logger.info(
                "Veeam local PowerShell jobs fallback returned %d jobs", len(local_jobs)
            )
            if local_jobs:
                jobs = local_jobs
        sessions = await self._rest_get("/api/v1/sessions") or []
        repos = await self._rest_get("/api/v1/backupInfrastructure/repositories") or []
        managed_servers = (
            await self._rest_get("/api/v1/backupInfrastructure/managedServers") or []
        )
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
                    return {
                        "success": True,
                        "available": True,
                        "message": "Veeam REST API reachable",
                    }
                return {
                    "success": False,
                    "error": f"HTTP {resp.status_code}: {resp.text}",
                    "available": False,
                }
            except Exception as exc:
                return {"success": False, "error": str(exc), "available": False}
        if command == "start_job":
            return await self._rest_post(
                f"/api/v1/jobs/{args.get('job_id', '')}/start", {}
            )
        if command == "stop_job":
            return await self._rest_post(
                f"/api/v1/jobs/{args.get('job_id', '')}/stop", {}
            )
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
                except TimeoutError:
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
            stdout_text = (
                stdout.decode("utf-8", errors="replace").strip() if stdout else ""
            )
            stderr_text = (
                stderr.decode("utf-8", errors="replace").strip() if stderr else ""
            )
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
        except TimeoutError:
            return {
                "success": False,
                "stdout": "",
                "stderr": "timeout",
                "exit_code": -1,
                "data": None,
            }
        except Exception as exc:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(exc),
                "exit_code": -1,
                "data": None,
            }

    async def _run_script_file(self, script: str, timeout: int = 60) -> dict[str, Any]:
        try:
            fd, path = tempfile.mkstemp(suffix=".ps1")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(script)
                proc = await asyncio.create_subprocess_exec(
                    "powershell",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout
                )
                stdout_text = (
                    stdout.decode("utf-8", errors="replace").strip() if stdout else ""
                )
                stderr_text = (
                    stderr.decode("utf-8", errors="replace").strip() if stderr else ""
                )
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
            finally:
                Path(path).unlink(missing_ok=True)
        except TimeoutError:
            return {
                "success": False,
                "stdout": "",
                "stderr": "timeout",
                "exit_code": -1,
                "data": None,
            }
        except Exception as exc:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(exc),
                "exit_code": -1,
                "data": None,
            }

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

    async def _execute_windows(
        self, command: str, args: dict[str, Any]
    ) -> dict[str, Any]:
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
            return {
                "success": False,
                "error": "Veeam PowerShell module not available on this host",
            }

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
            return {
                "success": False,
                "error": result["stderr"],
                "stdout": result["stdout"],
                "exit_code": result["exit_code"],
            }

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

    async def _execute_linux(
        self, command: str, args: dict[str, Any]
    ) -> dict[str, Any]:
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
        logger.info(
            "Veeam relay managed_servers collected=%d", len(managed_servers or [])
        )
        restore_points = await self._run_collector_via_relay("restore_points")
        logger.info(
            "Veeam relay restore_points collected=%d", len(restore_points or [])
        )
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

    async def _execute_relay(
        self, command: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        target_id = args.get("target_id")
        collector_ops = {
            "veeam:jobs": "jobs",
            "veeam:sessions": "sessions",
            "veeam:repositories": "repositories",
            "veeam:managed_servers": "managed_servers",
            "veeam:restore_points": "restore_points",
            "veeam:license": "license",
        }
        payload_key = {"managed_servers": "servers"}
        if command in collector_ops:
            collector = collector_ops[command]
            items = await self._run_collector_via_relay(collector, target_id=target_id)
            if collector in ("jobs", "sessions", "repositories") and items is None:
                items = await self._db_collect(collector, target_id)
            if collector == "license":
                return {
                    "success": bool(items),
                    "license": items or {},
                    "error": None if items else "Veeam relay license unavailable",
                }
            key = payload_key.get(collector, collector)
            return {
                "success": items is not None,
                key: items or [],
                "count": len(items or []),
                "error": None if items is not None else "Veeam relay collection failed",
            }
        if command == "veeam:test":
            db_ok = await self._db_ping(target_id)
            return {
                "success": db_ok,
                "rest_available": False,
                "powershell_available": False,
                "db_available": db_ok,
                "version": "",
                "error": None if db_ok else "Veeam DB bridge unavailable",
            }
        if command == "veeam:job_stats":
            jobs = await self._db_job_stats(target_id)
            return {
                "success": jobs is not None,
                "jobs": jobs or [],
                "count": len(jobs or []),
                "ssh_available": jobs is not None,
                "message": None,
                "error": None if jobs is not None else "Veeam DB bridge unavailable",
            }
        if command == "veeam:session_stats":
            stats = await self._db_session_stats(target_id)
            return {
                "success": stats is not None,
                "stats": stats or [],
                "count": len(stats or []),
                "ssh_available": stats is not None,
                "message": None,
                "error": None if stats is not None else "Veeam DB bridge unavailable",
            }
        if command == "veeam:job_stats_daily":
            days = int(args.get("days", 7) or 7)
            jobs, dates = await self._db_job_stats_daily(days, target_id)
            return {
                "success": jobs is not None,
                "jobs": jobs or [],
                "dates": dates or [],
                "count": len(jobs or []),
                "ssh_available": jobs is not None,
                "message": None,
                "error": None if jobs is not None else "Veeam DB bridge unavailable",
            }
        if command == "veeam:db:detect":
            return await self._db_detect(target_id)
        if command == "veeam:db:query":
            out = await self._run_db_query_via_relay(
                str(args.get("sql", "")), target_id=target_id
            )
            if out is None:
                return {
                    "success": False, "output": "", "stderr": "DB query failed",
                    "exit_code": 1, "error": "Veeam DB query failed",
                }
            return {"success": True, "output": out, "stderr": "", "exit_code": 0}
        if command == "veeam:capacity_tier":
            return {"success": True, "object_storages": [], "count": 0, "error": None}
        if command == "test_connection":
            db_ok = await self._db_ping(target_id)
            if not db_ok:
                return {
                    "success": False,
                    "error": "Veeam DB bridge test failed",
                    "available": False,
                }
            return {
                "success": True,
                "available": True,
                "message": "Veeam DB bridge reachable",
            }
        if command == "start_job":
            script = (
                "Import-Module Veeam.Backup.PowerShell -ErrorAction SilentlyContinue; "
                f"Start-VBRJob -JobId {args.get('job_id', '')} -ErrorAction Stop | ConvertTo-Json -Compress"
            )
            result = await self._run_script_via_relay(
                script, timeout=60, target_id=target_id
            )
            return {
                "success": result.get("success", False),
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", ""),
                "exit_code": result.get("exit_code", -1),
            }
        if command == "stop_job":
            script = (
                "Import-Module Veeam.Backup.PowerShell -ErrorAction SilentlyContinue; "
                f"Stop-VBRJob -JobId {args.get('job_id', '')} -ErrorAction Stop | ConvertTo-Json -Compress"
            )
            result = await self._run_script_via_relay(
                script, timeout=60, target_id=target_id
            )
            return {
                "success": result.get("success", False),
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", ""),
                "exit_code": result.get("exit_code", -1),
            }
        return {"success": False, "error": f"Unknown relay command: {command}"}

    # ------------------------------------------------------------------
    # PostgreSQL DB bridge (agent relay ops: jobs/stats/sessions/detect)
    # ------------------------------------------------------------------

    _PSQL = r"C:\Program Files\PostgreSQL\15\bin\psql.exe"
    _DB_NAME = "VeeamBackup"
    _DB_USER = "postgres"
    _WHERE_FILTER = """\
AND js.job_name NOT LIKE '%Resynchronize%'
AND js.job_name NOT LIKE '%Host Discovery%'
AND js.job_name NOT LIKE '%Foreign transform%'
AND js.job_name NOT LIKE '%Infrastructure update%'
AND js.job_name NOT LIKE '%Audit Logs%'
AND js.job_name NOT LIKE '%Catalog Cleanup%'
AND js.job_name NOT LIKE '%Shell run%'
AND js.job_name NOT LIKE '%Backup Configuration%'
AND js.job_name NOT LIKE '%Hyper-V CBT%'
AND js.job_name NOT LIKE '%Rescan%'
AND js.job_name NOT LIKE '%Checkpoint Removal%'
AND js.job_name NOT LIKE '%Retention job%'
AND js.job_name NOT LIKE '%Malware Detection%'"""

    @staticmethod
    def _norm_name() -> str:
        return "regexp_replace(js.job_name, ' - [A-Za-z0-9._]+$', '')"

    async def _run_db_query_via_relay(
        self, sql: str, target_id: int | None = None, timeout: int = 120,
    ) -> str | None:
        """Run a SQL query against the Veeam PostgreSQL DB via SSH relay."""
        if not sql:
            return None
        ps_script = (
            "$sql = @'\n" + sql + "\n'@\n"
            "$sqlPath = 'C:\\temp\\mc_query.sql'\n"
            "New-Item -ItemType Directory -Force -Path 'C:\\temp' | Out-Null\n"
            "[System.IO.File]::WriteAllText($sqlPath, $sql, [System.Text.Encoding]::UTF8)\n"
            "& '" + self._PSQL + "' -h 127.0.0.1 -U " + self._DB_USER + " -d " + self._DB_NAME + " -t -A -f $sqlPath 2>&1 | Out-String\n"
        )
        result = await self._run_script_via_relay(
            ps_script, timeout=timeout, target_id=target_id
        )
        if not result.get("success"):
            logger.error(
                "Veeam DB relay failed: stderr=%s",
                str(result.get("stderr", ""))[:1000],
            )
            return None
        return str(result.get("stdout", "") or "")

    async def _db_ping(self, target_id: int | None = None) -> bool:
        out = await self._run_db_query_via_relay(
            "SELECT 1", target_id=target_id, timeout=60,
        )
        return out is not None and "1" in out

    async def _db_detect(self, target_id: int | None = None) -> dict[str, Any]:
        """Probe psql binary + PG port on the Veeam host."""
        result = await self._run_script_via_relay(
            "if (Test-Path '" + self._PSQL + "') { Write-Output 'PSQL_FOUND' }",
            timeout=60, target_id=target_id,
        )
        psql_found = "PSQL_FOUND" in (result.get("stdout") or "")
        return {
            "success": True,
            "db_type": "postgresql" if psql_found else "mssql",
            "psql_found": psql_found,
            "sqlcmd_found": False,
            "pg_port": psql_found,
            "mssql_port": False,
        }

    async def _db_job_stats(
        self, target_id: int | None = None,
    ) -> list[dict[str, Any]] | None:
        sql = (
            "SELECT " + self._norm_name() + " AS job_name, "
            "COUNT(*) as session_count, "
            "COALESCE(SUM(bs.total_size), 0), "
            "COALESCE(SUM(bs.processed_size), 0), "
            "COALESCE(SUM(bs.read_size), 0), "
            "COALESCE(SUM(bs.stored_size), 0), "
            "COALESCE(AVG(bs.avg_speed), 0), "
            "MAX(js.creation_time), "
            "SUM(CASE WHEN js.result = 0 THEN 1 ELSE 0 END), "
            "SUM(CASE WHEN js.result = 1 THEN 1 ELSE 0 END), "
            "SUM(CASE WHEN js.result = 2 THEN 1 ELSE 0 END) "
            'FROM "backup.model.jobsessions" js '
            'LEFT JOIN "backup.model.backupjobsessions" bs ON bs.id = js.id '
            "WHERE 1=1 " + self._WHERE_FILTER + " "
            "GROUP BY 1 "
            "ORDER BY MAX(js.creation_time) DESC"
        )
        raw = await self._run_db_query_via_relay(sql, target_id=target_id)
        rows = self._parse_psql_rows(raw)
        jobs = []
        for r in rows:
            if len(r) < 11:
                continue
            jobs.append({
                "job_name": r[0],
                "session_count": int(r[1] or 0),
                "total_bytes": int(float(r[2] or 0)),
                "processed_bytes": int(float(r[3] or 0)),
                "read_bytes": int(float(r[4] or 0)),
                "stored_bytes": int(float(r[5] or 0)),
                "avg_speed": float(r[6] or 0),
                "last_run": r[7] or None,
                "success_count": int(r[8] or 0),
                "warning_count": int(r[9] or 0),
                "failed_count": int(r[10] or 0),
            })
        return jobs

    async def _db_session_stats(
        self, target_id: int | None = None,
    ) -> list[dict[str, Any]] | None:
        sql = (
            "SELECT js.id, js.job_id, "
            + self._norm_name() + " AS job_name, "
            "js.state, js.creation_time, js.end_time, js.result, "
            "COALESCE(bs.processed_size, 0), "
            "COALESCE(bs.read_size, 0), "
            "COALESCE(bs.stored_size, 0) "
            'FROM "backup.model.jobsessions" js '
            'LEFT JOIN "backup.model.backupjobsessions" bs ON bs.id = js.id '
            "WHERE 1=1 " + self._WHERE_FILTER + " "
            "ORDER BY js.creation_time DESC "
            "LIMIT 200"
        )
        raw = await self._run_db_query_via_relay(sql, target_id=target_id)
        rows = self._parse_psql_rows(raw)
        stats = []
        for r in rows:
            if len(r) < 10:
                continue
            stats.append({
                "session_id": r[0],
                "job_id": r[1],
                "job_name": r[2],
                "creation_time": r[4] or None,
                "end_time": r[5] or None,
                "state": r[3],
                "processed_bytes": int(float(r[7] or 0)),
                "read_bytes": int(float(r[8] or 0)),
                "transferred_bytes": int(float(r[9] or 0)),
            })
        return stats

    async def _db_job_stats_daily(
        self, days: int, target_id: int | None = None,
    ) -> tuple[list[dict[str, Any]] | None, list[str]]:
        days = max(1, int(days))
        sql = (
            "SELECT " + self._norm_name() + " AS job_name, "
            "DATE(js.creation_time) AS run_date, "
            "COALESCE(SUM(bs.processed_size), 0), "
            "COALESCE(SUM(bs.read_size), 0), "
            "COALESCE(SUM(bs.stored_size), 0), "
            "COUNT(*) AS session_count, "
            "SUM(CASE WHEN js.result = 0 THEN 1 ELSE 0 END) AS success_count, "
            "SUM(CASE WHEN js.result = 1 THEN 1 ELSE 0 END) AS warning_count, "
            "SUM(CASE WHEN js.result = 2 THEN 1 ELSE 0 END) AS failed_count "
            'FROM "backup.model.jobsessions" js '
            'LEFT JOIN "backup.model.backupjobsessions" bs ON bs.id = js.id '
            "WHERE js.creation_time >= NOW() - INTERVAL '" + str(days) + " days' "
            + self._WHERE_FILTER + " "
            "GROUP BY 1, DATE(js.creation_time) "
            "ORDER BY 1, DATE(js.creation_time) DESC"
        )
        raw = await self._run_db_query_via_relay(sql, target_id=target_id)
        if raw is None:
            return None, []
        rows = self._parse_psql_rows(raw)
        by_job: dict[str, dict[str, Any]] = {}
        date_set: set[str] = set()
        for r in rows:
            if len(r) < 9:
                continue
            job_name, run_date = r[0], r[1]
            if not run_date:
                continue
            date_set.add(run_date)
            cell = {
                "processed_bytes": int(float(r[2] or 0)),
                "read_bytes": int(float(r[3] or 0)),
                "stored_bytes": int(float(r[4] or 0)),
                "session_count": int(r[5] or 0),
                "success_count": int(r[6] or 0),
                "warning_count": int(r[7] or 0),
                "failed_count": int(r[8] or 0),
            }
            if cell["failed_count"] > 0:
                cell["result"] = "Failed"
            elif cell["warning_count"] > 0:
                cell["result"] = "Warning"
            else:
                cell["result"] = "Success"
            by_job.setdefault(job_name, {"job_name": job_name, "daily": {}})
            by_job[job_name]["daily"][run_date] = cell
        dates = sorted(date_set)
        jobs = sorted(by_job.values(), key=lambda j: j["job_name"])
        return jobs, dates

    async def _db_collect(
        self, collector: str, target_id: int | None = None,
    ) -> list[dict[str, Any]] | None:
        """Collect jobs/sessions from the Veeam DB (fallback for PS relay)."""
        if collector == "jobs":
            sql = (
                "SELECT b.id, b.name, b.type, b.schedule_enabled, "
                "COALESCE(js.state, -1) AS state, "
                "COALESCE(js.result, -1) AS result, "
                "js.creation_time, js.end_time, js.progress "
                "FROM bjobs b "
                "LEFT JOIN LATERAL ("
                "  SELECT state, result, creation_time, end_time, progress "
                '  FROM "backup.model.jobsessions" js '
                "  WHERE js.job_id = b.id "
                "  ORDER BY js.creation_time DESC LIMIT 1"
                ") js ON true "
                "WHERE b.is_deleted = false "
                "ORDER BY b.name"
            )
            raw = await self._run_db_query_via_relay(sql, target_id=target_id)
            if raw is None:
                return None
            rows = self._parse_psql_rows(raw)
            jobs = []
            for r in rows:
                if len(r) < 9:
                    continue
                last_state = self._map_job_state(int(r[4] or -1))
                last_result = self._map_result(int(r[5] or -1))
                last_run = None
                if r[6]:
                    last_run = {
                        "id": r[0],
                        "state": last_state,
                        "result": {"result": last_result} if last_result else None,
                        "creationTime": r[6],
                        "endTime": r[7],
                        "progressPercent": int(r[8] or 0),
                    }
                jobs.append({
                    "id": r[0],
                    "name": r[1],
                    "type": self._map_job_type(int(r[2] or 0)),
                    "state": last_state,
                    "enabled": bool(r[3]),
                    "schedule": {"kind": "periodic"} if bool(r[3]) else None,
                    "lastRun": last_run,
                    "includedObjects": {"objectsInJob": 0},
                })
            return jobs
        if collector == "sessions":
            sql = (
                "SELECT js.id, js.job_id, js.job_name, js.state, js.result, "
                "js.creation_time, js.end_time, js.progress "
                'FROM "backup.model.jobsessions" js '
                "WHERE 1=1 " + self._WHERE_FILTER + " "
                "ORDER BY js.creation_time DESC LIMIT 200"
            )
            raw = await self._run_db_query_via_relay(sql, target_id=target_id)
            if raw is None:
                return None
            rows = self._parse_psql_rows(raw)
            sessions = []
            for r in rows:
                if len(r) < 8:
                    continue
                result_name = self._map_result(int(r[4] or -1))
                sessions.append({
                    "id": r[0],
                    "jobId": r[1],
                    "name": r[2],
                    "sessionType": "Backup",
                    "state": self._map_job_state(int(r[3] or -1)),
                    "result": {"result": result_name} if result_name else None,
                    "creationTime": r[5] or None,
                    "endTime": r[6] or None,
                    "progressPercent": int(r[7] or 0),
                })
            return sessions
        if collector == "repositories":
            sql = (
                "SELECT id, name, description, type, host_id, path, "
                "is_unavailable, status "
                'FROM "backuprepositories" '
                "ORDER BY name"
            )
            raw = await self._run_db_query_via_relay(sql, target_id=target_id)
            if raw is None:
                return None
            rows = self._parse_psql_rows(raw)
            repos = []
            for r in rows:
                if len(r) < 8:
                    continue
                status = "Unavailable" if r[6] == "t" else "Available"
                repos.append({
                    "id": r[0],
                    "name": r[1],
                    "description": r[2] or "",
                    "type": self._map_repo_type(int(r[3] or 0)),
                    "hostId": r[4] or "",
                    "repository": {"path": r[5] or ""},
                    "status": status,
                })
            return repos
        return None

    @staticmethod
    def _parse_psql_rows(raw: str | None) -> list[list[str]]:
        rows = []
        if not raw:
            return rows
        for line in raw.splitlines():
            line = line.rstrip("\r").strip()
            if not line:
                continue
            rows.append([c.strip() for c in line.split("|")])
        return rows

    @staticmethod
    def _map_result(code: int) -> str | None:
        return {0: "Success", 1: "Warning", 2: "Failed"}.get(code)

    @staticmethod
    def _map_repo_type(code: int) -> str:
        return {
            0: "Windows",
            1: "Linux",
            2: "Scale-Out",
            3: "Object Storage",
            4: "Shared Folder",
            5: "Dedup Store",
            6: "ReFS",
            7: "XFS",
            11: "Object Storage",
        }.get(code, "Backup Repository")

    @staticmethod
    def _map_job_state(code: int) -> str:
        return {0: "Success", 1: "Warning", 2: "Failed"}.get(code, "Stopped")

    @staticmethod
    def _map_job_type(code: int) -> str:
        return {
            0: "Backup",
            1: "Replica",
            2: "Backup Copy",
            3: "NAS",
            4: "SureBackup",
            100: "Backup",
            12000: "Agent",
            13000: "NAS",
            14000: "Backup Copy",
        }.get(code, "Backup")

    async def _run_collector_via_relay(
        self, collector: str, target_id: int | None = None
    ) -> Any:
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
        result = await self._run_script_via_relay(
            script, timeout=120, target_id=target_id
        )
        if not result.get("success"):
            return None
        return self._parse_json_array(result.get("stdout", "[]")) or []

    # ------------------------------------------------------------------
    # Relay fallback for Windows backend inventory
    # ------------------------------------------------------------------

    async def _run_script_via_relay(
        self, script: str, timeout: int = 60, target_id: int | None = None
    ) -> dict[str, Any]:
        """Execute a PowerShell script on the Veeam server via SSH relay.

        Prefers the dispatched ``target_id`` (the agent remote target id from
        the server's ``veeam_backup_servers`` row). When no ``target_id`` is
        given or it does not match a known SSH target, falls back to resolving
        the SSH target from ``self._api_base`` (the existing single-target
        behavior).
        """
        remote_manager = self._context.get("remote_manager") or None
        if remote_manager is None:
            logger.warning("Veeam relay skipped: remote_manager not in plugin context")
            return {
                "success": False,
                "stdout": "",
                "stderr": "no remote_manager",
                "exit_code": -1,
                "data": None,
            }

        if not self._api_base:
            logger.warning("Veeam relay skipped: api_base not configured")
            return {
                "success": False,
                "stdout": "",
                "stderr": "no api_base",
                "exit_code": -1,
                "data": None,
            }

        if target_id is not None:
            try:
                target_id = int(target_id)
            except (TypeError, ValueError):
                target_id = None

        hostname = ""
        resolved_id: int | None = None
        if target_id is not None:
            target = (getattr(remote_manager, "targets", {}) or {}).get(target_id)
            if target and (target.get("protocol") or "").lower() == "ssh":
                resolved_id = target_id
                hostname = target.get("hostname") or ""

        if resolved_id is None:
            api_base = self._api_base.strip()
            if api_base.startswith("https://"):
                api_base = api_base[len("https://") :]
            if api_base.startswith("http://"):
                api_base = api_base[len("http://") :]
            hostname = api_base.split("/", 1)[0].split(":", 1)[0]

            for tid, target in (getattr(remote_manager, "targets", {}) or {}).items():
                if (
                    target.get("hostname") == hostname
                    and (target.get("protocol") or "").lower() == "ssh"
                ):
                    resolved_id = tid
                    break

        if resolved_id is None:
            logger.warning("Veeam relay skipped: no SSH target for host %s", hostname)
            return {
                "success": False,
                "stdout": "",
                "stderr": f"no ssh target for {hostname}",
                "exit_code": -1,
                "data": None,
            }

        encoded = self._encode_powershell(script)
        ps_command = f"powershell -NoProfile -NonInteractive -EncodedCommand {encoded}"
        logger.info("Veeam relay script -> target=%s host=%s", resolved_id, hostname)
        result = await remote_manager.execute_on_target(
            target_id=resolved_id,
            command=ps_command,
            timeout=timeout,
        )
        return {
            "success": result.get("success", False),
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
            "exit_code": result.get("exit_code", -1),
            "data": None,
        }

    async def _collect_jobs_via_relay(self) -> list[dict[str, Any]]:
        """Collect Veeam jobs from the Windows backend via agent SSH relay."""
        remote_manager = self._context.get("remote_manager") or None
        if remote_manager is None:
            logger.warning(
                "Veeam jobs relay skipped: remote_manager not in plugin context"
            )
            return []

        if not self._api_base:
            logger.warning("Veeam jobs relay skipped: api_base not configured")
            return []

        hostname = ""
        api_base = self._api_base.strip()
        if api_base.startswith("https://"):
            api_base = api_base[len("https://") :]
        if api_base.startswith("http://"):
            api_base = api_base[len("http://") :]
        hostname = api_base.split("/", 1)[0].split(":", 1)[0]
        if not hostname:
            return []

        target_id = None
        for tid, target in (remote_manager.targets or {}).items():
            if (
                target.get("hostname") == hostname
                and (target.get("protocol") or "").lower() == "ssh"
            ):
                target_id = tid
                break
        if target_id is None:
            logger.warning(
                "Veeam jobs relay skipped: no SSH target for host %s", hostname
            )
            return []

        sql = (
            "SELECT regexp_replace(js.job_name, ' - [A-Za-z0-9._]+$', '') AS job_name, "
            "COUNT(*) AS session_count, "
            "COALESCE(SUM(bs.total_size), 0), "
            "COALESCE(SUM(bs.processed_size), 0), "
            "COALESCE(SUM(bs.read_size), 0), "
            "COALESCE(SUM(bs.stored_size), 0), "
            "COALESCE(AVG(bs.avg_speed), 0), "
            "MAX(js.creation_time) AS last_run, "
            "SUM(CASE WHEN js.result = 0 THEN 1 ELSE 0 END) AS success_count, "
            "SUM(CASE WHEN js.result = 1 THEN 1 ELSE 0 END) AS warning_count, "
            "SUM(CASE WHEN js.result = 2 THEN 1 ELSE 0 END) AS failed_count "
            'FROM "backup.model.jobsessions" js '
            'LEFT JOIN "backup.model.backupjobsessions" bs ON bs.id = js.id '
            "WHERE js.job_name NOT LIKE '%Resynchronize%' "
            "AND js.job_name NOT LIKE '%Host Discovery%' "
            "AND js.job_name NOT LIKE '%Foreign transform%' "
            "AND js.job_name NOT LIKE '%Infrastructure update%' "
            "AND js.job_name NOT LIKE '%Audit Logs%' "
            "AND js.job_name NOT LIKE '%Catalog Cleanup%' "
            "AND js.job_name NOT LIKE '%Shell run%' "
            "AND js.job_name NOT LIKE '%Backup Configuration%' "
            "AND js.job_name NOT LIKE '%Hyper-V CBT%' "
            "AND js.job_name NOT LIKE '%Rescan%' "
            "AND js.job_name NOT LIKE '%Checkpoint Removal%' "
            "AND js.job_name NOT LIKE '%Retention job%' "
            "AND js.job_name NOT LIKE '%Malware Detection%' "
            "GROUP BY 1 "
            "ORDER BY MAX(js.creation_time) DESC"
        )
        psql = r"C:\Program Files\PostgreSQL\15\bin\psql.exe"
        ps_script = (
            f"& '{psql}' -h 127.0.0.1 -U postgres -d VeeamBackup -t -A -c \"{sql}\""
        )
        encoded = self._encode_powershell(ps_script)
        ps_command = f"powershell -NoProfile -NonInteractive -EncodedCommand {encoded}"
        logger.info("Veeam DB relay via SSH target %s", target_id)
        result = await remote_manager.execute_on_target(
            target_id=target_id,
            command=ps_command,
            timeout=120,
        )
        if not result.get("success"):
            logger.error("Veeam DB relay failed: stderr=%s", result.get("stderr", ""))
            return []
        return self._parse_db_rows(result.get("stdout", "")) or []

    @staticmethod
    def _encode_powershell(script: str) -> str:
        """Encode a PowerShell script as base64 UTF-16LE for -EncodedCommand."""
        import base64

        encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
        return encoded

    def _parse_db_rows(self, raw: str) -> list[dict[str, Any]]:
        rows = []
        if not raw:
            return rows
        for line in raw.splitlines():
            cols = line.split("|")
            if len(cols) < 9:
                continue
            rows.append(
                {
                    "job_name": cols[0].strip(),
                    "session_count": int(cols[1].strip() or 0),
                    "processed_bytes": int(cols[2].strip() or 0),
                    "read_bytes": int(cols[3].strip() or 0),
                    "stored_bytes": int(cols[4].strip() or 0),
                    "avg_speed": float(cols[5].strip() or 0),
                    "last_run": cols[6].strip() or None,
                    "success_count": int(cols[7].strip() or 0),
                    "warning_count": int(cols[8].strip() or 0),
                    "failed_count": int(cols[9].strip() or 0) if len(cols) > 9 else 0,
                }
            )
        return rows

    # ------------------------------------------------------------------
    # Shared collectors
    # ------------------------------------------------------------------

    async def _run_collector(self, collector: str) -> Any:
        prefix = "Import-Module Veeam.Backup.PowerShell -ErrorAction SilentlyContinue; "

        if collector == "jobs":
            ps1 = [
                "Import-Module Veeam.Backup.PowerShell -ErrorAction SilentlyContinue",
                "$jobsOut = @()",
                "Get-VBRJob | ForEach-Object {",
                "  $j = $_",
                "  $lastRunTime = $null",
                "  $lastResult = 'Unknown'",
                "  try {",
                "    $lastRun = $j.GetLastRun()",
                "    if ($lastRun) {",
                "      $lastRunTime = $lastRun.CreationTime.ToString('o')",
                "      $lastResult = $lastRun.Result.ToString()",
                "    }",
                "  } catch {",
                "    $lastRunTime = $null",
                "    $lastResult = 'Unknown'",
                "  }",
                "  $objectsInJob = 0",
                "  try {",
                "    if ($j.Info -and $j.Info.LinkedObjects) { $objectsInJob = $j.Info.LinkedObjects.Count }",
                "  } catch { $objectsInJob = 0 }",
                "  $schedule = $null",
                "  if ($j.ScheduleOptions -and $j.ScheduleOptions.Enabled) {",
                "    $schedule = @{ kind = 'periodic' }",
                "  }",
                "  $lastRunBlock = $null",
                "  if ($lastRunTime) {",
                "    $lastRunBlock = @{",
                "      state = $lastResult",
                "      result = @{ result = $lastResult }",
                "      creationTime = $lastRunTime",
                "      progressPercent = 0",
                "    }",
                "  }",
                "  $jobsOut += @{",
                "    id = $j.Id.ToString()",
                "    name = $j.Name",
                "    type = $j.JobType.ToString()",
                "    state = if ($j.IsRunning) { 'Running' } else { 'Stopped' }",
                "    enabled = $j.Options.Enabled",
                "    schedule = $schedule",
                "    lastRun = $lastRunBlock",
                "    includedObjects = @{ objectsInJob = $objectsInJob }",
                "  }",
                "}",
                "$jobsOut | ConvertTo-Json -Depth 3 -Compress",
                "",
            ]
            script = "\r\n".join(ps1)
            result = await self._run_script_file(script, timeout=90)
            if not result["success"]:
                logger.error(
                    "Veeam local PowerShell jobs collector failed: stderr=%s",
                    result.get("stderr", ""),
                )
                return []
            stdout = (result.get("stdout") or "").strip()
            if not stdout:
                logger.error(
                    "Veeam local PowerShell jobs collector returned empty stdout"
                )
                return []
            jobs = self._parse_json_array(stdout)
            logger.info(
                "Veeam local PowerShell jobs collector returned %d jobs", len(jobs)
            )
            if len(jobs) == 0:
                logger.warning(
                    "Local jobs collector returned 0 jobs, trying SSH relay fallback"
                )
                relay_jobs = await self._collect_jobs_via_relay()
                if relay_jobs:
                    logger.info(
                        "Veeam SSH relay jobs collector returned %d jobs",
                        len(relay_jobs),
                    )
                    return relay_jobs
            return jobs

        if collector == "sessions":
            script = (
                prefix + "Get-VBRSession -Last 200 | ForEach-Object { "
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
                prefix + "Get-VBRBackupRepository | ForEach-Object { "
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
                prefix + "Get-VBRServer | ForEach-Object { "
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
                prefix + "$ver = (Get-Module Veeam.Backup.PowerShell).Version; "
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
