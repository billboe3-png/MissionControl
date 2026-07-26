# Mission Control Plugin SDK

The Plugin SDK enables extending Mission Control with custom server, agent, and hybrid plugins. Plugins are distributed via the marketplace and run within the Mission Control runtime with access to typed events, services, and configuration.

## Plugin Types

| Type | Runtime | Use Cases |
|------|---------|-----------|
| **Server** | Mission Control server | REST API extensions, UI widgets, background jobs, integrations |
| **Agent** | Agent host (Python 3.12) | System inventory, local command execution, health checks |
| **Hybrid** | Server + Agent pair | Remote operations, distributed tasks, cross-host workflows |

## Manifest

Every plugin requires a `manifest.json` at its root. See [MANIFEST.md](MANIFEST.md) for the full schema.

```json
{
  "name": "example-plugin",
  "version": "1.0.0",
  "type": "hybrid",
  "description": "Example hybrid plugin",
  "author": "Mission Control",
  "license": "MIT",
  "minMissionControl": "2.0.0",
  "maxMissionControl": "3.0.0",
  "capabilities": ["event.subscribe", "inventory.collect", "command.execute"],
  "permissions": ["read:agents", "write:inventory", "execute:commands"],
  "entry": {
    "server": "server/index.py",
    "agent": "agent/index.py"
  },
  "config": {
    "api_key": { "type": "string", "required": false, "default": "" },
    "interval": { "type": "integer", "required": false, "default": 30 }
  }
}
```

## Capabilities

Capabilities declare what the plugin can do. The runtime validates capabilities at install time and gates access accordingly.

| Capability | Description | Plugin Type |
|------------|-------------|-------------|
| `event.subscribe` | Subscribe to event bus events | All |
| `event.publish` | Publish events to the event bus | All |
| `rest.extend` | Add REST API routes (server) | Server, Hybrid |
| `router.mount` | Mount FastAPI router | Server, Hybrid |
| `service.access` | Access service layer | Server, Hybrid |
| `database.access` | Access database through ORM | Server, Hybrid |
| `inventory.collect` | Provide inventory data | Agent, Hybrid |
| `command.execute` | Execute agent commands | Agent, Hybrid |
| `health.check` | Provide health check data | Agent, Hybrid |
| `config.read` | Read plugin configuration | All |
| `config.write` | Modify plugin configuration | All |
| `websocket.connect` | Use WebSocket connections | Server, Hybrid |
| `middleware.register` | Register request middleware | Server, Hybrid |
| `scheduler.register` | Register scheduled tasks | Server, Hybrid |

## Lifecycle

```
Install → Enable → Active → Disable → Uninstall
              ↓
         Update (re-install with new version)
```

1. **Install**: Plugin files are extracted, manifest validated, capabilities checked against permissions.
2. **Enable**: Plugin entry point is loaded, `on_enable()` called, event subscriptions registered.
3. **Active**: Plugin runs normally, responding to events and serving requests.
4. **Disable**: Plugin is gracefully stopped, `on_disable()` called, resources released.
5. **Uninstall**: Plugin is removed, `on_uninstall()` called, cleanup performed.

## Installation

### From Marketplace

```bash
mission-control plugin install <plugin-name>@<version>
```

### From Local File

```bash
mission-control plugin install ./path/to/plugin.tar.gz
```

### Programmatic

```python
from mission_control.plugins import PluginManager

manager = PluginManager()
manager.install("plugin-name", version="1.2.0")
manager.enable("plugin-name")
```

## Configuration

Plugins declare configuration fields in their manifest. Values are stored in `~/.config/mission-control/plugins/<plugin-name>/config.yaml` (agent-side) or the server database (server-side).

Access configuration in code:

```python
from mission_control.config import get_plugin_config

config = get_plugin_config("example-plugin")
api_key = config.get("api_key", "")
interval = config.get("interval", 30)
```

See [AGENT_SDK.md](AGENT_SDK.md) for agent-specific configuration at `~/.config/mission-control-agent/config.yaml`.

## API Access

### Server Plugins

Server plugins receive a FastAPI `APIRouter` instance and can mount custom routes:

```python
from fastapi import APIRouter

router = APIRouter(prefix="/example", tags=["example"])

@router.get("/status")
async def get_status():
    return {"status": "ok"}
```

### Agent Plugins

Agent plugins access agent services through the agent runtime:

```python
from mission_control_agent.inventory import InventoryCollector
from mission_control_agent.commands import CommandExecutor

async def on_enable(agent):
    collector = InventoryCollector(agent)
    await collector.register_provider("custom_metrics", collect_metrics)
```

### Shared

All plugin types can subscribe to and publish events on the event bus. See [EVENTS.md](EVENTS.md).

## SDK Versioning

The SDK follows semantic versioning. The `minMissionControl` and `maxMissionControl` fields in the manifest control compatibility.

| SDK Version | Mission Control Version | Status |
|-------------|------------------------|--------|
| 1.x | 1.x | Legacy |
| 2.x | 2.x | Current |
| 3.x | 3.x | Beta |

See [VERSIONING.md](VERSIONING.md) for detailed versioning rules.

## Compatibility Matrix

| Feature | Server | Agent | Hybrid |
|---------|--------|-------|--------|
| Event bus | Yes | Yes | Yes |
| REST API | Yes | No | Yes |
| Database | Yes | No | Yes |
| Inventory | No | Yes | Yes |
| Commands | No | Yes | Yes |
| Health checks | No | Yes | Yes |
| WebSocket | Yes | No | Yes |
| Scheduler | Yes | No | Yes |
| Middleware | Yes | No | Yes |
| Offline mode | No | Yes | Yes |

## Permissions

Plugins must declare required permissions in their manifest. The runtime validates permissions at install time and enforces them at runtime. See [PERMISSIONS.md](PERMISSIONS.md) for details.

## Error Handling

Plugins should handle errors gracefully and report them through the event bus:

```python
from mission_control.events import publish_event

async def on_enable(agent):
    try:
        await setup_resources(agent)
    except Exception as e:
        await publish_event("plugin.error", {
            "plugin": "example-plugin",
            "error": str(e),
            "phase": "enable"
        })
        raise
```

## Testing

Plugins can be tested using the SDK test utilities:

```python
from mission_control.testing import PluginTestHarness

harness = PluginTestHarness("example-plugin")
harness.set_config({"api_key": "test-key"})

async def test_inventory_collection():
    result = await harness.invoke_agent_hook("on_inventory_collect")
    assert "custom_metrics" in result
```

## Next Steps

- [AGENT_SDK.md](AGENT_SDK.md) — Develop agent-side plugins
- [SERVER_PLUGINS.md](SERVER_PLUGINS.md) — Develop server-side plugins
- [HYBRID_PLUGINS.md](HYBRID_PLUGINS.md) — Develop hybrid plugins
- [MANIFEST.md](MANIFEST.md) — Full manifest reference
- [EVENTS.md](EVENTS.md) — Event system reference
- [PERMISSIONS.md](PERMISSIONS.md) — Permissions model
