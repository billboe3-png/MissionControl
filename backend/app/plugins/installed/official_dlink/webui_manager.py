"""
D-Link DGS-1210 Web UI Session Manager

Manages HTTP-over-WebSocket tunnels for D-Link switch web interface access.
Same pattern as MikroTik WebFig relay.
"""
import asyncio
import base64
import logging
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger("plugin.dlink.webui")


@dataclass
class WebUISession:
    """Single Web UI proxy session."""
    session_id: str
    switch_id: int
    agent_id: int
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    status: str = "connecting"
    input_queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    output_buffer: List[bytes] = field(default_factory=list)
    error: Optional[str] = None

    def send_input(self, data: str) -> None:
        """Queue base64-encoded input from browser."""
        self.input_queue.put_nowait(data)
        self.last_activity = datetime.utcnow()

    def get_input(self) -> List[str]:
        """Get all queued input chunks."""
        chunks = []
        while not self.input_queue.empty():
            try:
                chunks.append(self.input_queue.get_nowait())
            except asyncio.QueueEmpty:
                break
        return chunks

    def add_output(self, chunk: bytes) -> None:
        """Add output chunk from agent."""
        self.output_buffer.append(chunk)
        self.last_activity = datetime.utcnow()

    def read_output(self) -> List[bytes]:
        """Read and clear output buffer."""
        chunks = self.output_buffer
        self.output_buffer = []
        return chunks

    def close(self) -> None:
        self.status = "closed"

    def set_error(self, error: str) -> None:
        self.error = error
        self.status = "error"


class WebUIManager:
    """Manages Web UI sessions for D-Link switches."""

    def __init__(self):
        self._sessions: Dict[str, WebUISession] = {}
        self._cleanup_task: Optional[asyncio.Task] = None

    def create_session(self, switch_id: int, agent_id: int) -> str:
        """Create a new Web UI session."""
        session_id = f"dlink-webui-{switch_id}-{uuid.uuid4().hex[:12]}"
        session = WebUISession(
            session_id=session_id,
            switch_id=switch_id,
            agent_id=agent_id
        )
        self._sessions[session_id] = session
        logger.info(f"Created D-Link Web UI session: {session_id}")
        return session_id

    def get_session(self, session_id: str) -> Optional[WebUISession]:
        """Get session by ID."""
        return self._sessions.get(session_id)

    def close_session(self, session_id: str) -> None:
        """Close and remove a session."""
        session = self._sessions.pop(session_id, None)
        if session:
            session.close()
            logger.info(f"Closed D-Link Web UI session: {session_id}")

    def apply_agent_update(
        self,
        agent_id: int,
        session_id: str,
        output_b64: str,
        status: Optional[str] = None,
        error: str = ""
    ) -> Dict[str, Any]:
        """Apply update from agent (called via edge agent webui/io endpoint)."""
        session = self._sessions.get(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}

        if output_b64:
            try:
                session.add_output(base64.b64decode(output_b64))
            except Exception as e:
                logger.warning(f"Failed to decode agent output: {e}")

        if status:
            session.status = status
        if error:
            session.set_error(error)

        return {"success": True, "input": session.get_input()}

    def get_pending_input(self, session_id: str) -> List[str]:
        """Get pending input for agent to send to switch."""
        session = self._sessions.get(session_id)
        if not session:
            return []
        return session.get_input()

    async def start_cleanup_task(self):
        """Start background task to clean up stale sessions."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def _cleanup_loop(self):
        while True:
            await asyncio.sleep(60)
            now = datetime.utcnow()
            stale = [
                sid for sid, s in self._sessions.items()
                if (now - s.last_activity).total_seconds() > 300
            ]
            for sid in stale:
                logger.info(f"Cleaning up stale Web UI session: {sid}")
                self.close_session(sid)


# Singleton instance
webui_manager = WebUIManager()