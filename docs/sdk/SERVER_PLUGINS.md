# Server Plugin Development

Server plugins extend the Mission Control server with custom REST API routes, background services, middleware, and integrations. They run within the FastAPI application and have access to the service layer, database, and event bus.

## Server Plugin Structure

```
my-server-plugin/
├── manifest.json
├── index.py
├── routes/
│   └── api.py
├── services/
│   └── my_service.py
├── models/
│   └── my_model.py
├── middleware/
│   └── my_middleware.py
└── tests/
    └── test_plugin.py
```

### manifest.json

```json
{
  "name": "my-server-plugin",
  "version": "1.0.0",
  "type": "server",
  "description": "Custom server plugin for API extensions",
  "author": "Your Name",
  "license": "MIT",
  "minMissionControl": "2.0.0",
  "maxMissionControl": "3.0.0",
  "capabilities": ["rest.extend", "router.mount", "service.access", "database.access", "event.subscribe"],
  "permissions": ["read:agents", "write:agents", "admin:plugins"],
  "entry": {
    "server": "index.py"
  },
  "config": {
    "api_prefix": { "type": "string", "required": false, "default": "/custom" },
    "rate_limit": { "type": "integer", "required": false, "default": 100 }
  }
}
```

See [MANIFEST.md](MANIFEST.md) for the complete manifest schema.

## Server Plugin Entry Point

The entry point exports a plugin class that integrates with the FastAPI application:

```python
# index.py
import logging
from fastapi import APIRouter
from mission_control.plugins import ServerPlugin
from mission_control.events import subscribe_event, publish_event

logger = logging.getLogger(__name__)

class MyServerPlugin(ServerPlugin):
    """Custom server plugin."""
    
    def __init__(self):
        super().__init__()
        self.router = APIRouter(prefix="/custom", tags=["custom"])
        self._setup_routes()
    
    async def on_enable(self, app, db, services):
        """Called when plugin is enabled."""
        logger.info("Server plugin enabled")
        
        # Subscribe to events
        await subscribe_event("agent.heartbeat", self._handle_heartbeat)
        await subscribe_event("agent.inventory.updated", self._handle_inventory_update)
        
        # Register background task
        self.scheduler.register("cleanup_old_records", self._cleanup, interval=3600)
    
    async def on_disable(self, app, db, services):
        """Called when plugin is disabled."""
        logger.info("Server plugin disabled")
        
        # Unsubscribe from events
        await unsubscribe_event("agent.heartbeat", self._handle_heartbeat)
        await unsubscribe_event("agent.inventory.updated", self._handle_inventory_update)
        
        # Cancel background tasks
        self.scheduler.cancel("cleanup_old_records")
    
    def _setup_routes(self):
        """Set up API routes."""
        
        @self.router.get("/status")
        async def get_status():
            return {"plugin": "my-server-plugin", "status": "active"}
        
        @self.router.get("/agents/{agent_id}/metrics")
        async def get_agent_metrics(agent_id: str):
            return await self._get_agent_metrics(agent_id)
        
        @self.router.post("/agents/{agent_id}/commands")
        async def send_command(agent_id: str, command: dict):
            return await self._send_command(agent_id, command)
        
        @self.router.get("/reports/summary")
        async def get_summary():
            return await self._generate_summary()
    
    async def _handle_heartbeat(self, event):
        """Handle agent heartbeat events."""
        agent_id = event.data["agent_id"]
        status = event.data["status"]
        
        # Update plugin state
        await self._update_agent_status(agent_id, status)
    
    async def _handle_inventory_update(self, event):
        """Handle inventory update events."""
        agent_id = event.data["agent_id"]
        inventory = event.data["inventory"]
        
        # Process inventory changes
        await self._process_inventory(agent_id, inventory)
    
    async def _get_agent_metrics(self, agent_id: str):
        """Get metrics for a specific agent."""
        # Access database through ORM
        agent = await self.db.agents.get(agent_id)
        if not agent:
            return {"error": "Agent not found"}
        
        metrics = await self.db.metrics.query(
            agent_id=agent_id,
            limit=100
        )
        
        return {
            "agent_id": agent_id,
            "metrics": [m.to_dict() for m in metrics]
        }
    
    async def _send_command(self, agent_id: str, command: dict):
        """Send command to an agent."""
        # Access service layer
        command_service = self.services.get("command")
        
        result = await command_service.execute(
            agent_id=agent_id,
            command=command.get("type", "status"),
            params=command.get("params", {})
        )
        
        # Publish event
        await publish_event("plugin.command.sent", {
            "plugin": "my-server-plugin",
            "agent_id": agent_id,
            "command": command
        })
        
        return result
    
    async def _generate_summary(self):
        """Generate summary report."""
        agents = await self.db.agents.list_all()
        
        return {
            "total_agents": len(agents),
            "active_agents": sum(1 for a in agents if a.status == "active"),
            "inactive_agents": sum(1 for a in agents if a.status != "active"),
            "generated_at": time.time()
        }
    
    async def _cleanup(self):
        """Clean up old records."""
        cutoff = time.time() - (30 * 24 * 3600)  # 30 days
        deleted = await self.db.metrics.delete_old(cutoff)
        logger.info("Cleaned up %d old metric records", deleted)
    
    async def _update_agent_status(self, agent_id: str, status: str):
        """Update agent status in database."""
        await self.db.agents.update_status(agent_id, status)
    
    async def _process_inventory(self, agent_id: str, inventory: dict):
        """Process inventory changes."""
        # Store inventory snapshot
        await self.db.inventory.create_snapshot(agent_id, inventory)
        
        # Check for changes
        previous = await self.db.inventory.get_latest(agent_id)
        if previous:
            changes = self._diff_inventory(previous.data, inventory)
            if changes:
                await publish_event("plugin.inventory.changes_detected", {
                    "agent_id": agent_id,
                    "changes": changes
                })
    
    def _diff_inventory(self, old: dict, new: dict) -> list:
        """Compare inventory snapshots and return changes."""
        changes = []
        
        for key in set(list(old.keys()) + list(new.keys())):
            old_val = old.get(key)
            new_val = new.get(key)
            
            if old_val != new_val:
                changes.append({
                    "field": key,
                    "old": old_val,
                    "new": new_val
                })
        
        return changes

# Export plugin instance
plugin = MyServerPlugin()
```

