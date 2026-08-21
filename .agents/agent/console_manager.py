"""Mission Control Agent - Interactive console relay.

Persistent SSH PTY sessions to remote targets, streamed through the
Mission Control backend via a lightweight piggyback I/O endpoint. The
agent owns the PTY; the backend only buffers bytes between the browser
WebSocket and the agent's 1-second I/O posts.
"""

import logging
import threading
import time
from typing import Any

import httpx

logger = logging.getLogger("mc-agent")

IO_INTERVAL = 1.0


class ConsoleSession:
    """One PTY session to a remote target, relayed via the backend."""

    def __init__(
        self,
        session_id: str,
        agent_id: int,
        base_url: str,
        api_key: str,
        verify_ssl: bool,
        target: dict[str, Any] | None,
        width: int,
        height: int,
    ):
        self.session_id = session_id
        self.agent_id = agent_id
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.verify_ssl = verify_ssl
        self.target = target
        self.width = max(20, int(width or 120))
        self.height = max(5, int(height or 40))

        self.client: Any = None
        self.chan: Any = None
        self._lock = threading.Lock()
        self._pending_out: list[str] = []
        self.status = "connecting"  # connecting | connected | error | exited
        self.error = ""
        self.exit_code: int | None = None
        self.stop = False

    def start(self) -> None:
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self) -> None:
        try:
            self._connect()
        except Exception as e:
            with self._lock:
                self.status = "error"
                self.error = str(e)
            logger.warning("Console %s connect failed: %s", self.session_id, e)
            self._io_loop(report_only=True)
            return
        threading.Thread(target=self._read_loop, daemon=True).start()
        self._io_loop()
        self._shutdown()

    def _connect(self) -> None:
        if not self.target:
            raise RuntimeError("Unknown console target for this agent")
        import paramiko

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        kwargs: dict[str, Any] = {
            "hostname": self.target.get("hostname"),
            "port": int(self.target.get("port") or 22),
            "username": self.target.get("username"),
            "timeout": 12,
            "allow_agent": False,
            "look_for_keys": False,
        }
        ssh_key = self.target.get("ssh_key")
        if ssh_key:
            import io

            key_file = io.StringIO(ssh_key)
            pkey = None
            for key_cls in (
                paramiko.Ed25519Key,
                paramiko.ECDSAKey,
                paramiko.RSAKey,
            ):
                try:
                    pkey = key_cls.from_private_key(key_file)
                    break
                except Exception:
                    key_file.seek(0)
            if pkey is None:
                raise RuntimeError("Could not parse stored SSH key")
            kwargs["pkey"] = pkey
        elif self.target.get("password"):
            kwargs["password"] = self.target.get("password")
        else:
            raise RuntimeError("Target has no credentials")

        client.connect(**kwargs)
        chan = client.invoke_shell(
            term="xterm-256color", width=self.width, height=self.height
        )
        chan.settimeout(0.0)
        self.client = client
        self.chan = chan
        with self._lock:
            self.status = "connected"
        logger.info(
            "Console %s connected to %s",
            self.session_id,
            self.target.get("hostname"),
        )

    def _read_loop(self) -> None:
        while not self.stop:
            try:
                if self.chan.recv_ready():
                    data = self.chan.recv(8192).decode("utf-8", errors="replace")
                    if data:
                        with self._lock:
                            self._pending_out.append(data)
                elif self.chan.closed or self.chan.exit_status_ready():
                    while self.chan.recv_ready():
                        data = self.chan.recv(8192).decode(
                            "utf-8", errors="replace"
                        )
                        with self._lock:
                            self._pending_out.append(data)
                    with self._lock:
                        self.status = "exited"
                        try:
                            self.exit_code = self.chan.recv_exit_status()
                        except Exception:
                            self.exit_code = 0
                    break
                else:
                    time.sleep(0.05)
            except Exception:
                with self._lock:
                    self.status = "exited"
                    self.exit_code = -1
                break

    def _io_loop(self, report_only: bool = False) -> None:
        """Post output / receive input until closed or exited."""
        url = f"{self.base_url}/api/v1/edge/{self.agent_id}/console/io"
        headers = {"X-Agent-API-Key": self.api_key}
        while not self.stop:
            with self._lock:
                out = "".join(self._pending_out)
                self._pending_out = []
                status = self.status if self.status != "connecting" else None
                error = self.error
                exit_code = self.exit_code
            body: dict[str, Any] = {"session_id": self.session_id, "output": out}
            if status:
                body.update(
                    {"status": status, "error": error, "exit_code": exit_code}
                )
            confirmed_terminal = False
            try:
                resp = httpx.post(
                    url,
                    json=body,
                    headers=headers,
                    verify=self.verify_ssl,
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if report_only:
                        return
                    for chunk in data.get("input") or []:
                        try:
                            self.chan.sendall(chunk.encode("utf-8"))
                        except Exception:
                            pass
                    resize = data.get("resize")
                    if resize and self.chan:
                        try:
                            self.chan.resize_pty(
                                width=int(resize.get("width", self.width)),
                                height=int(resize.get("height", self.height)),
                            )
                        except Exception:
                            pass
                    if data.get("closed"):
                        break
                    if status == "exited":
                        confirmed_terminal = True
                else:
                    with self._lock:
                        self._pending_out.insert(0, out)
            except Exception:
                with self._lock:
                    self._pending_out.insert(0, out)
            if confirmed_terminal:
                # Terminal state already delivered; keep draining briefly so
                # trailing output reaches the browser, then stop.
                deadline = time.time() + 2.0
                while time.time() < deadline and not self.stop:
                    with self._lock:
                        trail = "".join(self._pending_out)
                        self._pending_out = []
                    if trail:
                        try:
                            httpx.post(
                                url,
                                json={
                                    "session_id": self.session_id,
                                    "output": trail,
                                    "status": "exited",
                                    "exit_code": exit_code,
                                },
                                headers=headers,
                                verify=self.verify_ssl,
                                timeout=10.0,
                            )
                        except Exception:
                            pass
                    time.sleep(0.2)
                break
            time.sleep(IO_INTERVAL)
        self.stop = True

    def _shutdown(self) -> None:
        try:
            if self.chan:
                self.chan.close()
        except Exception:
            pass
        try:
            if self.client:
                self.client.close()
        except Exception:
            pass


class ConsoleRelay:
    """Registry of active console sessions on this agent."""

    def __init__(self):
        self._sessions: dict[str, ConsoleSession] = {}

    def start_session(
        self,
        session_id: str,
        agent_id: int,
        base_url: str,
        api_key: str,
        verify_ssl: bool,
        targets: list[dict],
        hostname: str,
        width: int,
        height: int,
    ) -> None:
        target = next(
            (t for t in targets if t.get("hostname") == hostname), None
        )
        session = ConsoleSession(
            session_id=session_id,
            agent_id=agent_id,
            base_url=base_url,
            api_key=api_key,
            verify_ssl=verify_ssl,
            target=target,
            width=width,
            height=height,
        )
        self._sessions[session_id] = session
        session.start()

    def active_count(self) -> int:
        return sum(1 for s in self._sessions.values() if not s.stop)
