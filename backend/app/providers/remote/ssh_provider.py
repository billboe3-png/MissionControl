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

import contextlib
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
        # Secure by default: reject unknown hosts (mitigates MITM). Only
        # auto-accept when the operator has explicitly opted in via
        # SSH_AUTO_ADD_HOST_KEYS for trusted single-purpose hosts.
        from app.core.config import get_settings

        if get_settings().ssh_auto_add_host_keys:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        else:
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.RejectPolicy())

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
            with contextlib.suppress(Exception):
                transport = existing.get_transport()
                if transport and transport.is_active():
                    return existing

            self._close_client(existing)
            del self._clients[key]

        client = self._build_client(
            hostname, port, username, password, ssh_key
        )
        self._clients[key] = client
        return client

    def _close_client(self, client: paramiko.SSHClient) -> None:
        """Safely close an SSH client."""
        with contextlib.suppress(Exception):
            client.close()

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
        if channel.exit_status_ready():
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
                hostname=target,
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
            _, stdout, _stderr = client.exec_command(
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
        target = ip_address if ip_address else hostname
        timeouts = _get_timeouts()
        command_timeout = min(
            timeouts["command"],
            _get_max_command_timeout(),
        )

        logger.info(
            "SSH: execute_command user=%s host=%s",
            username,
            target,
        )

        start_time = time.monotonic()
        started_at = datetime.now(UTC).isoformat()

        try:
            result = self._execute_with_retry(
                hostname=target,
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
                target,
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
                username, target, command, e, start_time
            )

    async def execute_command_stream(
        self,
        hostname: str,
        port: int,
        username: str,
        password: str | None,
        ssh_key: str | None,
        command: str,
        shell: str,
        ip_address: str | None,
    ):
        """Execute a command and yield output chunks in real-time."""
        import asyncio
        import queue
        import threading
        target = ip_address if ip_address else hostname
        timeouts = _get_timeouts()
        min(timeouts["command"], _get_max_command_timeout())

        q: queue.Queue = queue.Queue()
        cancel_event = threading.Event()

        def _reader():
            import time
            client = None
            try:
                client = self._build_client(target, port, username, password, ssh_key)
                chan = client.invoke_shell(term="xterm", width=200, height=50)
                time.sleep(0.5)

                while chan.recv_ready():
                    chan.recv(4096)

                chan.send(command + "\n")

                sudo_handled = False
                while not cancel_event.is_set():
                    if chan.recv_ready():
                        data = chan.recv(4096).decode("utf-8", errors="replace")

                        if (
                            not sudo_handled
                            and password
                            and "[sudo] password" in data.lower()
                        ):
                            sudo_handled = True
                            chan.send(password + "\n")
                            continue

                        q.put(("stdout", data))

                    if chan.recv_stderr_ready():
                        data = chan.recv_stderr(4096).decode("utf-8", errors="replace")
                        q.put(("stderr", data))

                    if chan.exit_status_ready():
                        while chan.recv_ready():
                            q.put(("stdout", chan.recv(4096).decode("utf-8", errors="replace")))
                        while chan.recv_stderr_ready():
                            q.put(("stderr", chan.recv_stderr(4096).decode("utf-8", errors="replace")))
                        break

                    time.sleep(0.1)

                if cancel_event.is_set():
                    with contextlib.suppress(Exception):
                        chan.send_exit_status(130)
                        chan.close()
                    q.put(("exit", 130))
                    return

                exit_code = chan.recv_exit_status()
                q.put(("exit", exit_code))
            except Exception as e:
                q.put(("error", str(e)))
            finally:
                if client is not None:
                    self._close_client(client)
                q.put(None)

        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, _reader)

        try:
            while True:
                item = await asyncio.get_event_loop().run_in_executor(None, q.get)
                if item is None:
                    break
                kind, value = item
                if kind == "exit":
                    yield {"type": "exit", "exit_code": value}
                elif kind == "error":
                    yield {"type": "error", "message": value}
                else:
                    yield {"type": kind, "data": value}
        except asyncio.CancelledError:
            cancel_event.set()
            yield {"type": "error", "message": "Command cancelled"}

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
        """Upload a file to the remote host via SFTP."""
        target = ip_address if ip_address else hostname
        logger.info(
            "SSH: upload_file user=%s host=%s path=%s",
            username, target, remote_path,
        )
        client = None
        try:
            client = self._build_client(
                target, port, username, password, ssh_key
            )
            return _ssh_upload_file(client, remote_path, content)
        except Exception as e:
            logger.warning(
                "SSH: upload_file user=%s host=%s error=%s",
                username, target, type(e).__name__,
            )
            return {
                "success": False,
                "message": f"Upload failed: {e}",
                "remote_path": remote_path,
            }
        finally:
            if client:
                self._close_client(client)

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
        """Download a file from the remote host via SFTP."""
        target = ip_address if ip_address else hostname
        logger.info(
            "SSH: download_file user=%s host=%s path=%s",
            username, target, remote_path,
        )
        client = None
        try:
            client = self._build_client(
                target, port, username, password, ssh_key
            )
            return _ssh_download_file(client, remote_path)
        except Exception as e:
            logger.warning(
                "SSH: download_file user=%s host=%s error=%s",
                username, target, type(e).__name__,
            )
            return {
                "success": False,
                "message": f"Download failed: {e}",
                "remote_path": remote_path,
            }
        finally:
            if client:
                self._close_client(client)

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
        """List contents of a remote directory via SFTP."""
        target = ip_address if ip_address else hostname
        logger.info(
            "SSH: list_directory user=%s host=%s path=%s",
            username, target, remote_path,
        )
        client = None
        try:
            client = self._build_client(
                target, port, username, password, ssh_key
            )
            return _ssh_list_directory(client, remote_path)
        except Exception as e:
            logger.warning(
                "SSH: list_directory user=%s host=%s error=%s",
                username, target, type(e).__name__,
            )
            return {
                "success": False,
                "message": f"List failed: {e}",
                "path": remote_path,
                "items": [],
            }
        finally:
            if client:
                self._close_client(client)

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
        """Create a directory on the remote host via SFTP."""
        target = ip_address if ip_address else hostname
        logger.info(
            "SSH: create_directory user=%s host=%s path=%s",
            username, target, remote_path,
        )
        client = None
        try:
            client = self._build_client(
                target, port, username, password, ssh_key
            )
            return _ssh_create_directory(client, remote_path)
        except Exception as e:
            logger.warning(
                "SSH: create_directory user=%s host=%s error=%s",
                username, target, type(e).__name__,
            )
            return {
                "success": False,
                "message": f"Mkdir failed: {e}",
                "remote_path": remote_path,
            }
        finally:
            if client:
                self._close_client(client)

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
        """Delete a file on the remote host via SFTP."""
        target = ip_address if ip_address else hostname
        logger.info(
            "SSH: delete_file user=%s host=%s path=%s",
            username, target, remote_path,
        )
        client = None
        try:
            client = self._build_client(
                target, port, username, password, ssh_key
            )
            return _ssh_delete_file(client, remote_path)
        except Exception as e:
            logger.warning(
                "SSH: delete_file user=%s host=%s error=%s",
                username, target, type(e).__name__,
            )
            return {
                "success": False,
                "message": f"Delete failed: {e}",
                "remote_path": remote_path,
            }
        finally:
            if client:
                self._close_client(client)


