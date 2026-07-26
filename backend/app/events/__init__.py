"""
Mission Control Event Bus

Internal pub/sub system for decoupled component communication.
All cross-component communication flows through events rather than
direct method calls.

Usage:
    from app.events import event_bus, Event

    # Publish an event
    await event_bus.publish(Event(
        type=EventType.HEARTBEAT_RECEIVED,
        data={"agent_id": 1, "health": "healthy"}
    ))

    # Subscribe to events
    @event_bus.on(EventType.HEARTBEAT_RECEIVED)
    async def handle_heartbeat(event: Event):
        ...
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class EventType(StrEnum):
    """All event types in the system."""

    # Agent lifecycle
    AGENT_REGISTERED = "agent.registered"
    AGENT_ENABLED = "agent.enabled"
    AGENT_DISABLED = "agent.disabled"
    AGENT_REMOVED = "agent.removed"

    # Heartbeat
    HEARTBEAT_RECEIVED = "heartbeat.received"
    AGENT_ONLINE = "agent.online"
    AGENT_OFFLINE = "agent.offline"
    AGENT_HEALTH_CHANGED = "agent.health_changed"

    # Inventory
    INVENTORY_UPDATED = "inventory.updated"
    REMOTE_INVENTORY_UPDATED = "inventory.remote_updated"

    # Commands
    COMMAND_QUEUED = "command.queued"
    COMMAND_DISPATCHED = "command.dispatched"
    COMMAND_COMPLETED = "command.completed"
    COMMAND_FAILED = "command.failed"

    # Plugin lifecycle
    PLUGIN_INSTALLED = "plugin.installed"
    PLUGIN_REMOVED = "plugin.removed"
    PLUGIN_ENABLED = "plugin.enabled"
    PLUGIN_DISABLED = "plugin.disabled"
    PLUGIN_HEALTH_CHANGED = "plugin.health_changed"

    # Automation
    AUTOMATION_STARTED = "automation.started"
    AUTOMATION_COMPLETED = "automation.completed"
    AUTOMATION_FAILED = "automation.failed"
    PLAYBOOK_EXECUTED = "playbook.executed"
    APPROVAL_REQUESTED = "approval.requested"

    # Infrastructure
    BACKUP_SUCCEEDED = "backup.succeeded"
    BACKUP_FAILED = "backup.failed"
    ALERT_CREATED = "alert.created"
    ALERT_RESOLVED = "alert.resolved"

    # Integration
    INTEGRATION_CONNECTED = "integration.connected"
    INTEGRATION_DISCONNECTED = "integration.disconnected"
    INTEGRATION_ERROR = "integration.error"

    # System
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    MIGRATION_COMPLETED = "migration.completed"


@dataclass
class Event:
    """An event published to the bus."""

    type: EventType
    data: dict[str, Any] = field(default_factory=dict)
    source: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


# Type alias for event handlers
EventHandler = Callable[[Event], Coroutine[Any, Any, None]]


class EventBus:
    """In-process async event bus for decoupled communication."""

    def __init__(self) -> None:
        self._handlers: dict[EventType, list[EventHandler]] = {}
        self._history: list[Event] = []
        self._max_history = 100

    def on(self, event_type: EventType) -> Callable[[EventHandler], EventHandler]:
        """Decorator to register an event handler."""

        def decorator(handler: EventHandler) -> EventHandler:
            self._handlers.setdefault(event_type, []).append(handler)
            return handler

        return decorator

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Register a handler for an event type."""
        self._handlers.setdefault(event_type, []).append(handler)

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Remove a handler for an event type."""
        handlers = self._handlers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)

    async def publish(self, event: Event) -> None:
        """Publish an event to all subscribed handlers."""
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        handlers = self._handlers.get(event.type, [])
        if not handlers:
            return

        logger.debug(
            "Event published: %s (source=%s, handlers=%d)",
            event.type.value,
            event.source,
            len(handlers),
        )

        for handler in handlers:
            try:
                await handler(event)
            except Exception:
                logger.exception(
                    "Event handler failed for %s in %s",
                    event.type.value,
                    handler.__qualname__,
                )

    def get_history(self, event_type: EventType | None = None, limit: int = 50) -> list[Event]:
        """Return recent events, optionally filtered by type."""
        events = self._history
        if event_type:
            events = [e for e in events if e.type == event_type]
        return events[-limit:]

    def clear(self) -> None:
        """Clear all handlers and history (for testing)."""
        self._handlers.clear()
        self._history.clear()


# Global singleton
event_bus = EventBus()
