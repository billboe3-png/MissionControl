# Agent SDK

The Agent SDK enables building plugins that run on agent hosts within the Mission Control ecosystem. Agent plugins are written in Python 3.12 with no external dependencies, using only the standard library and the agent runtime.

## Agent Plugin Structure

```
my-agent-plugin/
├── manifest.json
├── index.py
├── inventory/
│   └── collectors.py
├── commands/
│   └── handlers.py
├── health/
│   └── checks.py
└── tests/
    └── test_plugin.py
```

### manifest.json

```json
{
  "name": "my-agent-plugin",
  "version": "1.0.0",
  "type": "agent",
  "description": "Custom agent plugin for system monitoring",
  "author": "Your Name",
  "license": "MIT",
  "minMissionControl": "2.0.0",
  "maxMissionControl": "3.0.0",
  "capabilities": ["inventory.collect", "command.execute", "health.check"],
  "permissions": ["read:system", "execute:commands"],
  "entry": {
    "agent": "index.py"
  },
  "config": {
    "monitor_interval": { "type": "integer", "required": false, "default": 60 },
    "log_level": { "type": "string", "required": false, "default": "info" }
  }
}
```

See [MANIFEST.md](MANIFEST.md) for the complete manifest schema.

## Agent Plugin Entry Point

The entry point is a Python module that exports lifecycle hooks:

```python
# index.py
import logging
from mission_control_agent.plugins import AgentPlugin

logger = logging.getLogger(__name__)

class MyAgentPlugin(AgentPlugin):
    """Custom agent plugin."""
    
    async def on_install(self, agent):
        """Called when plugin is first installed."""
        logger.info("Plugin installed, setting up resources")
        await self._create_data_directory()
    
    async def on_enable(self, agent):
        """Called when plugin is enabled."""
        logger.info("Plugin enabled, registering hooks")
        
        # Register inventory collector
        await agent.inventory.register_collector(
            "custom_metrics",
            self.collect_metrics
        )
        
        # Register command handler
        await agent.commands.register_handler(
            "custom.execute",
            self.handle_custom_command
        )
        
        # Register health check
        await agent.health.register_check(
            "custom_health",
            self.check_health
        )
    
    async def on_disable(self, agent):
        """Called when plugin is disabled."""
        logger.info("Plugin disabled, cleaning up")
        await agent.inventory.unregister_collector("custom_metrics")
        await agent.commands.unregister_handler("custom.execute")
        await agent.health.unregister_check("custom_health")
    
    async def on_uninstall(self, agent):
        """Called when plugin is uninstalled."""
        logger.info("Plugin uninstalled, removing data")
        await self._remove_data_directory()
    
    async def collect_metrics(self, agent):
        """Collect custom inventory data."""
        config = agent.get_plugin_config("my-agent-plugin")
        interval = config.get("monitor_interval", 60)
        
        return {
            "custom_metrics": {
                "disk_usage": await self._get_disk_usage(),
                "process_count": await self._get_process_count(),
                "uptime": await self._get_uptime(),
                "collected_at": time.time()
            }
        }
    
    async def handle_custom_command(self, agent, command):
        """Handle custom command execution."""
        action = command.get("action", "status")
        
        if action == "status":
            return {"status": "ok", "plugin": "my-agent-plugin"}
        elif action == "restart":
            await self._restart_service()
            return {"status": "restarted"}
        else:
            return {"status": "unknown_action", "action": action}
    
    async def check_health(self, agent):
        """Provide health check data."""
        return {
            "healthy": True,
            "message": "Plugin operating normally",
            "last_check": time.time()
        }
    
    async def _get_disk_usage(self):
        """Get disk usage information."""
        import shutil
        usage = shutil.disk_usage("/")
        return {
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
            "percent": (usage.used / usage.total) * 100
        }
    
    async def _get_process_count(self):
        """Get count of running processes."""
        import os
        return len(os.listdir("/proc"))
    
    async def _get_uptime(self):
        """Get system uptime."""
        with open("/proc/uptime", "r") as f:
            uptime = float(f.read().split()[0])
        return uptime
    
    async def _create_data_directory(self):
        """Create plugin data directory."""
        import os
        data_dir = os.path.expanduser(
            "~/.config/mission-control-agent/plugins/my-agent-plugin/data"
        )
        os.makedirs(data_dir, exist_ok=True)
    
    async def _remove_data_directory(self):
        """Remove plugin data directory."""
        import shutil
        data_dir = os.path.expanduser(
            "~/.config/mission-control-agent/plugins/my-agent-plugin/data"
        )
        if os.path.exists(data_dir):
            shutil.rmtree(data_dir)
    
    async def _restart_service(self):
        """Restart the monitored service."""
        import subprocess
        subprocess.run(["systemctl", "restart", "my-service"], check=False)

# Export plugin instance
plugin = MyAgentPlugin()
```

## Lifecycle Hooks

### on_install(agent)

Called once when the plugin is first installed. Use this for one-time setup:

```python
async def on_install(self, agent):
    """First-time setup."""
    # Create data directories
    # Initialize configuration defaults
    # Set up initial state
```

### on_enable(agent)

Called each time the plugin is enabled. Register all hooks and start background tasks:

```python
async def on_enable(self, agent):
    """Register hooks and start tasks."""
    # Register inventory collectors
    # Register command handlers
    # Register health checks
    # Start background monitoring
```

### on_disable(agent)

Called when the plugin is disabled. Unregister hooks and clean up:

```python
async def on_disable(self, agent):
    """Unregister hooks and clean up."""
    # Unregister inventory collectors
    # Unregister command handlers
    # Unregister health checks
    # Stop background tasks
```