def _get_max_command_timeout() -> int:
    """Get max command timeout from config."""
    try:
        from app.core.config import get_settings

        return get_settings().remote_max_command_timeout
    except Exception:
        return 3600


# ------------------------------------------------------------------ #
# File Transfer Methods (added to SSHProvider below)                  #
# ------------------------------------------------------------------ #

import stat  # noqa: E402


def _ssh_upload_file(
    client: paramiko.SSHClient,
    remote_path: str,
    content: bytes,
) -> dict:
    """Upload bytes to a remote file via SFTP."""
    sftp = client.open_sftp()
    try:
        with sftp.open(remote_path, "w") as f:
            f.write(content.decode("utf-8", errors="replace"))
        return {
            "success": True,
            "message": f"File uploaded to {remote_path}",
            "remote_path": remote_path,
            "size_bytes": len(content),
        }
    finally:
        sftp.close()


def _ssh_download_file(
    client: paramiko.SSHClient,
    remote_path: str,
) -> dict:
    """Download a remote file via SFTP."""
    sftp = client.open_sftp()
    try:
        with sftp.open(remote_path, "r") as f:
            content = f.read()
        return {
            "success": True,
            "message": f"File downloaded from {remote_path}",
            "remote_path": remote_path,
            "content": content,
            "size_bytes": len(content),
        }
    finally:
        sftp.close()


def _ssh_list_directory(
    client: paramiko.SSHClient,
    remote_path: str,
) -> dict:
    """List contents of a remote directory via SFTP."""
    sftp = client.open_sftp()
    try:
        entries = []
        for item in sftp.listdir_attr(remote_path):
            full_path = f"{remote_path.rstrip('/')}/{item.filename}"
            is_dir = stat.S_ISDIR(item.st_mode)
            entries.append({
                "name": item.filename,
                "path": full_path,
                "is_directory": is_dir,
                "size_bytes": item.st_size if not is_dir else None,
                "modified_at": str(item.st_mtime) if item.st_mtime else None,
                "permissions": oct(item.st_mode)[-3:],
            })
        entries.sort(key=lambda x: (not x["is_directory"], x["name"]))
        return {
            "success": True,
            "path": remote_path,
            "items": entries,
        }
    finally:
        sftp.close()


def _ssh_create_directory(
    client: paramiko.SSHClient,
    remote_path: str,
) -> dict:
    """Create a directory on the remote host via SFTP."""
    sftp = client.open_sftp()
    try:
        sftp.mkdir(remote_path)
        return {
            "success": True,
            "message": f"Directory created: {remote_path}",
            "remote_path": remote_path,
        }
    finally:
        sftp.close()


def _ssh_delete_file(
    client: paramiko.SSHClient,
    remote_path: str,
) -> dict:
    """Delete a file on the remote host via SFTP."""
    sftp = client.open_sftp()
    try:
        sftp.remove(remote_path)
        return {
            "success": True,
            "message": f"File deleted: {remote_path}",
            "remote_path": remote_path,
        }
    finally:
        sftp.close()
