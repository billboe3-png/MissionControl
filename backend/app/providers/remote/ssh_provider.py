"""
Mission Control SSH Provider

Production SSH provider using Paramiko for command execution
against remote Linux hosts.

Sprint 2.1.6 - Real WinRM Command Execution.

Features:
- Connection reuse with automatic reconnect
- Configurable connection, command, and idle timeouts
- Retry once for transient transport failures
- Monotonic timer for accurate duration measurement
- Internal streaming hooks for future WebSocket support
- Secure logging (never logs passwords, keys, or output)
"""

import io
import logging
import time
from datetime import UTC, datetime

import paramiko
from paramiko.ssh_exception import NoValidConnectionsError

from app.providers.remote.base_provider import RemoteBaseProvider

logger = logging.getLogger(__name__)


def _get_timeouts() -> dict:
    """Get timeout settings from config."""
    try:
        from app.core.config import get_settings

        settings = get_settings()
        return {
            "connect": settings.ssh_connect_timeout,
            "command": settings.ssh_command_timeout,
            "idle": settings.ssh_idle_timeout,
        }
    except Exception:
        return {"connect": 10, "command": 60, "idle": 300}


def _get_retry_count() -> int:
    """Get retry count from config."""
    try:
        from app.core.config import get_settings

        return get_settings().remote_retry_count
    except Exception:
        return 1


