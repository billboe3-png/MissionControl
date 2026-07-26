# Hybrid Plugin Development

Hybrid plugins combine server-side and agent-side components to enable distributed functionality. The server handles coordination, storage, and API access while agents execute tasks on remote hosts.

## Hybrid Plugin Structure

```
my-hybrid-plugin/
├── manifest.json
├── server/
│   ├── index.py
│   ├── routes.py
│   └── services.py
├── agent/
│   ├── index.py
│   ├── collectors.py
│   └── handlers.py
├── shared/
│   ├── models.py
│   └── events.py
└── tests/
    ├── test_server.py
    └── test_agent.py
```

### manifest.json

```json
{
  "name": "my-hybrid-plugin",
  "version": "1.0.0",
  "type": "hybrid",
  "description": "Hybrid plugin for distributed monitoring",
  "author": "Your Name",
  "license": "MIT",
  "minMissionControl": "2.0.0",
  "maxMissionControl": "3.0.0",
  "capabilities": [
    "rest.extend",
    "router.mount",
    "service.access",
    "database.access",
    "event.subscribe",
    "inventory.collect",
    "command.execute",
    "health.check"
  ],
  "permissions": [
    "read:agents",
    "write:agents",
    "execute:commands",
    "read:inventory",
    "write:inventory"
  ],
  "entry": {
    "server": "server/index.py",
    "agent": "agent/index.py"
  },
  "config": {
    "server": {
      "sync_interval": { "type": "integer", "required": false, "default": 300 },
      "data_retention_days": { "type": "integer", "required": false, "default": 30 }
    },
    "agent": {
      "collect_interval": { "type": "integer", "required": false, "default": 60 },
      "batch_size": { "type": "integer", "required": false, "default": 100 }
    }
  }
}
```

## Communication Patterns

### Server-to-Agent (Command Dispatch)

The server sends commands to agents via the heartbeat response:

```python
# server/services.py
from mission_control.events import publish_event

class HybridCommandService:
    """Service for sending commands to agents."""
    
    def __init__(self, db, event_bus):
        self.db = db
        self.event_bus = event_bus
    
    async def send_command(self, agent_id: str, command: dict):
        """Queue command for agent execution."""
        # Store command in database
        command_record = await self.db.commands.create({
            "agent_id": agent_id,
            "command": command,
            "status": "pending",
            "created_at": time.time()
        })
        
        # Publish event for agent pickup
        await self.event_bus.publish("hybrid.command.queued", {
            "plugin": "my-hybrid-plugin",
            "agent_id": agent_id,
            "command_id": command_record.id,
            "command": command
        })
        
        return command_record
    
    async def get_command_result(self, command_id: str):
        """Get result of executed command."""
        return await self.db.commands.get(command_id)
```

```python
# agent/handlers.py
from mission_control_agent.events import subscribe_event, publish_event

class HybridCommandHandler:
    """Handle commands from server."""
    
    async def on_enable(self, agent):
        """Subscribe to command events."""
        await subscribe_event("hybrid.command.queued", self._handle_command)
    
    async def _handle_command(self, event):
        """Process queued command."""
        command_id = event.data["command_id"]
        command = event.data["command"]
        
        try:
            # Execute command
            result = await self._execute_command(command)
            
            # Report result back to server
            await publish_event("hybrid.command.completed", {
                "command_id": command_id,
                "result": result,
                "status": "completed"
            })
        except Exception as e:
            await publish_event("hybrid.command.failed", {
                "command_id": command_id,
                "error": str(e),
                "status": "failed"
            })
    
    async def _execute_command(self, command):
        """Execute command locally."""
        import subprocess
        
        cmd_type = command.get("type")
        
        if cmd_type == "script":
            result = subprocess.run(
                command["script"],
                shell=True,
                capture_output=True,
                text=True,
                timeout=command.get("timeout", 300)
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        elif cmd_type == "status":
            return await self._get_status()
        else:
            return {"error": f"Unknown command type: {cmd_type}"}
```

### Agent-to-Server (Data Sync)

Agents send data to the server via inventory updates:

