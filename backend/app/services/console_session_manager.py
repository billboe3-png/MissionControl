"""In-memory registry for agent-relayed interactive console sessions.

The browser talks to a WebSocket on ``/remote/console-agent``; the edge
agent streams PTY bytes through the piggyback ``/edge/{id}/console/io``
endpoint. This manager is the meeting point. Nothing is persisted —
sessions die with the worker process, which is the desired lifetime for
interactive shells.
"""

from __future__ import annotations

import threading
import time
import uuid


class ConsoleSession:
    """State for one relayed console session."""

    def __init__(self, session_id: str, agent_id: int, host_id: int, hostname: str):
        self.session_id = session_id
        self.agent_id = agent_id
        self.host_id = host_id
        self.hostname = hostname
        self.status = "pending"  # pending | connected | error | closed
        self.error = ""
        self.exit_code: int | None = None
        self.buffer = ""
        self.input_queue: list[str] = []
        self.pending_resize: dict | None = None
        self.close_requested = False
        self.created_at = time.time()
        self.last_activity = time.time()

    def touch(self) -> None:
        self.last_activity = time.time()


class ConsoleSessionManager:
    """Process-global registry of console sessions and pending start ops."""

    STALE_AFTER = 180.0  # seconds without activity before auto-close
    PRUNE_AFTER = 600.0  # seconds to keep finished sessions around

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._sessions: dict[str, ConsoleSession] = {}
        self._pending_ops: dict[int, list[dict]] = {}

    # ------------------------------------------------------------------
    # Lifecycle (browser side)
    # ------------------------------------------------------------------

    def create_session(
        self,
        agent_id: int,
        host_id: int,
        hostname: str,
        width: int = 120,
        height: int = 40,
    ) -> ConsoleSession:
        session_id = uuid.uuid4().hex[:16]
        session = ConsoleSession(session_id, agent_id, host_id, hostname)
        with self._lock:
            self._sweep_locked()
            self._sessions[session_id] = session
            self._pending_ops.setdefault(agent_id, []).append(
                {
                    "session_id": session_id,
                    "hostname": hostname,
                    "width": width,
                    "height": height,
                }
            )
        return session

    def get_session(self, session_id: str) -> ConsoleSession | None:
        with self._lock:
            return self._sessions.get(session_id)

    # ------------------------------------------------------------------
    # Commands poll (agent side)
    # ------------------------------------------------------------------

    def drain_pending_ops(self, agent_id: int) -> list[dict]:
        with self._lock:
            return self._pending_ops.pop(agent_id, [])

    # ------------------------------------------------------------------
    # I/O endpoint (agent side)
    # ------------------------------------------------------------------

    def apply_agent_update(
        self,
        agent_id: int,
        session_id: str,
        output: str = "",
        status: str | None = None,
        error: str = "",
        exit_code: int | None = None,
    ) -> dict:
        """Store PTY output/status; return queued input for the agent."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None or session.agent_id != agent_id:
                return {"closed": True, "input": [], "resize": None}
            session.touch()
            if output:
                session.buffer += output
            if status == "connected" and session.status in (
                "pending",
                "connected",
            ):
                session.status = "connected"
                session.error = ""
            elif status == "error":
                session.status = "error"
                session.error = error or "console failed"
            elif status == "exited":
                session.status = "closed"
                session.exit_code = exit_code
            reply = {
                "input": session.input_queue,
                "resize": session.pending_resize,
                "closed": session.close_requested
                or session.status in ("error", "closed"),
            }
            session.input_queue = []
            session.pending_resize = None
            return reply

    # ------------------------------------------------------------------
    # WebSocket bridge (browser side)
    # ------------------------------------------------------------------

    def read_output(self, session_id: str, cursor: int) -> tuple[str, int]:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None or len(session.buffer) <= cursor:
                return "", cursor
            return session.buffer[cursor:], len(session.buffer)

    def send_input(self, session_id: str, data: str) -> None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is not None:
                session.touch()
                session.input_queue.append(data)

    def request_resize(self, session_id: str, width: int, height: int) -> None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is not None:
                session.touch()
                session.pending_resize = {"width": width, "height": height}

    def request_close(self, session_id: str) -> None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is not None:
                session.close_requested = True

    # ------------------------------------------------------------------
    # Housekeeping
    # ------------------------------------------------------------------

    def _sweep_locked(self) -> None:
        now = time.time()
        for sid, session in list(self._sessions.items()):
            if session.status in ("error", "closed"):
                if now - session.last_activity > self.PRUNE_AFTER:
                    del self._sessions[sid]
                continue
            if now - session.last_activity > self.STALE_AFTER:
                session.status = "closed"
                session.error = "session timed out"
                session.close_requested = True


# Module-level singleton shared by routers.
manager = ConsoleSessionManager()
