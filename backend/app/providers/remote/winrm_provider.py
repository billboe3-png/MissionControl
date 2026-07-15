"""
Mission Control WinRM Provider

Production WinRM provider using pywinrm for command execution
against remote Windows hosts.

Sprint 2.1.6 - Real WinRM Command Execution.

Supports:
- NTLM authentication
- Basic authentication
- HTTPS with certificate validation options
- SSL/TLS error classification
- Configurable timeouts
- Retry for transient failures
- Secure logging
"""

import logging
import time
from datetime import UTC, datetime

import winrm

from app.providers.remote.base_provider import RemoteBaseProvider

logger = logging.getLogger(__name__)


def _get_timeouts() -> dict:
    """Get WinRM timeout settings from config."""
    try:
        from app.core.config import get_settings

        settings = get_settings()
        return {
            "connect": settings.winrm_connect_timeout,
            "operation": settings.winrm_operation_timeout,
        }
    except Exception:
        return {"connect": 10, "operation": 60}


def _get_retry_count() -> int:
    """Get retry count from config."""
    try:
        from app.core.config import get_settings

        return get_settings().remote_retry_count
    except Exception:
        return 1


def _get_max_command_timeout() -> int:
    """Get max command timeout from config."""
    try:
        from app.core.config import get_settings

        return get_settings().remote_max_command_timeout
    except Exception:
        return 3600


