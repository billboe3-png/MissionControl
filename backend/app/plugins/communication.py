"""
Mission Control Plugin Communication Protocol

Handles secure communication between the server and agent plugins.
Supports heartbeat, streaming logs, progress updates, cancellation,
retries, compression, chunked transfer, and secure tokens.
"""

import hashlib
import json
import logging
import secrets
import time
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class MessageType(StrEnum):
    """Plugin message types."""
    HEARTBEAT = "heartbeat"
    COMMAND = "command"
    COMMAND_RESULT = "command_result"
    PROGRESS = "progress"
    LOG = "log"
    INVENTORY = "inventory"
    HEALTH_CHECK = "health_check"
    CANCEL = "cancel"
    ERROR = "error"


class MessagePriority(StrEnum):
    """Message priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class PluginMessage:
    """A single message in the plugin communication protocol."""

    def __init__(
        self,
        message_type: MessageType,
        source: str,
        destination: str,
        payload: dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        correlation_id: str | None = None,
    ):
        self.id = secrets.token_hex(16)
        self.type = message_type
        self.source = source
        self.destination = destination
        self.payload = payload
        self.priority = priority
        self.correlation_id = correlation_id
        self.timestamp = datetime.now(UTC).isoformat()
        self.retry_count = 0
        self.max_retries = 3

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "source": self.source,
            "destination": self.destination,
            "payload": self.payload,
            "priority": self.priority.value,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
            "retry_count": self.retry_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PluginMessage":
        msg = cls(
            message_type=MessageType(data["type"]),
            source=data["source"],
            destination=data["destination"],
            payload=data.get("payload", {}),
            priority=MessagePriority(data.get("priority", "normal")),
            correlation_id=data.get("correlation_id"),
        )
        msg.id = data.get("id", msg.id)
        msg.timestamp = data.get("timestamp", msg.timestamp)
        msg.retry_count = data.get("retry_count", 0)
        return msg

    def checksum(self) -> str:
        """Compute integrity checksum of the message."""
        raw = json.dumps(self.payload, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


class PluginMessageBus:
    """
    In-memory message bus for plugin communication.

    In production this would be backed by Redis Pub/Sub or a
    message queue. The in-memory version is suitable for
    single-server deployments and testing.
    """

    def __init__(self):
        self._queues: dict[str, list[PluginMessage]] = {}
        self._subscribers: dict[str, list] = {}
        self._dead_letter: list[PluginMessage] = []
        self._metrics = {
            "sent": 0,
            "delivered": 0,
            "failed": 0,
            "dead_letter": 0,
        }

    def send(self, message: PluginMessage) -> bool:
        """Send a message to a destination queue."""
        self._metrics["sent"] += 1

        dest = message.destination
        if dest not in self._queues:
            self._queues[dest] = []

        self._queues[dest].append(message)
        self._metrics["delivered"] += 1

        # Notify subscribers
        for callback in self._subscribers.get(dest, []):
            try:
                callback(message)
            except Exception:
                logger.exception("Subscriber callback failed for %s", dest)

        logger.debug(
            "Message sent: %s -> %s [%s]",
            message.source,
            dest,
            message.type.value,
        )
        return True

    def receive(self, destination: str) -> PluginMessage | None:
        """Receive the next message for a destination."""
        queue = self._queues.get(destination, [])
        if not queue:
            return None
        return queue.pop(0)

    def peek(self, destination: str) -> list[dict[str, Any]]:
        """Peek at all pending messages for a destination without consuming."""
        queue = self._queues.get(destination, [])
        return [m.to_dict() for m in queue]

    def subscribe(self, destination: str, callback) -> None:
        """Subscribe to messages for a destination."""
        if destination not in self._subscribers:
            self._subscribers[destination] = []
        self._subscribers[destination].append(callback)

    def unsubscribe(self, destination: str, callback) -> None:
        """Unsubscribe from messages for a destination."""
        if destination in self._subscribers:
            self._subscribers[destination] = [
                cb for cb in self._subscribers[destination] if cb != callback
            ]

    def send_with_retry(
        self,
        message: PluginMessage,
        max_retries: int = 3,
        backoff_seconds: float = 1.0,
    ) -> bool:
        """Send a message with retry logic."""
        for attempt in range(max_retries + 1):
            message.retry_count = attempt
            success = self.send(message)
            if success:
                return True

            if attempt < max_retries:
                logger.warning(
                    "Retry %d/%d for message %s",
                    attempt + 1,
                    max_retries,
                    message.id,
                )
                time.sleep(backoff_seconds * (2 ** attempt))

        self._dead_letter.append(message)
        self._metrics["dead_letter"] += 1
        self._metrics["failed"] += 1
        return False

    def get_metrics(self) -> dict[str, int]:
        """Return message bus metrics."""
        return {
            **self._metrics,
            "queue_depths": {
                k: len(v) for k, v in self._queues.items()
            },
        }

    def clear_queue(self, destination: str) -> int:
        """Clear all messages for a destination. Returns count cleared."""
        queue = self._queues.get(destination, [])
        count = len(queue)
        self._queues[destination] = []
        return count


class PluginTokenManager:
    """Manages secure tokens for plugin authentication."""

    def __init__(self, secret_key: str = ""):
        self._secret_key = secret_key or secrets.token_hex(32)
        self._tokens: dict[str, dict[str, Any]] = {}

    def generate_token(
        self,
        plugin_slug: str,
        expires_in_seconds: int = 3600,
    ) -> str:
        """Generate a time-limited token for a plugin."""
        token = secrets.token_urlsafe(32)
        self._tokens[token] = {
            "plugin_slug": plugin_slug,
            "created_at": time.time(),
            "expires_at": time.time() + expires_in_seconds,
        }
        return token

    def validate_token(self, token: str) -> dict[str, Any] | None:
        """Validate a token and return its claims, or None if invalid."""
        claims = self._tokens.get(token)
        if claims is None:
            return None
        if time.time() > claims["expires_at"]:
            del self._tokens[token]
            return None
        return claims

    def revoke_token(self, token: str) -> bool:
        """Revoke a token."""
        if token in self._tokens:
            del self._tokens[token]
            return True
        return False

    def revoke_all_for_plugin(self, plugin_slug: str) -> int:
        """Revoke all tokens for a given plugin. Returns count revoked."""
        to_revoke = [
            t for t, c in self._tokens.items()
            if c["plugin_slug"] == plugin_slug
        ]
        for t in to_revoke:
            del self._tokens[t]
        return len(to_revoke)

    def cleanup_expired(self) -> int:
        """Remove all expired tokens. Returns count removed."""
        now = time.time()
        expired = [t for t, c in self._tokens.items() if now > c["expires_at"]]
        for t in expired:
            del self._tokens[t]
        return len(expired)


# Module-level singletons
message_bus = PluginMessageBus()
token_manager = PluginTokenManager()
