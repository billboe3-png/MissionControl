# Event System for Plugins

Mission Control uses a typed event bus with 34 event categories. Plugins subscribe to and publish events to communicate with the system and other plugins.

## Event Types by Category

### Agent Lifecycle Events

| Event | Description | Payload |
|-------|-------------|---------|
| `agent.registered` | Agent registered with server | `agent_id`, `hostname`, `platform`, `ip_address` |
| `agent.connected` | Agent established connection | `agent_id`, `connection_id`, `protocol` |
| `agent.disconnected` | Agent lost connection | `agent_id`, `reason`, `last_seen` |
| `agent.deregistered` | Agent removed from server | `agent_id`, `reason` |
| `agent.status.changed` | Agent status changed | `agent_id`, `old_status`, `new_status` |
| `agent.updated` | Agent metadata updated | `agent_id`, `changes` |

### Heartbeat Events

| Event | Description | Payload |
|-------|-------------|---------|
| `agent.heartbeat` | Agent heartbeat received | `agent_id`, `status`, `uptime`, `metrics`, `inventory_hash` |
| `agent.heartbeat.missed` | Agent missed heartbeat | `agent_id`, `last_heartbeat`, `threshold` |
| `agent.heartbeat.recovered` | Agent heartbeat recovered | `agent_id`, `downtime_duration` |

### Inventory Events

| Event | Description | Payload |
|-------|-------------|---------|
| `agent.inventory.updated` | Agent inventory changed | `agent_id`, `inventory`, `changes` |
| `agent.inventory.synced` | Inventory synced to server | `agent_id`, `sync_id`, `records_updated` |
| `agent.inventory.conflict` | Inventory sync conflict | `agent_id`, `field`, `server_value`, `agent_value` |

### Command Events

| Event | Description | Payload |
|-------|-------------|---------|
| `agent.command.queued` | Command queued for execution | `command_id`, `agent_id`, `command_type`, `params` |
| `agent.command.started` | Command execution started | `command_id`, `agent_id`, `started_at` |
| `agent.command.completed` | Command execution completed | `command_id`, `agent_id`, `result`, `duration` |
| `agent.command.failed` | Command execution failed | `command_id`, `agent_id`, `error`, `duration` |
| `agent.command.timeout` | Command execution timed out | `command_id`, `agent_id`, `timeout` |
| `agent.command.cancelled` | Command cancelled | `command_id`, `agent_id`, `reason` |

### Plugin Events

| Event | Description | Payload |
|-------|-------------|---------|
| `plugin.installed` | Plugin installed | `plugin_name`, `version`, `type` |
| `plugin.enabled` | Plugin enabled | `plugin_name`, `version` |
| `plugin.disabled` | Plugin disabled | `plugin_name`, `reason` |
| `plugin.uninstalled` | Plugin uninstalled | `plugin_name`, `reason` |
| `plugin.updated` | Plugin updated | `plugin_name`, `old_version`, `new_version` |
| `plugin.error` | Plugin error occurred | `plugin_name`, `error`, `phase`, `stacktrace` |
| `plugin.command.sent` | Plugin sent command | `plugin_name`, `agent_id`, `command` |

### Automation Events

| Event | Description | Payload |
|-------|-------------|---------|
| `automation.rule.triggered` | Automation rule triggered | `rule_id`, `rule_name`, `conditions`, `actions` |
| `automation.rule.executed` | Automation rule executed | `rule_id`, `actions`, `results` |
| `automation.rule.failed` | Automation rule failed | `rule_id`, `error`, `partial_results` |
| `automation.schedule.fired` | Scheduled automation fired | `schedule_id`, `cron`, `next_run` |

### Infrastructure Events

| Event | Description | Payload |
|-------|-------------|---------|
| `infrastructure.service.started` | Infrastructure service started | `service_name`, `version`, `pid` |
| `infrastructure.service.stopped` | Infrastructure service stopped | `service_name`, `reason` |
| `infrastructure.service.health` | Service health check | `service_name`, `healthy`, `details` |
| `infrastructure.resource.warning` | Resource warning | `resource_type`, `current`, `threshold`, `agent_id` |
| `infrastructure.resource.critical` | Resource critical | `resource_type`, `current`, `threshold`, `agent_id` |

### System Events