```python
# agent/collectors.py
from mission_control_agent.events import publish_event

class HybridDataCollector:
    """Collect and sync data to server."""
    
    async def on_enable(self, agent):
        """Start data collection."""
        self.agent = agent
        await agent.inventory.register_collector("hybrid_data", self.collect_data)
    
    async def collect_data(self, agent):
        """Collect data for sync."""
        data = {
            "system_metrics": await self._collect_metrics(),
            "custom_inventory": await self._collect_custom_inventory(),
            "alerts": await self._check_alerts()
        }
        
        # Batch data for efficient sync
        batch = await self._prepare_batch(data)
        
        return {
            "hybrid_data": {
                "batch": batch,
                "timestamp": time.time(),
                "agent_id": agent.id
            }
        }
    
    async def _collect_metrics(self):
        """Collect system metrics."""
        import psutil
        
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_io": dict(psutil.disk_io_counters()._asdict()),
            "net_io": dict(psutil.net_io_counters()._asdict())
        }
    
    async def _collect_custom_inventory(self):
        """Collect custom inventory data."""
        return {
            "installed_packages": await self._get_installed_packages(),
            "running_processes": await self._get_running_processes(),
            "open_ports": await self._get_open_ports()
        }
    
    async def _check_alerts(self):
        """Check for alert conditions."""
        alerts = []
        
        import psutil
        
        # CPU alert
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > 90:
            alerts.append({
                "type": "cpu_high",
                "severity": "warning",
                "value": cpu_percent
            })
        
        # Memory alert
        memory = psutil.virtual_memory()
        if memory.percent > 85:
            alerts.append({
                "type": "memory_high",
                "severity": "warning",
                "value": memory.percent
            })
        
        return alerts
    
    async def _prepare_batch(self, data):
        """Prepare data batch for sync."""
        import hashlib
        import json
        
        # Create checksum for data integrity
        checksum = hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()
        
        return {
            "data": data,
            "checksum": checksum,
            "version": "1.0"
        }
```

### Server-Side Data Processing

```python
# server/services.py
class HybridDataProcessor:
    """Process synced data from agents."""
    
    def __init__(self, db, event_bus):
        self.db = db
        self.event_bus = event_bus
    
    async def process_sync(self, agent_id: str, batch: dict):
        """Process data batch from agent."""
        # Validate checksum
        if not self._validate_checksum(batch):
            raise ValueError("Invalid checksum")
        
        data = batch["data"]
        
        # Store metrics
        if "system_metrics" in data:
            await self._store_metrics(agent_id, data["system_metrics"])
        
        # Store inventory
        if "custom_inventory" in data:
            await self._store_inventory(agent_id, data["custom_inventory"])
        
        # Process alerts
        if "alerts" in data:
            await self._process_alerts(agent_id, data["alerts"])
        
        # Publish sync completed event
        await self.event_bus.publish("hybrid.sync.completed", {
            "plugin": "my-hybrid-plugin",
            "agent_id": agent_id,
            "timestamp": time.time(),
            "records_processed": len(data)
        })
    
    def _validate_checksum(self, batch):
        """Validate batch checksum."""
        import hashlib
        import json
        
        expected = hashlib.sha256(
            json.dumps(batch["data"], sort_keys=True).encode()
        ).hexdigest()
        
        return batch["checksum"] == expected
    
    async def _store_metrics(self, agent_id: str, metrics: dict):
        """Store metrics in database."""
        await self.db.metrics.create({
            "agent_id": agent_id,
            "metrics": metrics,
            "timestamp": time.time()
        })
    
    async def _store_inventory(self, agent_id: str, inventory: dict):
        """Store inventory in database."""
        await self.db.inventory.create_snapshot(agent_id, inventory)
    
    async def _process_alerts(self, agent_id: str, alerts: list):
        """Process alerts from agent."""
        for alert in alerts:
            # Create alert record
            await self.db.alerts.create({
                "agent_id": agent_id,
                "alert": alert,
                "status": "active",
                "created_at": time.time()
            })
            
            # Publish alert event
            await self.event_bus.publish("hybrid.alert.created", {
                "plugin": "my-hybrid-plugin",
                "agent_id": agent_id,
                "alert": alert
            })
```

## Data Synchronization

### Sync Strategy