### on_uninstall(agent)

Called when the plugin is removed. Clean up all resources:

```python
async def on_uninstall(self, agent):
    """Clean up all resources."""
    # Remove data directories
    # Delete configuration files
    # Release external resources
```

## Heartbeat Integration

Agent plugins can extend heartbeat data. The agent sends heartbeats to the server at regular intervals (default: 30 seconds). Plugins contribute data to heartbeats through inventory collectors.

```python
async def collect_heartbeat_data(self, agent):
    """Collect data for heartbeat payload."""
    return {
        "plugin_status": {
            "name": "my-agent-plugin",
            "enabled": True,
            "last_check": time.time(),
            "metrics": await self._collect_metrics()
        }
    }
```

The heartbeat payload is included in the `agent.heartbeat` event (see [EVENTS.md](EVENTS.md)).

## Inventory Collection

Plugins provide inventory data through collectors. Collectors are called during heartbeat and on-demand:

```python
async def collect_inventory(self, agent):
    """Collect inventory data."""
    return {
        "custom_services": await self._discover_services(),
        "custom_config": await self._read_config(),
        "custom_status": await self._get_status()
    }

# Register collector
await agent.inventory.register_collector("custom_inventory", collect_inventory)
```

Inventory data is merged into the agent's inventory and synced to the server.

## Configuration

Agent plugins read configuration from `~/.config/mission-control-agent/config.yaml`:

```yaml
plugins:
  my-agent-plugin:
    enabled: true
    config:
      monitor_interval: 60
      log_level: info
      api_key: "your-api-key"
```

Access configuration in code:

```python
config = agent.get_plugin_config("my-agent-plugin")
interval = config.get("monitor_interval", 60)
```

See [MANIFEST.md](MANIFEST.md) for declaring configuration fields in the manifest.

## Logging

Use the standard library `logging` module. The agent runtime configures log handlers automatically:

```python
import logging

logger = logging.getLogger(__name__)

async def on_enable(self, agent):
    logger.info("Plugin enabled")
    logger.debug("Debug details: %s", debug_info)
    logger.warning("Warning: %s", warning_message)
    logger.error("Error: %s", error_message)
```

Logs are written to `~/.config/mission-control-agent/logs/agent.log` and forwarded to the server when connected.

## Error Handling

Plugins should handle errors gracefully and report them through the event bus:

```python
from mission_control_agent.events import publish_event

async def on_enable(self, agent):
    try:
        await self._setup_resources(agent)
    except Exception as e:
        logger.error("Failed to setup: %s", e)
        await publish_event("plugin.error", {
            "plugin": "my-agent-plugin",
            "error": str(e),
            "phase": "enable"
        })
        raise
```

See [EVENTS.md](EVENTS.md) for the full list of event types.

## Remote Operations

Agent plugins support remote operations initiated by the server. The agent always initiates contact with the server (heartbeat-driven), and remote operations are delivered via heartbeat responses:

```python
async def handle_remote_operation(self, agent, operation):
    """Handle operation received from server."""
    op_type = operation.get("type")
    
    if op_type == "execute_script":
        return await self._execute_script(operation["script"])
    elif op_type == "collect_files":
        return await self._collect_files(operation["paths"])
    elif op_type == "update_config":
        return await self._update_config(operation["config"])
    else:
        return {"status": "unsupported", "type": op_type}
```

See [HYBRID_PLUGINS.md](HYBRID_PLUGINS.md) for hybrid plugin patterns.

## Testing

### Unit Testing

```python
import pytest
from mission_control.testing import AgentPluginTestHarness

@pytest.fixture
def harness():
    return AgentPluginTestHarness("my-agent-plugin")

@pytest.mark.asyncio
async def test_inventory_collection(harness):
    result = await harness.invoke_hook("collect_inventory")
    assert "custom_services" in result
    assert isinstance(result["custom_services"], list)

@pytest.mark.asyncio
async def test_command_handling(harness):
    command = {"action": "status"}
    result = await harness.invoke_hook("handle_custom_command", command=command)
    assert result["status"] == "ok"

@pytest.mark.asyncio
async def test_health_check(harness):
    result = await harness.invoke_hook("check_health")
    assert result["healthy"] is True
```

### Integration Testing

```python
from mission_control.testing import AgentIntegrationTest

@pytest.mark.integration
async def test_full_lifecycle():
    test = AgentIntegrationTest("my-agent-plugin")
    
    # Install and enable
    await test.install()
    await test.enable()
    
    # Verify inventory collection
    inventory = await test.collect_inventory()
    assert "custom_metrics" in inventory
    
    # Verify command execution
    result = await test.execute_command({"action": "status"})
    assert result["status"] == "ok"
    
    # Disable and uninstall
    await test.disable()
    await test.uninstall()
```

## File Paths

| Path | Description |
|------|-------------|
| `~/.config/mission-control-agent/config.yaml` | Agent configuration |
| `~/.config/mission-control-agent/plugins/<name>/` | Plugin installation directory |
| `~/.config/mission-control-agent/plugins/<name>/data/` | Plugin data directory |
| `~/.config/mission-control-agent/logs/agent.log` | Agent log file |

## Next Steps

- [SERVER_PLUGINS.md](SERVER_PLUGINS.md) — Develop server-side plugins
- [HYBRID_PLUGINS.md](HYBRID_PLUGINS.md) — Develop hybrid plugins
- [EVENTS.md](EVENTS.md) — Event system reference
- [PERMISSIONS.md](PERMISSIONS.md) — Permissions model
- [PLUGIN_SDK.md](PLUGIN_SDK.md) — SDK overview