| Event | Description | Payload |
|-------|-------------|---------|
| `system.startup` | System starting up | `version`, `components` |
| `system.shutdown` | System shutting down | `reason`, `graceful` |
| `system.error` | System error occurred | `component`, `error`, `severity` |
| `system.backup` | System backup event | `backup_id`, `status`, `size` |
| `system.migration` | Database migration event | `version`, `status`, `tables_affected` |

## Subscribing to Events

### Server-Side Subscription

```python
from mission_control.events import subscribe_event, unsubscribe_event

async def on_enable(self, app, db, services):
    """Subscribe to events when plugin is enabled."""
    # Subscribe to specific event
    await subscribe_event("agent.heartbeat", self._handle_heartbeat)
    
    # Subscribe with filter
    await subscribe_event(
        "agent.command.completed",
        self._handle_command,
        filter={"status": "failed"}
    )
    
    # Subscribe with multiple filters
    await subscribe_event(
        "agent.inventory.updated",
        self._handle_inventory,
        filter={"agent_id": ["agent-1", "agent-2"]}
    )

async def on_disable(self, app, db, services):
    """Unsubscribe when plugin is disabled."""
    await unsubscribe_event("agent.heartbeat", self._handle_heartbeat)
    await unsubscribe_event("agent.command.completed", self._handle_command)
    await unsubscribe_event("agent.inventory.updated", self._handle_inventory)
```

### Agent-Side Subscription

```python
from mission_control_agent.events import subscribe_event, unsubscribe_event

async def on_enable(self, agent):
    """Subscribe to events when plugin is enabled."""
    # Subscribe to command events
    await subscribe_event("hybrid.command.queued", self._handle_command)
    
    # Subscribe to sync events
    await subscribe_event("hybrid.sync.requested", self._handle_sync)

async def on_disable(self, agent):
    """Unsubscribe when plugin is disabled."""
    await unsubscribe_event("hybrid.command.queued", self._handle_command)
    await unsubscribe_event("hybrid.sync.requested", self._handle_sync)
```

### Wildcard Subscriptions

```python
# Subscribe to all agent events
await subscribe_event("agent.*", self._handle_any_agent_event)

# Subscribe to all command events
await subscribe_event("agent.command.*", self._handle_any_command_event)

# Subscribe to all plugin events
await subscribe_event("plugin.*", self._handle_any_plugin_event)
```

## Publishing Events

### Server-Side Publishing

```python
from mission_control.events import publish_event

async def trigger_action(self):
    """Publish event from server."""
    await publish_event("plugin.command.sent", {
        "plugin": "my-plugin",
        "agent_id": "agent-1",
        "command": {
            "type": "execute_script",
            "script": "/opt/scripts/backup.sh"
        }
    })
```

### Agent-Side Publishing

```python
from mission_control_agent.events import publish_event

async def report_status(self, agent):
    """Publish event from agent."""
    await publish_event("hybrid.command.completed", {
        "command_id": "cmd-123",
        "result": {"status": "success"},
        "duration": 5.2
    })
```

### Custom Events

Plugins can define and publish custom events:

```python
from mission_control.events import publish_event

# Define custom event
await publish_event("my-plugin.custom.event", {
    "data": "custom payload",
    "metadata": {
        "source": "my-plugin",
        "version": "1.0.0"
    }
})
```

## Event History

### Querying Event History

```python
from mission_control.events import get_event_history

# Get recent events
history = await get_event_history(
    event_type="agent.heartbeat",
    limit=100
)

# Get events with time range
history = await get_event_history(
    event_type="agent.command.completed",
    start_time=time.time() - 3600,  # Last hour
    end_time=time.time()
)

# Get events for specific agent
history = await get_event_history(
    event_type="agent.inventory.updated",
    filter={"agent_id": "agent-1"},
    limit=50
)
```

### Event History Schema

```python
{
    "id": "evt-abc123",
    "event_type": "agent.heartbeat",
    "timestamp": 1693000000.0,
    "source": "agent:agent-1",
    "data": {
        "agent_id": "agent-1",
        "status": "active",
        "uptime": 86400
    },
    "metadata": {
        "version": "2.0.0",
        "plugin": None
    }
}
```

## Event Filtering

### Filter Syntax

