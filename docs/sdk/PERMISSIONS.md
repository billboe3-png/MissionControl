# Plugin Permissions Model

Mission Control enforces a permissions model that controls what plugins can access and modify. Plugins declare required permissions in their manifest, and the runtime validates and enforces these permissions throughout the plugin lifecycle.

## Permission Types

### Read Permissions

Read permissions allow plugins to view data without modifying it:

| Permission | Description | Scope |
|------------|-------------|-------|
| `read:agents` | View agent list and details | Server, Hybrid |
| `read:inventory` | View agent inventory data | Server, Hybrid |
| `read:commands` | View command history and results | Server, Hybrid |
| `read:plugins` | View installed plugins | Server, Hybrid |
| `read:events` | View event history | Server, Hybrid |
| `read:alerts` | View system alerts | Server, Hybrid |
| `read:config` | View system configuration | Server, Hybrid |
| `read:logs` | View system logs | Server, Hybrid |
| `read:system` | View system information | Agent, Hybrid |
| `read:network` | View network information | Agent, Hybrid |
| `read:processes` | View process information | Agent, Hybrid |
| `read:services` | View service information | Agent, Hybrid |
| `read:files` | View file metadata | Agent, Hybrid |

### Write Permissions

Write permissions allow plugins to create and modify data:

| Permission | Description | Scope |
|------------|-------------|-------|
| `write:agents` | Modify agent details | Server, Hybrid |
| `write:inventory` | Modify inventory data | Server, Hybrid |
| `write:commands` | Create and modify commands | Server, Hybrid |
| `write:plugins` | Install and modify plugins | Server, Hybrid |
| `write:alerts` | Create and modify alerts | Server, Hybrid |
| `write:config` | Modify system configuration | Server, Hybrid |
| `write:inventory` | Write inventory data | Agent, Hybrid |
| `write:files` | Create and modify files | Agent, Hybrid |

### Execute Permissions

Execute permissions allow plugins to perform actions:

| Permission | Description | Scope |
|------------|-------------|-------|
| `execute:commands` | Execute commands on agents | Server, Hybrid |
| `execute:scripts` | Execute scripts on agents | Agent, Hybrid |
| `execute:services` | Start/stop/restart services | Agent, Hybrid |
| `execute:system` | Execute system operations | Agent, Hybrid |
| `execute:network` | Execute network operations | Agent, Hybrid |

### Admin Permissions

Admin permissions grant elevated access:

| Permission | Description | Scope |
|------------|-------------|-------|
| `admin:plugins` | Manage all plugins | Server, Hybrid |
| `admin:agents` | Manage all agents | Server, Hybrid |
| `admin:config` | Manage system configuration | Server, Hybrid |
| `admin:users` | Manage users and roles | Server |
| `admin:system` | System administration | Server, Hybrid |

## Requesting Permissions

### Manifest Declaration

Plugins declare required permissions in their manifest:

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "type": "hybrid",
  "permissions": [
    "read:agents",
    "read:inventory",
    "write:inventory",
    "execute:commands",
    "admin:plugins"
  ]
}
```

### Runtime Permission Checks

Plugins can check permissions at runtime:

```python
from mission_control.auth import check_permission

async def on_enable(self, app, db, services):
    """Check permissions before accessing resources."""
    # Check specific permission
    if not await check_permission("read:agents"):
        raise PermissionError("Missing read:agents permission")
    
    # Check multiple permissions
    required = ["read:agents", "write:inventory"]
    for perm in required:
        if not await check_permission(perm):
            raise PermissionError(f"Missing {perm} permission")
```

### Agent-Side Permission Checks

```python
from mission_control_agent.auth import check_permission

async def on_enable(self, agent):
    """Check permissions on agent side."""
    if not await check_permission("execute:scripts"):
        raise PermissionError("Missing execute:scripts permission")
    
    # Access protected resources
    await self._setup_script_execution(agent)
```

## Permission Validation

### Install-Time Validation

The runtime validates permissions during plugin installation:

```python
from mission_control.plugins import PluginInstaller

class PluginInstaller:
    async def install(self, plugin_path: str):
        """Install plugin with permission validation."""
        manifest = await self._load_manifest(plugin_path)
        
        # Validate required permissions exist
        for permission in manifest.get("permissions", []):
            if not self._is_valid_permission(permission):
                raise ValidationError(f"Invalid permission: {permission}")
        
        # Check if current user has required permissions
        for permission in manifest.get("permissions", []):
            if not await self._check_user_permission(permission):
                raise PermissionError(
                    f"User lacks required permission: {permission}"
                )
        
        # Proceed with installation
        await self._extract_plugin(plugin_path)
        await self._register_plugin(manifest)
```

### Runtime Enforcement

The runtime enforces permissions through middleware:

```python
from starlette.middleware.base import BaseHTTPMiddleware

class PermissionMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce plugin permissions."""
    
    async def dispatch(self, request, call_next):
        # Extract plugin from request
        plugin = self._extract_plugin(request)
        
        if plugin:
            # Check required permissions for endpoint
            required_permission = self._get_required_permission(request)
            
            if required_permission:
                if not await self._check_plugin_permission(plugin, required_permission):
                    return JSONResponse(
                        status_code=403,
                        content={"error": "Insufficient permissions"}
                    )
        
        return await call_next(request)
```

## Scope-Based Access

### Server Scope

Server-scoped permissions apply to the Mission Control server:

```python
# Server-side scope
server_scope = {
    "read:agents": True,
    "write:agents": True,
    "execute:commands": True,
    "admin:plugins": False  # Requires admin role
}
```

### Agent Scope

Agent-scoped permissions apply to agent hosts:

```python
# Agent-side scope
agent_scope = {
    "read:system": True,
    "execute:scripts": True,
    "execute:services": True,
    "write:files": True
}
```

### Hybrid Scope

Hybrid plugins combine both scopes:

```python
# Hybrid scope
hybrid_scope = {
    "server": {
        "read:agents": True,
        "write:inventory": True
    },
    "agent": {
        "read:system": True,
        "execute:scripts": True
    }
}
```

### Role-Based Access

Permissions are tied to user roles:

```python
ROLES = {
    "admin": [
        "read:agents", "write:agents", "execute:commands",
        "admin:plugins", "admin:agents", "admin:config"
    ],
    "operator": [
        "read:agents", "write:agents", "execute:commands",
        "read:inventory", "write:inventory"
    ],
    "viewer": [
        "read:agents", "read:inventory", "read:commands"
    ],
    "plugin": []  # Plugin-specific permissions
}

def get_role_permissions(role: str) -> list:
    """Get permissions for a role."""
    return ROLES.get(role, [])
```

## Audit Trail

### Permission Audit Log

All permission checks are logged for audit purposes:

```python
from mission_control.audit import log_permission_check

async def check_permission_with_audit(self, permission: str, context: dict):
    """Check permission with audit logging."""
    result = await self._check_permission(permission)
    
    # Log permission check
    await log_permission_check({
        "timestamp": time.time(),
        "permission": permission,
        "result": result,
        "plugin": context.get("plugin"),
        "user": context.get("user"),
        "resource": context.get("resource"),
        "action": context.get("action")
    })
    
    return result
```

### Audit Log Schema

```python
{
    "id": "audit-abc123",
    "timestamp": 1693000000.0,
    "event_type": "permission.check",
    "data": {
        "permission": "execute:commands",
        "result": True,
        "plugin": "my-plugin",
        "user": "admin@example.com",
        "resource": "agent:agent-1",
        "action": "execute"
    },
    "metadata": {
        "ip_address": "192.168.1.100",
        "user_agent": "MissionControl/2.0.0"
    }
}
```

### Querying Audit Logs

```python
from mission_control.audit import query_audit_logs

# Query recent permission checks
logs = await query_audit_logs(
    event_type="permission.check",
    start_time=time.time() - 86400,  # Last 24 hours
    filter={"plugin": "my-plugin"},
    limit=100
)

# Query failed permission checks
logs = await query_audit_logs(
    event_type="permission.check",
    filter={"result": False},
    limit=50
)
```

## Permission Examples

### Plugin with Read-Only Access

```json
{
  "name": "monitoring-plugin",
  "version": "1.0.0",
  "type": "server",
  "permissions": [
    "read:agents",
    "read:inventory",
    "read:commands"
  ]
}
```

### Plugin with Command Execution

```json
{
  "name": "command-plugin",
  "version": "1.0.0",
  "type": "hybrid",
  "permissions": [
    "read:agents",
    "execute:commands",
    "execute:scripts"
  ]
}
```

### Plugin with Full Access

```json
{
  "name": "admin-plugin",
  "version": "1.0.0",
  "type": "server",
  "permissions": [
    "admin:plugins",
    "admin:agents",
    "admin:config"
  ]
}
```

## Best Practices

1. **Principle of Least Privilege**: Request only the minimum permissions needed.
2. **Granular Permissions**: Use specific permissions instead of broad ones.
3. **Runtime Checks**: Validate permissions at runtime, not just at install time.
4. **Audit Logging**: Log all permission checks for security auditing.
5. **Error Handling**: Handle permission errors gracefully and report them.
6. **Documentation**: Document required permissions in plugin documentation.

## Next Steps

- [PLUGIN_SDK.md](PLUGIN_SDK.md) — SDK overview
- [MANIFEST.md](MANIFEST.md) — Manifest format reference
- [EVENTS.md](EVENTS.md) — Event system reference
- [AGENT_SDK.md](AGENT_SDK.md) — Agent plugin development
- [SERVER_PLUGINS.md](SERVER_PLUGINS.md) — Server plugin development
