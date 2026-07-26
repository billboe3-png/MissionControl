# Mission Control — Event Bus

**Version:** 3.0.0

---

## Overview

The Event Bus is an in-process async pub/sub system for decoupled component communication. All cross-component communication flows through events rather than direct method calls.

---

## 1. Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Event Bus                         │
│  Path: backend/app/events/__init__.py               │
│-----------------------------------------------------│
│                                                      │
│  Publishers              Subscribers                 │
│  ──────────              ───────────                 │
│  Heartbeat Service  ──>  Agent State Engine          │
│  Agent Service      ──>  Dashboard Service           │
│  Automation Service ──>  Notification Service        │
│  Plugin Loader      ──>  Audit Trail                 │
│  Remote Service     ──>  AI Operations               │
│                                                      │
│  Event History (last 100 events)                     │
│  ─────────────────────────────────                   │
│  [Event, Event, Event, ...]                          │
└─────────────────────────────────────────────────────┘
```

---

## 2. Event Types

34 typed events across 8 categories.

### Agent Lifecycle

| Event | Trigger |
|-------|---------|
| `agent.registered` | New agent registers with server |
| `agent.enabled` | Agent is administratively enabled |
| `agent.disabled` | Agent is administratively disabled |
| `agent.removed` | Agent is deleted from server |

### Heartbeat

| Event | Trigger |
|-------|---------|
| `heartbeat.received` | Heartbeat processed successfully |
| `agent.online` | Agent transitions to online state |
| `agent.offline` | Agent transitions to offline state |
| `agent.health_changed` | Agent health status changes |

### Inventory

| Event | Trigger |
|-------|---------|
| `inventory.updated` | Agent inventory data received |
| `inventory.remote_updated` | Remote target inventory received |

### Commands

| Event | Trigger |
|-------|---------|
| `command.queued` | Command added to queue |
| `command.dispatched` | Command sent to agent via heartbeat |
| `command.completed` | Command execution succeeded |
| `command.failed` | Command execution failed |

### Plugin Lifecycle

| Event | Trigger |
|-------|---------|
| `plugin.installed` | Plugin installed and initialized |
| `plugin.removed` | Plugin removed from server |
| `plugin.enabled` | Plugin enabled |
| `plugin.disabled` | Plugin disabled |
| `plugin.health_changed` | Plugin health status changes |

### Automation

| Event | Trigger |
|-------|---------|
| `automation.started` | Playbook execution started |
| `automation.completed` | Playbook execution completed |
| `automation.failed` | Playbook execution failed |
| `playbook.executed` | Individual playbook step executed |
| `approval.requested` | Approval request created |

### Infrastructure

| Event | Trigger |
|-------|---------|
| `backup.succeeded` | Backup job succeeded |
| `backup.failed` | Backup job failed |
| `alert.created` | New alert created |
| `alert.resolved` | Alert resolved |

### Integration

| Event | Trigger |
|-------|---------|
| `integration.connected` | Integration connection successful |
| `integration.disconnected` | Integration disconnected |
| `integration.error` | Integration error occurred |

### System

| Event | Trigger |
|-------|---------|
| `system.startup` | Server starting up |
| `system.shutdown` | Server shutting down |
| `migration.completed` | Database migration completed |

---

## 3. Publishing Events

```python
from app.events import Event, EventType, event_bus

# Publish an event
await event_bus.publish(Event(
    type=EventType.HEARTBEAT_RECEIVED,
    data={
        "agent_id": 1,
        "health": "healthy",
        "cpu_percent": 45.2,
    },
    source="heartbeat_service",
))
```

### Event Structure

```python
@dataclass
class Event:
    type: EventType          # Event type enum
    data: dict[str, Any]     # Event payload
    source: str              # Publishing component
    timestamp: datetime      # UTC timestamp
```

---

## 4. Subscribing to Events

### Decorator Pattern

```python
from app.events import EventType, event_bus

@event_bus.on(EventType.AGENT_ONLINE)
async def handle_agent_online(event):
    logger.info("Agent %s is now online", event.data["agent_id"])
```

### Manual Subscription

```python
async def handle_heartbeat(event):
    # Process heartbeat event
    pass

event_bus.subscribe(EventType.HEARTBEAT_RECEIVED, handle_heartbeat)
```

---

## 5. Event History

The event bus maintains a history of recent events.

```python
# Get last 50 events
history = event_bus.get_history()

# Get last 20 heartbeat events
history = event_bus.get_history(
    event_type=EventType.HEARTBEAT_RECEIVED,
    limit=20,
)
```

**Retention:** Last 100 events (configurable via `_max_history`).

---

## 6. Error Handling

Event handlers are isolated. A failing handler does not affect other handlers or the publisher.

```python
@event_bus.on(EventType.COMMAND_COMPLETED)
async def handle_command_completed(event):
    try:
        # Update dashboard cache
        await update_dashboard_cache(event)
    except Exception:
        logger.exception("Dashboard cache update failed")  # Logged, not raised
```

---

## 7. Current Subscribers

| Event | Subscriber | Action |
|-------|------------|--------|
| `heartbeat.received` | Agent State Engine | Update agent state |
| `agent.online` | Dashboard Service | Refresh agent count |
| `agent.offline` | Notification Service | Send offline alert |
| `agent.health_changed` | State Engine | Transition state |
| `command.queued` | Audit Trail | Record command |
| `command.completed` | Audit Trail | Record result |
| `command.failed` | Notification Service | Send failure alert |
| `automation.started` | Audit Trail | Record execution |
| `automation.completed` | Audit Trail | Record completion |
| `plugin.installed` | Audit Trail | Record installation |

---

## 8. Future: External Message Broker

The current event bus is in-process only. For multi-server deployments, an external message broker can be added.

### Planned: Redis Streams

```python
# Future: External event bus
class RedisEventBus:
    async def publish(self, event: Event):
        await redis.xadd("mc:events", event.to_dict())
    
    async def subscribe(self, event_type: EventType):
        async for message in redis.xread({"mc:events": "$"}):
            yield Event.from_dict(message)
```

### Migration Path

1. Current: In-process `EventBus` (single server)
2. Future: `RedisEventBus` (multi-server)
3. Configuration: `EVENT_BUS_BACKEND=inprocess|redis`

The API remains identical — only the backend implementation changes.