class WinRMProvider(RemoteBaseProvider):
    """
    Production WinRM provider using pywinrm.

    Supports NTLM, Basic, and HTTPS transport with
    configurable certificate validation.
    """

    def _build_session(
        self,
        hostname: str,
        port: int,
        username: str,
        password: str | None,
        transport: str = "ntlm",
        https: bool = False,
        cert_validation: bool = True,
    ) -> winrm.Session:
        """
        Build a pywinrm Session.

        Args:
            hostname: Target host
            port: WinRM port
            username: Authentication username
            password: Authentication password
            transport: Auth transport (ntlm, basic, kerberos)
            https: Use HTTPS instead of HTTP
            cert_validation: Validate SSL certificates
        """
        scheme = "https" if https else "http"
        endpoint = f"{scheme}://{hostname}:{port}/wsman"

        session_kwargs: dict = {
            "endpoint": endpoint,
            "auth": (username, password) if password else (username, None),
            "transport": transport,
            "server_cert_validation": "validate" if cert_validation else "ignore",
            "read_timeout": _get_timeouts()["operation"],
            "operation_timeout_sec": _get_timeouts()["operation"],
        }

        return winrm.Session(**session_kwargs)

    def _execute_with_retry(
        self,
        session: winrm.Session,
        command: str,
        retries: int,
    ) -> winrm.Response:
        """
        Execute a command with retry for transient failures.

        Does NOT retry authentication failures.
        """
        last_error = None

        for attempt in range(1 + retries):
            try:
                result = session.run_cmd(command)
                return result

            except winrm.exceptions.WinRMError as e:
                error_str = str(e).lower()

                if "401" in error_str or "unauthorized" in error_str:
                    raise

                last_error = e
                if attempt < retries:
                    logger.info(
                        "WinRM: retrying command attempt=%d",
                        attempt + 1,
                    )
                    continue
                raise

        raise last_error  # type: ignore[misc]

    def _handle_execute_error(
        self,
        username: str,
        hostname: str,
        command: str,
        error: Exception,
        start_time: float,
    ) -> dict:
        """Format an error response for execute_command failures."""
        duration_ms = int((time.monotonic() - start_time) * 1000)
        now = datetime.now(UTC).isoformat()

        error_str = str(error).lower()

        if "401" in error_str or "unauthorized" in error_str:
            logger.warning(
                "WinRM: execute_command user=%s host=%s "
                "command_auth_failed",
                username,
                hostname,
            )
            return {
                "success": False,
                "stdout": "",
                "stderr": "WinRM authentication failed",
                "exit_code": -1,
                "duration_ms": duration_ms,
                "started_at": now,
                "completed_at": now,
            }

        if "timed out" in error_str or "timeout" in error_str:
            logger.warning(
                "WinRM: execute_command user=%s host=%s "
                "command_timeout",
                username,
                hostname,
            )
            return {
                "success": False,
                "stdout": "",
                "stderr": "Command execution timed out",
                "exit_code": -1,
                "duration_ms": duration_ms,
                "started_at": now,
                "completed_at": now,
            }

        if "connection refused" in error_str:
            logger.warning(
                "WinRM: execute_command user=%s host=%s "
                "command_refused",
                username,
                hostname,
            )
            return {
                "success": False,
                "stdout": "",
                "stderr": "Connection refused",
                "exit_code": -1,
                "duration_ms": duration_ms,
                "started_at": now,
                "completed_at": now,
            }

        if "name or service not known" in error_str or "getaddrinfo" in error_str:
            logger.warning(
                "WinRM: execute_command user=%s host=%s "
                "command_dns_failure",
                username,
                hostname,
            )
            return {
                "success": False,
                "stdout": "",
                "stderr": "DNS resolution failed",
                "exit_code": -1,
                "duration_ms": duration_ms,
                "started_at": now,
                "completed_at": now,
            }

        if "unreachable" in error_str:
            logger.warning(
                "WinRM: execute_command user=%s host=%s "
                "command_unreachable",
                username,
                hostname,
            )
            return {
                "success": False,
                "stdout": "",
                "stderr": "Host unreachable",
                "exit_code": -1,
                "duration_ms": duration_ms,
                "started_at": now,
                "completed_at": now,
            }

        if "ssl" in error_str or "certificate" in error_str:
            logger.warning(
                "WinRM: execute_command user=%s host=%s "
                "command_ssl_failure",
                username,
                hostname,
            )
            return {
                "success": False,
                "stdout": "",
                "stderr": "SSL/TLS handshake failed",
                "exit_code": -1,
                "duration_ms": duration_ms,
                "started_at": now,
                "completed_at": now,
            }

        logger.warning(
            "WinRM: execute_command user=%s host=%s "
            "command_error=%s",
            username,
            hostname,
            type(error).__name__,
        )
        return {
            "success": False,
            "stdout": "",
            "stderr": f"WinRM error: {str(error).strip()}",
            "exit_code": -1,
            "duration_ms": duration_ms,
            "started_at": now,
            "completed_at": now,
        }

    def _handle_test_error(
        self,
        username: str,
        target: str,
        port: int,
        error: Exception,
        start_time: float,
    ) -> dict:
        """Format an error response for test_connection failures."""
        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        error_str = str(error).lower()

        if "401" in error_str or "unauthorized" in error_str:
            logger.warning(
                "WinRM: test_connection user=%s host=%s failed auth",
                username,
                target,
            )
            return {
                "success": False,
                "latency_ms": elapsed_ms,
                "message": (
                    f"WinRM connection to {target}:{port} failed: "
                    "authentication failed"
                ),
            }

        if "timed out" in error_str or "timeout" in error_str:
            logger.warning(
                "WinRM: test_connection user=%s host=%s "
                "failed timeout",
                username,
                target,
            )
            return {
                "success": False,
                "latency_ms": elapsed_ms,
                "message": (
                    f"WinRM connection to {target}:{port} failed: "
                    "connection timed out"
                ),
            }

        if "connection refused" in error_str:
            logger.warning(
                "WinRM: test_connection user=%s host=%s "
                "failed connection_refused",
                username,
                target,
            )
            return {
                "success": False,
                "latency_ms": elapsed_ms,
                "message": (
                    f"WinRM connection to {target}:{port} failed: "
                    "connection refused"
                ),
            }

        if "name or service not known" in error_str or "getaddrinfo" in error_str:
            logger.warning(
                "WinRM: test_connection user=%s host=%s failed dns",
                username,
                target,
            )
            return {
                "success": False,
                "latency_ms": elapsed_ms,
                "message": (
                    f"WinRM connection to {target}:{port} failed: "
                    "DNS resolution failed"
                ),
            }

        if "unreachable" in error_str:
            logger.warning(
                "WinRM: test_connection user=%s host=%s "
                "failed unreachable",
                username,
                target,
            )
            return {
                "success": False,
                "latency_ms": elapsed_ms,
                "message": (
                    f"WinRM connection to {target}:{port} failed: "
                    "host unreachable"
                ),
            }

        if "ssl" in error_str or "certificate" in error_str:
            logger.warning(
                "WinRM: test_connection user=%s host=%s "
                "failed ssl",
                username,
                target,
            )
            return {
                "success": False,
                "latency_ms": elapsed_ms,
                "message": (
                    f"WinRM connection to {target}:{port} failed: "
                    "SSL/TLS handshake failed"
                ),
            }

        logger.warning(
            "WinRM: test_connection user=%s host=%s failed %s",
            username,
            target,
            type(error).__name__,
        )
        return {
            "success": False,
            "latency_ms": elapsed_ms,
            "message": (
                f"WinRM connection to {target}:{port} failed: "
                f"{type(error).__name__}"
            ),
        }

    async def test_connection(
        self,
        hostname: str,
        port: int,
        username: str,
        password: str | None,
        ssh_key: str | None,
        ip_address: str | None,
    ) -> dict:
        """Test WinRM connectivity by running a probe command."""
        target = ip_address if ip_address else hostname

        logger.info(
            "WinRM: test_connection user=%s host=%s port=%d",
            username,
            target,
            port,
        )

        start_time = time.monotonic()

        try:
            session = self._build_session(
                hostname=target,
                port=port,
                username=username,
                password=password,
            )

            result = session.run_cmd("echo MissionControl")

            elapsed_ms = int((time.monotonic() - start_time) * 1000)

            stdout = (
                result.std_out.decode("utf-8", errors="replace")
                if isinstance(result.std_out, bytes)
                else result.std_out
            )

            if result.status_code == 0 and "MissionControl" in stdout:
                logger.info(
                    "WinRM: test_connection user=%s host=%s "
                    "success latency=%dms",
                    username,
                    target,
                    elapsed_ms,
                )
                return {
                    "success": True,
                    "latency_ms": elapsed_ms,
                    "message": (
                        f"WinRM connection to {target}:{port} "
                        f"successful ({elapsed_ms}ms)"
                    ),
                }

            logger.warning(
                "WinRM: test_connection user=%s host=%s "
                "failed unexpected_response",
                username,
                target,
            )
            return {
                "success": False,
                "latency_ms": elapsed_ms,
                "message": (
                    f"WinRM connection to {target}:{port} failed: "
                    "unexpected response"
                ),
            }

        except Exception as e:
            return self._handle_test_error(
                username, target, port, e, start_time
            )

    async def execute_command(
        self,
        hostname: str,
        port: int,
        username: str,
        password: str | None,
        ssh_key: str | None,
        command: str,
        shell: str,
        ip_address: str | None,
    ) -> dict:
        """Execute a command on a remote host via WinRM."""
        target = ip_address if ip_address else hostname
        retries = _get_retry_count()

        logger.info(
            "WinRM: execute_command user=%s host=%s",
            username,
            target,
        )

        start_time = time.monotonic()
        started_at = datetime.now(UTC).isoformat()

        try:
            session = self._build_session(
                hostname=target,
                port=port,
                username=username,
                password=password,
            )

            result = self._execute_with_retry(session, command, retries)

            duration_ms = int((time.monotonic() - start_time) * 1000)
            completed_at = datetime.now(UTC).isoformat()

            stdout_text = result.std_out or ""
            stderr_text = result.std_err or ""

            if isinstance(stdout_text, bytes):
                stdout_text = stdout_text.decode(
                    "utf-8", errors="replace"
                )
            if isinstance(stderr_text, bytes):
                stderr_text = stderr_text.decode(
                    "utf-8", errors="replace"
                )

            exit_code = result.status_code

            logger.info(
                "WinRM: execute_command user=%s host=%s "
                "exit_code=%d duration=%dms",
                username,
                target,
                exit_code,
                duration_ms,
            )

            return {
                "success": exit_code == 0,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "exit_code": exit_code,
                "duration_ms": duration_ms,
                "started_at": started_at,
                "completed_at": completed_at,
            }

        except Exception as e:
            return self._handle_execute_error(
                username, target, command, e, start_time
            )

    # ------------------------------------------------------------------ #
    # File Transfer                                                       #
    # ------------------------------------------------------------------ #

    async def upload_file(
        self,
        hostname: str,
        port: int,
        username: str,
        password: str | None,
        ssh_key: str | None,
        remote_path: str,
        content: bytes,
        ip_address: str | None,
    ) -> dict:
        """Upload a file to a Windows host via WinRM shell."""
        target = ip_address if ip_address else hostname
        logger.info(
            "WinRM: upload_file user=%s host=%s path=%s",
            username, target, remote_path,
        )
        try:
            session = self._build_session(
                hostname=target, port=port,
                username=username, password=password,
            )
            import base64 as b64
            encoded = b64.b64encode(content).decode("ascii")
            ps_cmd = (
                f"$data = [Convert]::FromBase64String('{encoded}'); "
                f"[System.IO.File]::WriteAllBytes('{remote_path}', $data)"
            )
            result = session.run_cmd(f"powershell -Command \"{ps_cmd}\"")
            if result.status_code == 0:
                return {
                    "success": True,
                    "message": f"File uploaded to {remote_path}",
                    "remote_path": remote_path,
                    "size_bytes": len(content),
                }
            stderr = result.std_err or ""
            if isinstance(stderr, bytes):
                stderr = stderr.decode("utf-8", errors="replace")
            return {
                "success": False,
                "message": f"Upload failed: {stderr}",
                "remote_path": remote_path,
            }
        except Exception as e:
            logger.warning(
                "WinRM: upload_file user=%s host=%s error=%s",
                username, target, type(e).__name__,
            )
            return {
                "success": False,
                "message": f"Upload failed: {e}",
                "remote_path": remote_path,
            }

    async def download_file(
        self,
        hostname: str,
        port: int,
        username: str,
        password: str | None,
        ssh_key: str | None,
        remote_path: str,
        ip_address: str | None,
    ) -> dict:
        """Download a file from a Windows host via WinRM shell."""
        target = ip_address if ip_address else hostname
        logger.info(
            "WinRM: download_file user=%s host=%s path=%s",
            username, target, remote_path,
        )
        try:
            session = self._build_session(
                hostname=target, port=port,
                username=username, password=password,
            )
            ps_cmd = (
                f"$data = [System.IO.File]::ReadAllBytes('{remote_path}'); "
                f"[Convert]::ToBase64String($data)"
            )
            result = session.run_cmd(f"powershell -Command \"{ps_cmd}\"")
            stdout = result.std_out or ""
            if isinstance(stdout, bytes):
                stdout = stdout.decode("utf-8", errors="replace")
            if result.status_code == 0 and stdout.strip():
                import base64 as b64
                content = b64.b64decode(stdout.strip())
                return {
                    "success": True,
                    "message": f"File downloaded from {remote_path}",
                    "remote_path": remote_path,
                    "content": content,
                    "size_bytes": len(content),
                }
            stderr = result.std_err or ""
            if isinstance(stderr, bytes):
                stderr = stderr.decode("utf-8", errors="replace")
            return {
                "success": False,
                "message": f"Download failed: {stderr}",
                "remote_path": remote_path,
            }
        except Exception as e:
            logger.warning(
                "WinRM: download_file user=%s host=%s error=%s",
                username, target, type(e).__name__,
            )
            return {
                "success": False,
                "message": f"Download failed: {e}",
                "remote_path": remote_path,
            }

    async def list_directory(
        self,
        hostname: str,
        port: int,
        username: str,
        password: str | None,
        ssh_key: str | None,
        remote_path: str,
        ip_address: str | None,
    ) -> dict:
        """List contents of a remote directory via WinRM."""
        target = ip_address if ip_address else hostname
        logger.info(
            "WinRM: list_directory user=%s host=%s path=%s",
            username, target, remote_path,
        )
        try:
            session = self._build_session(
                hostname=target, port=port,
                username=username, password=password,
            )
            ps_cmd = (
                f"Get-ChildItem '{remote_path}' | "
                f"Select-Object Name,FullName,PSIsContainer,"
                f"Length,LastWriteTime | ConvertTo-Json"
            )
            result = session.run_cmd(f"powershell -Command \"{ps_cmd}\"")
            stdout = result.std_out or ""
            if isinstance(stdout, bytes):
                stdout = stdout.decode("utf-8", errors="replace")
            if result.status_code == 0 and stdout.strip():
                import json
                data = json.loads(stdout.strip())
                if isinstance(data, dict):
                    data = [data]
                items = []
                for entry in data:
                    items.append({
                        "name": entry.get("Name", ""),
                        "path": entry.get("FullName", ""),
                        "is_directory": entry.get("PSIsContainer", False),
                        "size_bytes": entry.get("Length"),
                        "modified_at": str(entry.get("LastWriteTime", "")),
                        "permissions": None,
                    })
                items.sort(key=lambda x: (not x["is_directory"], x["name"]))
                return {
                    "success": True,
                    "path": remote_path,
                    "items": items,
                }
            return {
                "success": True,
                "path": remote_path,
                "items": [],
            }
        except Exception as e:
            logger.warning(
                "WinRM: list_directory user=%s host=%s error=%s",
                username, target, type(e).__name__,
            )
            return {
                "success": False,
                "message": f"List failed: {e}",
                "path": remote_path,
                "items": [],
            }

    async def create_directory(
        self,
        hostname: str,
        port: int,
        username: str,
        password: str | None,
        ssh_key: str | None,
        remote_path: str,
        ip_address: str | None,
    ) -> dict:
        """Create a directory on a Windows host via WinRM."""
        target = ip_address if ip_address else hostname
        logger.info(
            "WinRM: create_directory user=%s host=%s path=%s",
            username, target, remote_path,
        )
        try:
            session = self._build_session(
                hostname=target, port=port,
                username=username, password=password,
            )
            result = session.run_cmd(
                f'powershell -Command "New-Item -ItemType Directory -Path \'{remote_path}\' -Force"'
            )
            if result.status_code == 0:
                return {
                    "success": True,
                    "message": f"Directory created: {remote_path}",
                    "remote_path": remote_path,
                }
            stderr = result.std_err or ""
            if isinstance(stderr, bytes):
                stderr = stderr.decode("utf-8", errors="replace")
            return {
                "success": False,
                "message": f"Mkdir failed: {stderr}",
                "remote_path": remote_path,
            }
        except Exception as e:
            logger.warning(
                "WinRM: create_directory user=%s host=%s error=%s",
                username, target, type(e).__name__,
            )
            return {
                "success": False,
                "message": f"Mkdir failed: {e}",
                "remote_path": remote_path,
            }

    async def delete_file(
        self,
        hostname: str,
        port: int,
        username: str,
        password: str | None,
        ssh_key: str | None,
        remote_path: str,
        ip_address: str | None,
    ) -> dict:
        """Delete a file on a Windows host via WinRM."""
        target = ip_address if ip_address else hostname
        logger.info(
            "WinRM: delete_file user=%s host=%s path=%s",
            username, target, remote_path,
        )
        try:
            session = self._build_session(
                hostname=target, port=port,
                username=username, password=password,
            )
            result = session.run_cmd(
                f'powershell -Command "Remove-Item \'{remote_path}\' -Force"'
            )
            if result.status_code == 0:
                return {
                    "success": True,
                    "message": f"File deleted: {remote_path}",
                    "remote_path": remote_path,
                }
            stderr = result.std_err or ""
            if isinstance(stderr, bytes):
                stderr = stderr.decode("utf-8", errors="replace")
            return {
                "success": False,
                "message": f"Delete failed: {stderr}",
                "remote_path": remote_path,
            }
        except Exception as e:
            logger.warning(
                "WinRM: delete_file user=%s host=%s error=%s",
                username, target, type(e).__name__,
            )
            return {
                "success": False,
                "message": f"Delete failed: {e}",
                "remote_path": remote_path,
            }