## FastAPI Router Integration

Server plugins mount routers on the FastAPI application:

```python
from fastapi import APIRouter, Depends
from mission_control.auth import require_permission

router = APIRouter(prefix="/my-plugin", tags=["my-plugin"])

@router.get("/data")
@require_permission("read:my_data")
async def get_data(db=Depends(get_db)):
    """Get data with permission check."""
    return await db.my_data.list_all()

@router.post("/data")
@require_permission("write:my_data")
async def create_data(data: dict, db=Depends(get_db)):
    """Create data with permission check."""
    return await db.my_data.create(data)
```

The router is automatically mounted at the plugin's prefix when enabled.

## Service Layer Access

Plugins access services through the `services` object:

```python
async def on_enable(self, app, db, services):
    # Access existing services
    agent_service = services.get("agent")
    command_service = services.get("command")
    inventory_service = services.get("inventory")
    
    # Register custom service
    services.register("my_custom_service", MyCustomService())
    
    # Use services
    agents = await agent_service.list_active()
    result = await command_service.execute(agent_id, "status")
```

## Database Access

Plugins access the database through the ORM:

```python
from mission_control.db import BaseModel, Column, String, Integer, DateTime

class MyModel(BaseModel):
    """Custom database model."""
    __tablename__ = "my_plugin_data"
    
    id = Column(String, primary_key=True)
    agent_id = Column(String, index=True)
    name = Column(String)
    value = Column(Integer)
    created_at = Column(DateTime)

# Query database
async def get_data(self, agent_id: str):
    return await self.db.query(MyModel).filter(
        MyModel.agent_id == agent_id
    ).all()

# Create record
async def create_data(self, data: dict):
    record = MyModel(**data)
    await self.db.add(record)
    await self.db.commit()
    return record
```

## Event Subscriptions

Plugins subscribe to events to react to system changes:

```python
from mission_control.events import subscribe_event, unsubscribe_event

async def on_enable(self, app, db, services):
    # Subscribe to specific events
    await subscribe_event("agent.heartbeat", self._on_heartbeat)
    await subscribe_event("agent.inventory.updated", self._on_inventory)
    await subscribe_event("plugin.installed", self._on_plugin_installed)
    
    # Subscribe with filter
    await subscribe_event(
        "agent.command.completed",
        self._on_command_completed,
        filter={"status": "failed"}
    )

async def on_disable(self, app, db, services):
    # Unsubscribe from events
    await unsubscribe_event("agent.heartbeat", self._on_heartbeat)
    await unsubscribe_event("agent.inventory.updated", self._on_inventory)
    await unsubscribe_event("plugin.installed", self._on_plugin_installed)
    await unsubscribe_event("agent.command.completed", self._on_command_completed)
```