```python
class HybridSyncStrategy:
    """Manage data synchronization between server and agents."""
    
    def __init__(self, db, event_bus):
        self.db = db
        self.event_bus = event_bus
        self.sync_interval = 300  # 5 minutes
    
    async def start_sync_cycle(self):
        """Start periodic sync cycle."""
        while True:
            await self._sync_all_agents()
            await asyncio.sleep(self.sync_interval)
    
    async def _sync_all_agents(self):
        """Sync data from all active agents."""
        agents = await self.db.agents.list_active()
        
        for agent in agents:
            try:
                await self._sync_agent(agent)
            except Exception as e:
                logger.error("Sync failed for agent %s: %s", agent.id, e)
    
    async def _sync_agent(self, agent):
        """Sync data from specific agent."""
        # Get last sync timestamp
        last_sync = await self.db.sync.get_last_sync(agent.id)
        
        # Request sync from agent
        await self.event_bus.publish("hybrid.sync.requested", {
            "plugin": "my-hybrid-plugin",
            "agent_id": agent.id,
            "last_sync": last_sync
        })
    
    async def handle_sync_response(self, agent_id: str, data: dict):
        """Handle sync response from agent."""
        # Process synced data
        await self.db.sync.process_batch(agent_id, data)
        
        # Update last sync timestamp
        await self.db.sync.update_last_sync(agent_id, time.time())
        
        # Publish sync completed event
        await self.event_bus.publish("hybrid.sync.completed", {
            "plugin": "my-hybrid-plugin",
            "agent_id": agent_id,
            "timestamp": time.time()
        })
```

### Conflict Resolution

```python
class ConflictResolver:
    """Resolve data conflicts between server and agents."""
    
    def resolve(self, server_data: dict, agent_data: dict, strategy: str = "last_write"):
        """Resolve conflict based on strategy."""
        if strategy == "last_write":
            return self._resolve_last_write(server_data, agent_data)
        elif strategy == "server_wins":
            return server_data
        elif strategy == "agent_wins":
            return agent_data
        elif strategy == "merge":
            return self._resolve_merge(server_data, agent_data)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
    
    def _resolve_last_write(self, server_data, agent_data):
        """Resolve by last write timestamp."""
        server_ts = server_data.get("timestamp", 0)
        agent_ts = agent_data.get("timestamp", 0)
        
        return server_data if server_ts > agent_ts else agent_data
    
    def _resolve_merge(self, server_data, agent_data):
        """Merge data from both sources."""
        merged = {}
        
        # Merge all keys
        all_keys = set(list(server_data.keys()) + list(agent_data.keys()))
        
        for key in all_keys:
            server_val = server_data.get(key)
            agent_val = agent_data.get(key)
            
            if server_val is None:
                merged[key] = agent_val
            elif agent_val is None:
                merged[key] = server_val
            elif isinstance(server_val, dict) and isinstance(agent_val, dict):
                merged[key] = self._resolve_merge(server_val, agent_val)
            else:
                # Use last write for non-dict values
                merged[key] = server_data.get("timestamp", 0) > agent_data.get("timestamp", 0) and server_val or agent_val
        
        return merged
```

## Deployment Strategy

### Installation

```bash
# Install hybrid plugin
mission-control plugin install my-hybrid-plugin@1.0.0

# Server component is installed automatically
# Agent component is distributed to all agents
mission-control plugin distribute my-hybrid-plugin --agents all
```

### Server Component

```python
# server/index.py
from mission_control.plugins import ServerPlugin
from mission_control.events import subscribe_event

class MyHybridServerPlugin(ServerPlugin):
    """Server component of hybrid plugin."""
    
    async def on_enable(self, app, db, services):
        """Enable server component."""
        # Subscribe to agent events
        await subscribe_event("agent.heartbeat", self._handle_heartbeat)
        await subscribe_event("hybrid.command.completed", self._handle_command_result)
        await subscribe_event("hybrid.sync.completed", self._handle_sync)
        
        # Register API routes
        self.router = self._create_router()
        
        # Start sync manager
        self.sync_manager = HybridSyncManager(db, self.event_bus)
        self.scheduler.register("sync", self.sync_manager.start_sync_cycle)
    
    async def on_disable(self, app, db, services):
        """Disable server component."""
        self.scheduler.cancel("sync")
```

### Agent Component