```python
# Simple equality filter
filter = {"status": "active"}

# Multiple values (OR)
filter = {"agent_id": ["agent-1", "agent-2", "agent-3"]}

# Nested filter
filter = {"data.metrics.cpu_percent": {"$gt": 90}}

# Combined filters (AND)
filter = {
    "status": "active",
    "agent_id": {"$in": ["agent-1", "agent-2"]},
    "timestamp": {"$gte": time.time() - 3600}
}
```

### Filter Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `$eq` | Equals | `{"status": {"$eq": "active"}}` |
| `$ne` | Not equals | `{"status": {"$ne": "inactive"}}` |
| `$gt` | Greater than | `{"cpu_percent": {"$gt": 90}}` |
| `$gte` | Greater than or equal | `{"cpu_percent": {"$gte": 80}}` |
| `$lt` | Less than | `{"memory_percent": {"$lt": 50}}` |
| `$lte` | Less than or equal | `{"memory_percent": {"$lte": 60}}` |
| `$in` | In list | `{"status": {"$in": ["active", "warning"]}}` |
| `$nin` | Not in list | `{"status": {"$nin": ["inactive"]}}` |

## Async Handling

### Async Event Handlers

```python
async def handle_heartbeat(self, event):
    """Async event handler."""
    # Process heartbeat data
    agent_id = event.data["agent_id"]
    status = event.data["status"]
    
    # Perform async operations
    await self.db.agents.update_status(agent_id, status)
    await self._notify_subscribers(agent_id, status)
    
    # Return result (optional)
    return {"processed": True}
```

### Concurrent Event Processing

```python
import asyncio

async def handle_concurrent_events(self, events):
    """Process multiple events concurrently."""
    tasks = [self._process_event(event) for event in events]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle results
    for result in results:
        if isinstance(result, Exception):
            logger.error("Event processing failed: %s", result)
```

### Event Handler Timeout

```python
from mission_control.events import subscribe_event

async def on_enable(self, app, db, services):
    """Subscribe with timeout."""
    await subscribe_event(
        "agent.command.completed",
        self._handle_command,
        timeout=30  # 30 second timeout
    )

async def _handle_command(self, event):
    """Handle command with timeout."""
    try:
        result = await asyncio.wait_for(
            self._process_command(event),
            timeout=25
        )
        return result
    except asyncio.TimeoutError:
        logger.error("Command processing timed out")
        return {"error": "timeout"}
```

## Error Handling

### Event Handler Errors

```python
async def safe_handler(self, event):
    """Event handler with error handling."""
    try:
        await self._process_event(event)
    except ValueError as e:
        logger.warning("Invalid event data: %s", e)
        await publish_event("plugin.error", {
            "plugin": "my-plugin",
            "error": str(e),
            "event_type": event.type
        })
    except Exception as e:
        logger.error("Event processing failed: %s", e)
        await publish_event("plugin.error", {
            "plugin": "my-plugin",
            "error": str(e),
            "event_type": event.type
        })
```

### Dead Letter Queue

Failed events are placed in a dead letter queue for later inspection:

```python
from mission_control.events import get_dead_letter_queue

# Get failed events
dlq = await get_dead_letter_queue(
    event_type="agent.command.completed",
    limit=100
)

# Retry failed event
for failed_event in dlq:
    try:
        await self._process_event(failed_event)
        await mark_as_retried(failed_event.id)
    except Exception:
        await increment_retry_count(failed_event.id)
```

## Best Practices

1. **Idempotency**: Design handlers to be idempotent since events may be delivered multiple times.
2. **Timeouts**: Always set timeouts for event handlers to prevent blocking.
3. **Error Handling**: Catch and handle exceptions gracefully, reporting errors via the event bus.
4. **Filtering**: Use filters to reduce unnecessary event processing.
5. **Async**: Use async handlers for I/O operations to avoid blocking.
6. **Logging**: Log event processing for debugging and audit purposes.

## Next Steps

- [PLUGIN_SDK.md](PLUGIN_SDK.md) — SDK overview
- [AGENT_SDK.md](AGENT_SDK.md) — Agent plugin development
- [SERVER_PLUGINS.md](SERVER_PLUGINS.md) — Server plugin development
- [HYBRID_PLUGINS.md](HYBRID_PLUGINS.md) — Hybrid plugin development
- [PERMISSIONS.md](PERMISSIONS.md) — Permissions model