See [EVENTS.md](EVENTS.md) for the complete list of event types.

## REST API Extension

Plugins extend the REST API by mounting routers:

```python
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/extensions/my-plugin", tags=["my-plugin"])

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@router.get("/metrics")
async def get_metrics():
    """Get plugin metrics."""
    return {
        "requests_served": self.request_count,
        "errors": self.error_count,
        "uptime": time.time() - self.start_time
    }

@router.exception_handler(CustomException)
async def custom_exception_handler(request, exc):
    """Handle custom exceptions."""
    return JSONResponse(
        status_code=400,
        content={"error": str(exc), "type": "custom_error"}
    )
```

## Middleware

Plugins register middleware to intercept requests:

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class PluginMiddleware(BaseHTTPMiddleware):
    """Custom middleware for plugin."""
    
    async def dispatch(self, request: Request, call_next):
        # Pre-processing
        start_time = time.time()
        
        # Add custom headers
        response = await call_next(request)
        
        # Post-processing
        duration = time.time() - start_time
        response.headers["X-Plugin-Duration"] = str(duration)
        
        return response

# Register middleware in on_enable
async def on_enable(self, app, db, services):
    app.add_middleware(PluginMiddleware)
```

## Authentication

Plugins use the existing authentication system:

```python
from fastapi import Depends
from mission_control.auth import get_current_user, require_permission

@router.get("/admin/settings")
async def get_admin_settings(user=Depends(get_current_user)):
    """Admin-only endpoint."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return await self._get_settings()

@router.post("/data")
@require_permission("write:data")
async def create_data(data: dict, user=Depends(get_current_user)):
    """Endpoint requiring specific permission."""
    return await self._create_data(data, user)
```

## Background Tasks

Plugins register background tasks using the scheduler:

```python
async def on_enable(self, app, db, services):
    # Schedule periodic task
    self.scheduler.register(
        "cleanup",
        self._cleanup_task,
        interval=3600  # Every hour
    )
    
    # Schedule cron-like task
    self.scheduler.register(
        "daily_report",
        self._generate_daily_report,
        cron="0 2 * * *"  # Daily at 2 AM
    )
    
    # One-time task
    self.scheduler.register_once(
        "initial_setup",
        self._initial_setup,
        delay=10  # 10 seconds after enable
    )

async def on_disable(self, app, db, services):
    self.scheduler.cancel("cleanup")
    self.scheduler.cancel("daily_report")
    self.scheduler.cancel("initial_setup")
```

## Testing

### Unit Testing

```python
import pytest
from mission_control.testing import ServerPluginTestHarness

@pytest.fixture
def harness():
    return ServerPluginTestHarness("my-server-plugin")

@pytest.mark.asyncio
async def test_api_endpoint(harness):
    response = await harness.get("/custom/status")
    assert response.status_code == 200
    assert response.json()["status"] == "active"

@pytest.mark.asyncio
async def test_database_operation(harness):
    data = await harness.invoke_hook("_generate_summary")
    assert "total_agents" in data
```

### Integration Testing

```python
from mission_control.testing import ServerIntegrationTest

@pytest.mark.integration
async def test_full_workflow():
    test = ServerIntegrationTest("my-server-plugin")
    
    # Enable plugin
    await test.enable()
    
    # Test API routes
    response = await test.client.get("/custom/status")
    assert response.status_code == 200
    
    # Test event handling
    await test.publish_event("agent.heartbeat", {
        "agent_id": "test-agent",
        "status": "active"
    })
    
    # Disable plugin
    await test.disable()
```

## Next Steps

- [AGENT_SDK.md](AGENT_SDK.md) — Develop agent-side plugins
- [HYBRID_PLUGINS.md](HYBRID_PLUGINS.md) — Develop hybrid plugins
- [EVENTS.md](EVENTS.md) — Event system reference
- [PERMISSIONS.md](PERMISSIONS.md) — Permissions model
- [PLUGIN_SDK.md](PLUGIN_SDK.md) — SDK overview