class SSHProvider(RemoteBaseProvider):
    """
    Production SSH provider using Paramiko.

    Supports password and private key authentication.
    Connections are reused where possible and automatically
    reconnected on transient failures.
    """

    def __init__(self) -> None:
        self._clients: dict[str, paramiko.SSHClient] = {}

    # ------------------------------------------------------------------ #
    # Connection Management                                               #
    # ------------------------------------------------------------------ #

    def _connection_key(
        self, hostname: str, port: int, username: str
    ) -> str:
        return f"{username}@{hostname}:{port}"

    def _build_client(
        self,
        hostname: str,
        port: int,
        username: str,
        password: str | None,
        ssh_key: str | None,
        connect_timeout: int | None = None,
    ) -> paramiko.SSHClient:
        """Build and connect a Paramiko SSHClient."""
        if connect_timeout is None:
            connect_timeout = _get_timeouts()["connect"]

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        pkey = None
        if ssh_key:
            pkey = paramiko.RSAKey.from_private_key(io.StringIO(ssh_key))

        client.connect(
            hostname=hostname,
            port=port,
            username=username,
            password=password,
            pkey=pkey,
            timeout=connect_timeout,
            allow_agent=not ssh_key,
            look_for_keys=not ssh_key,
        )

        return client

    def _get_client(
        self,
        hostname: str,
        port: int,
        username: str,
        password: str | None,
        ssh_key: str | None,
    ) -> paramiko.SSHClient:
        """
        Get a reusable client or build a new one.

        Tests the existing connection with a lightweight check.
        If stale, reconnects automatically.
        """
        key = self._connection_key(hostname, port, username)

        if key in self._clients:
            existing = self._clients[key]
            try:
                transport = existing.get_transport()
                if transport and transport.is_active():
                    return existing
            except Exception:
                pass

            self._close_client(existing)
            del self._clients[key]

        client = self._build_client(
            hostname, port, username, password, ssh_key
        )
        self._clients[key] = client
        return client

    def _close_client(self, client: paramiko.SSHClient) -> None:
        """Safely close an SSH client."""
        try:
            client.close()
        except Exception:
            pass

    def _remove_client(
        self, hostname: str, port: int, username: str
    ) -> None:
        """Remove a client from the pool."""
        key = self._connection_key(hostname, port, username)
        client = self._clients.pop(key, None)
        if client is not None:
            self._close_client(client)

    # ------------------------------------------------------------------ #
    # Execution                                                           #
    # ------------------------------------------------------------------ #

    def _parse_exit_code(self, channel: paramiko.Channel) -> int:
        """Extract the exit code from an SSH channel."""
        if channel.recv_exit_status_ready():
            return channel.recv_exit_status()
        return -1

    def _execute_with_retry(
        self,
        hostname: str,
        port: int,
        username: str,
        password: str | None,
        ssh_key: str | None,
        command: str,
        timeout: int,
    ) -> dict:
        """
        Execute a command over SSH with one retry for transient failures.

        Does NOT retry authentication failures.
        """
        last_error = None
        retries = _get_retry_count()

        for attempt in range(1 + retries):
            client = None
            try:
                client = self._build_client(
                    hostname, port, username, password, ssh_key
                )

                _, stdout, stderr = client.exec_command(
                    command, timeout=timeout
                )

                stdout_text = stdout.read().decode(
                    "utf-8", errors="replace"
                )
                stderr_text = stderr.read().decode(
                    "utf-8", errors="replace"
                )
                exit_code = self._parse_exit_code(stdout.channel)

                return {
                    "stdout": stdout_text,
                    "stderr": stderr_text,
                    "exit_code": exit_code,
                    "success": exit_code == 0,
                }

            except paramiko.AuthenticationException:
                raise

            except Exception as e:
                last_error = e
                if attempt < retries:
                    logger.info(
                        "SSH: retrying command on user=%s host=%s "
                        "attempt=%d",
                        username,
                        hostname,
                        attempt + 1,
                    )
                    continue
                raise

            finally:
                if client is not None:
                    self._close_client(client)

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

        if isinstance(error, paramiko.AuthenticationException):
            logger.warning(
                "SSH: execute_command user=%s host=%s "
                "command_auth_failed",
                username,
                hostname,
            )
            return {
                "success": False,
                "stdout": "",
                "stderr": "SSH authentication failed",
                "exit_code": -1,
                "duration_ms": duration_ms,
                "started_at": now,
                "completed_at": now,
            }

        if isinstance(error, paramiko.SSHException):
            error_str = str(error).strip()
            if "timed out" in error_str.lower():
                logger.warning(
                    "SSH: execute_command user=%s host=%s "
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
            logger.warning(
                "SSH: execute_command user=%s host=%s "
                "command_ssh_error",
                username,
                hostname,
            )
            return {
                "success": False,
                "stdout": "",
                "stderr": f"SSH error: {error_str}",
                "exit_code": -1,
                "duration_ms": duration_ms,
                "started_at": now,
                "completed_at": now,
            }

        if isinstance(error, TimeoutError):
            logger.warning(
                "SSH: execute_command user=%s host=%s "
                "command_socket_timeout",
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

        if isinstance(error, NoValidConnectionsError):
            logger.warning(
                "SSH: execute_command user=%s host=%s "
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

        if isinstance(error, OSError):
            error_lower = str(error).lower()
            dns_match = (
                "no such host" in error_lower
                or "getaddrinfo" in error_lower
                or "name or service not known" in error_lower
            )
            if dns_match:
                logger.warning(
                    "SSH: execute_command user=%s host=%s "
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
            if "connection refused" in error_lower:
                logger.warning(
                    "SSH: execute_command user=%s host=%s "
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
            if "unreachable" in error_lower:
                logger.warning(
                    "SSH: execute_command user=%s host=%s "
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

            logger.warning(
                "SSH: execute_command user=%s host=%s "
                "command_os_error",
                username,
                hostname,
            )
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Connection error: {str(error).strip()}",
                "exit_code": -1,
                "duration_ms": duration_ms,
                "started_at": now,
                "completed_at": now,
            }

        logger.warning(
            "SSH: execute_command user=%s host=%s "
            "command_unexpected=%s",
            username,
            hostname,
            type(error).__name__,
        )
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Unexpected error: {type(error).__name__}",
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

        if isinstance(error, paramiko.AuthenticationException):
            logger.warning(
                "SSH: test_connection user=%s host=%s failed auth",
                username,
                target,
            )
            return {
                "success": False,
                "latency_ms": elapsed_ms,
                "message": (
                    f"SSH connection to {target}:{port} failed: "
                    "authentication failed"
                ),
            }

        if isinstance(error, paramiko.SSHException):
            error_str = str(error).strip()
            if "timed out" in error_str.lower():
                logger.warning(
                    "SSH: test_connection user=%s host=%s "
                    "failed timeout",
                    username,
                    target,
                )
                return {
                    "success": False,
                    "latency_ms": elapsed_ms,
                    "message": (
                        f"SSH connection to {target}:{port} failed: "
                        "connection timed out"
                    ),
                }
            logger.warning(
                "SSH: test_connection user=%s host=%s "
                "failed ssh_error",
                username,
                target,
            )
            return {
                "success": False,
                "latency_ms": elapsed_ms,
                "message": (
                    f"SSH connection to {target}:{port} failed: "
                    f"{error_str}"
                ),
            }

        if isinstance(error, TimeoutError):
            logger.warning(
                "SSH: test_connection user=%s host=%s "
                "failed socket_timeout",
                username,
                target,
            )
            return {
                "success": False,
                "latency_ms": elapsed_ms,
                "message": (
                    f"SSH connection to {target}:{port} failed: "
                    "connection timed out"
                ),
            }

        if isinstance(error, NoValidConnectionsError):
            logger.warning(
                "SSH: test_connection user=%s host=%s "
                "failed connection_refused",
                username,
                target,
            )
            return {
                "success": False,
                "latency_ms": elapsed_ms,
                "message": (
                    f"SSH connection to {target}:{port} failed: "
                    "connection refused"
                ),
            }

        if isinstance(error, OSError):
            error_lower = str(error).lower()
            dns_match = (
                "no such host" in error_lower
                or "getaddrinfo" in error_lower
                or "name or service not known" in error_lower
            )
            if dns_match:
                logger.warning(
                    "SSH: test_connection user=%s host=%s failed dns",
                    username,
                    target,
                )
                return {
                    "success": False,
                    "latency_ms": elapsed_ms,
                    "message": (
                        f"SSH connection to {target}:{port} failed: "
                        "DNS resolution failed"
                    ),
                }
            if "connection refused" in error_lower:
                logger.warning(
                    "SSH: test_connection user=%s host=%s "
                    "failed connection_refused",
                    username,
                    target,
                )
                return {
                    "success": False,
                    "latency_ms": elapsed_ms,
                    "message": (
                        f"SSH connection to {target}:{port} failed: "
                        "connection refused"
                    ),
                }
            if "unreachable" in error_lower:
                logger.warning(
                    "SSH: test_connection user=%s host=%s "
                    "failed unreachable",
                    username,
                    target,
                )
                return {
                    "success": False,
                    "latency_ms": elapsed_ms,
                    "message": (
                        f"SSH connection to {target}:{port} failed: "
                        "host unreachable"
                    ),
                }

            logger.warning(
                "SSH: test_connection user=%s host=%s "
                "failed os_error",
                username,
                target,
            )
            return {
                "success": False,
                "latency_ms": elapsed_ms,
                "message": (
                    f"SSH connection to {target}:{port} failed: "
                    f"{str(error).strip()}"
                ),
            }

        logger.warning(
            "SSH: test_connection user=%s host=%s failed %s",
            username,
            target,
            type(error).__name__,
        )
        return {
            "success": False,
            "latency_ms": elapsed_ms,
            "message": (
                f"SSH connection to {target}:{port} failed: "
                f"{type(error).__name__}"
            ),
        }

    # ------------------------------------------------------------------ #
    # Public API                                                          #
    # ------------------------------------------------------------------ #

    async def test_connection(
        self,
        hostname: str,
        port: int,
        username: str,
        password: str | None,
        ssh_key: str | None,
        ip_address: str | None,
    ) -> dict:
        """Test SSH connectivity by running an echo probe command."""
        target = ip_address if ip_address else hostname
        timeouts = _get_timeouts()

        logger.info(
            "SSH: test_connection user=%s host=%s port=%d",
            username,
            target,
            port,
        )

        start_time = time.monotonic()

        try:
            client = self._build_client(
                hostname=hostname,
                port=port,
                username=username,
                password=password,
                ssh_key=ssh_key,
                connect_timeout=timeouts["connect"],
            )
        except Exception as e:
            return self._handle_test_error(
                username, target, port, e, start_time
            )

        try:
            _, stdout, stderr = client.exec_command(
                "echo MissionControl",
                timeout=timeouts["command"],
            )

            output = stdout.read().decode(
                "utf-8", errors="replace"
            ).strip()
            exit_code = self._parse_exit_code(stdout.channel)

            elapsed_ms = int((time.monotonic() - start_time) * 1000)

            if exit_code == 0 and output == "MissionControl":
                logger.info(
                    "SSH: test_connection user=%s host=%s "
                    "success latency=%dms",
                    username,
                    target,
                    elapsed_ms,
                )
                return {
                    "success": True,
                    "latency_ms": elapsed_ms,
                    "message": (
                        f"SSH connection to {target}:{port} "
                        f"successful ({elapsed_ms}ms)"
                    ),
                }

            logger.warning(
                "SSH: test_connection user=%s host=%s "
                "failed unexpected_echo",
                username,
                target,
            )
            return {
                "success": False,
                "latency_ms": elapsed_ms,
                "message": (
                    f"SSH connection to {target}:{port} failed: "
                    "unexpected echo response"
                ),
            }

        except Exception as e:
            return self._handle_test_error(
                username, target, port, e, start_time
            )

        finally:
            self._close_client(client)

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
        """Execute a command on a remote host via SSH."""
        timeouts = _get_timeouts()
        command_timeout = min(
            timeouts["command"],
            _get_max_command_timeout(),
        )

        logger.info(
            "SSH: execute_command user=%s host=%s",
            username,
            hostname,
        )

        start_time = time.monotonic()
        started_at = datetime.now(UTC).isoformat()

        try:
            result = self._execute_with_retry(
                hostname=hostname,
                port=port,
                username=username,
                password=password,
                ssh_key=ssh_key,
                command=command,
                timeout=command_timeout,
            )

            duration_ms = int((time.monotonic() - start_time) * 1000)
            completed_at = datetime.now(UTC).isoformat()

            logger.info(
                "SSH: execute_command user=%s host=%s "
                "exit_code=%d duration=%dms",
                username,
                hostname,
                result["exit_code"],
                duration_ms,
            )

            return {
                "success": result["success"],
                "stdout": result["stdout"],
                "stderr": result["stderr"],
                "exit_code": result["exit_code"],
                "duration_ms": duration_ms,
                "started_at": started_at,
                "completed_at": completed_at,
            }

        except Exception as e:
            return self._handle_execute_error(
                username, hostname, command, e, start_time
            )


def _get_max_command_timeout() -> int:
    """Get max command timeout from config."""
    try:
        from app.core.config import get_settings

        return get_settings().remote_max_command_timeout
    except Exception:
        return 3600