```python
# agent/index.py
from mission_control_agent.plugins import AgentPlugin
from mission_control_agent.events import subscribe_event, publish_event

class MyHybridAgentPlugin(AgentPlugin):
    """Agent component of hybrid plugin."""
    
    async def on_enable(self, agent):
        """Enable agent component."""
        # Subscribe to server commands
        await subscribe_event("hybrid.command.queued", self._handle_command)
        await subscribe_event("hybrid.sync.requested", self._handle_sync_request)
        
        # Register inventory collector
        await agent.inventory.register_collector("hybrid_data", self.collect_data)
        
        # Register health check
        await agent.health.register_check("hybrid", self.check_health)
    
    async def on_disable(self, agent):
        """Disable agent component."""
        await agent.inventory.unregister_collector("hybrid_data")
        await agent.health.unregister_check("hybrid")
```

### Distribution

```python
class HybridPluginDistributor:
    """Distribute hybrid plugin to agents."""
    
    async def distribute(self, plugin_name: str, agents: list):
        """Distribute plugin to specified agents."""
        for agent_id in agents:
            try:
                await self._distribute_to_agent(plugin_name, agent_id)
            except Exception as e:
                logger.error("Failed to distribute to %s: %s", agent_id, e)
    
    async def _distribute_to_agent(self, plugin_name: str, agent_id: str):
        """Distribute plugin to specific agent."""
        # Create distribution package
        package = await self._create_package(plugin_name)
        
        # Send to agent via heartbeat response
        await self.event_bus.publish("hybrid.distribute", {
            "plugin": plugin_name,
            "agent_id": agent_id,
            "package": package
        })
        
        # Wait for installation confirmation
        await self._wait_for_installation(agent_id, plugin_name)
    
    async def _create_package(self, plugin_name: str):
        """Create distribution package."""
        import tarfile
        import io
        
        # Create tar.gz archive of agent component
        buffer = io.BytesIO()
        
        with tarfile.open(fileobj=buffer, mode='w:gz') as tar:
            # Add agent files
            agent_dir = f"plugins/{plugin_name}/agent"
            tar.add(agent_dir, arcname="agent")
            
            # Add manifest
            tar.add(f"plugins/{plugin_name}/manifest.json", arcname="manifest.json")
        
        return buffer.getvalue()
```

## Testing

### Server Component Testing

```python
import pytest
from mission_control.testing import ServerPluginTestHarness

@pytest.fixture
def harness():
    return ServerPluginTestHarness("my-hybrid-plugin")

@pytest.mark.asyncio
async def test_api_routes(harness):
    response = await harness.get("/hybrid/status")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_data_processing(harness):
    batch = {
        "data": {"system_metrics": {"cpu_percent": 50}},
        "checksum": "valid-checksum",
        "version": "1.0"
    }
    await harness.invoke_hook("process_sync", agent_id="test-agent", batch=batch)
```

### Agent Component Testing

```python
import pytest
from mission_control.testing import AgentPluginTestHarness

@pytest.fixture
def harness():
    return AgentPluginTestHarness("my-hybrid-plugin")

@pytest.mark.asyncio
async def test_data_collection(harness):
    result = await harness.invoke_hook("collect_data")
    assert "hybrid_data" in result
    assert "batch" in result["hybrid_data"]

@pytest.mark.asyncio
async def test_command_handling(harness):
    command = {"type": "status"}
    result = await harness.invoke_hook("_execute_command", command=command)
    assert "cpu_percent" in result
```

### Integration Testing

```python
from mission_control.testing import HybridIntegrationTest

@pytest.mark.integration
async def test_full_hybrid_workflow():
    test = HybridIntegrationTest("my-hybrid-plugin")
    
    # Enable both components
    await test.enable_server()
    await test.enable_agent()
    
    # Test command flow
    command = await test.send_command({"type": "status"})
    result = await test.get_command_result(command.id)
    assert result["status"] == "completed"
    
    # Test data sync
    await test.trigger_sync()
    sync_data = await test.get_sync_data("test-agent")
    assert "system_metrics" in sync_data
    
    # Disable components
    await test.disable_agent()
    await test.disable_server()
```

## Next Steps

- [AGENT_SDK.md](AGENT_SDK.md) — Agent plugin development
- [SERVER_PLUGINS.md](SERVER_PLUGINS.md) — Server plugin development
- [EVENTS.md](EVENTS.md) — Event system reference
- [PERMISSIONS.md](PERMISSIONS.md) — Permissions model
- [PLUGIN_SDK.md](PLUGIN_SDK.md) — SDK overview
