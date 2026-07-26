# Agent-Side Plugins

Agent-side plugins extend agent capabilities on the host machine. They handle system inventory, command execution, health checks, and remote operations support. Agent plugins are written in Python 3.12 with no external dependencies.

## Agent-Side Plugin Structure

```
my-agent-side-plugin/
├── manifest.json
├── index.py
├── inventory/
│   ├── system.py
│   ├── network.py
│   └── services.py
├── commands/
│   ├── handlers.py
│   └── scripts/
│       └── deploy.sh
├── health/
│   └── checks.py
├── remote/
│   └── operations.py
└── tests/
    └── test_plugin.py
```

### manifest.json

```json
{
  "name": "my-agent-side-plugin",
  "version": "1.0.0",
  "type": "agent",
  "description": "Agent-side plugin for system monitoring",
  "author": "Your Name",
  "license": "MIT",
  "minMissionControl": "2.0.0",
  "maxMissionControl": "3.0.0",
  "capabilities": ["inventory.collect", "command.execute", "health.check"],
  "permissions": ["read:system", "execute:commands", "read:network"],
  "entry": {
    "agent": "index.py"
  },
  "config": {
    "collectors": {
      "type": "list",
      "required": false,
      "default": ["system", "network", "services"]
    },
    "health_check_interval": {
      "type": "integer",
      "required": false,
      "default": 60
    }
  }
}
```

## Inventory Collection

Plugins provide inventory data through collectors. Each collector gathers specific system information:

```python
# inventory/system.py
import os
import platform
import psutil

async def collect_system_inventory():
    """Collect system inventory data."""
    return {
        "system": {
            "hostname": platform.node(),
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_total": psutil.virtual_memory().total,
            "memory_used": psutil.virtual_memory().used,
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": {
                path: {
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": (usage.used / usage.total) * 100
                }
                for path, usage in _get_disk_usage()
            }
        }
    }

def _get_disk_usage():
    """Get disk usage for all mounted partitions."""
    partitions = psutil.disk_partitions()
    usage = []
    
    for partition in partitions:
        try:
            usage.append((partition.mountpoint, psutil.disk_usage(partition.mountpoint)))
        except PermissionError:
            continue
    
    return usage
```

```python
# inventory/network.py
import socket
import psutil

async def collect_network_inventory():
    """Collect network inventory data."""
    interfaces = {}
    
    for name, addrs in psutil.net_if_addrs().items():
        interfaces[name] = {
            "addresses": [
                {
                    "family": str(addr.family),
                    "address": addr.address,
                    "netmask": addr.netmask,
                    "broadcast": addr.broadcast
                }
                for addr in addrs
            ],
            "stats": dict(psutil.net_if_stats().get(name, {}))
        }
    
    return {
        "network": {
            "interfaces": interfaces,
            "connections": len(psutil.net_connections()),
            "io_counters": dict(psutil.net_io_counters()._asdict())
        }
    }
```

```python
# inventory/services.py
import subprocess
import platform

async def collect_services_inventory():
    """Collect running services inventory."""
    system = platform.system()
    
    if system == "Linux":
        return await _collect_linux_services()
    elif system == "Windows":
        return await _collect_windows_services()
    else:
        return {"services": {"error": f"Unsupported platform: {system}"}}

async def _collect_linux_services():
    """Collect Linux services using systemctl."""
    try:
        result = subprocess.run(
            ["systemctl", "list-units", "--type=service", "--state=running", "--json"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            services = []
            
            for unit in data.get("units", []):
                services.append({
                    "name": unit["name"],
                    "status": unit.get("sub", "unknown"),
                    "description": unit.get("description", "")
                })
            
            return {"services": {"running": services}}
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    return {"services": {"error": "Failed to collect services"}}

async def _collect_windows_services():
    """Collect Windows services using PowerShell."""
    try:
        result = subprocess.run(
            ["powershell", "-Command", "Get-Service | Select-Object Name, Status, DisplayName | ConvertTo-Json"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            import json
            services = json.loads(result.stdout)
            
            return {"services": {"running": services}}
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    return {"services": {"error": "Failed to collect services"}}
```

## Command Execution

Plugins register handlers for commands sent from the server:

```python
# commands/handlers.py
import subprocess
import os

async def handle_execute_script(agent, command):
    """Handle script execution command."""
    script_path = command.get("script", "")
    args = command.get("args", [])
    timeout = command.get("timeout", 300)
    
    # Validate script path (security check)
    if not _is_safe_path(script_path):
        return {"status": "error", "message": "Unsafe script path"}
    
    try:
        result = subprocess.run(
            [script_path] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.path.dirname(script_path)
        )
        
        return {
            "status": "completed",
            "returncode": result.returncode,
            "stdout": result.stdout[:10000],  # Limit output
            "stderr": result.stderr[:10000]
        }
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "timeout": timeout}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def _is_safe_path(path):
    """Check if path is safe to execute."""
    # Implement path validation logic
    allowed_directories = [
        os.path.expanduser("~/.config/mission-control-agent/scripts"),
        "/opt/mission-control/scripts"
    ]
    
    return any(path.startswith(d) for d in allowed_directories)
```

## Health Checks

Plugins provide health check data:

```python
# health/checks.py
import psutil

async def check_system_health(agent):
    """Check system health."""
    checks = []
    
    # CPU check
    cpu_percent = psutil.cpu_percent(interval=1)
    checks.append({
        "name": "cpu_usage",
        "healthy": cpu_percent < 90,
        "value": cpu_percent,
        "threshold": 90
    })
    
    # Memory check
    memory = psutil.virtual_memory()
    checks.append({
        "name": "memory_usage",
        "healthy": memory.percent < 85,
        "value": memory.percent,
        "threshold": 85
    })
    
    # Disk check
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            checks.append({
                "name": f"disk_usage_{partition.mountpoint}",
                "healthy": usage.percent < 90,
                "value": usage.percent,
                "threshold": 90
            })
        except PermissionError:
            continue
    
    # Service check
    checks.append({
        "name": "agent_service",
        "healthy": True,
        "message": "Agent service is running"
    })
    
    overall_healthy = all(check["healthy"] for check in checks)
    
    return {
        "healthy": overall_healthy,
        "checks": checks,
        "timestamp": time.time()
    }
```

## Remote Operations Support

Plugins support remote operations initiated by the server:

```python
# remote/operations.py
import subprocess
import os

async def handle_remote_operation(agent, operation):
    """Handle remote operation from server."""
    op_type = operation.get("type")
    
    if op_type == "file_transfer":
        return await _handle_file_transfer(operation)
    elif op_type == "script_execution":
        return await _handle_script_execution(operation)
    elif op_type == "service_management":
        return await _handle_service_management(operation)
    elif op_type == "system_info":
        return await _handle_system_info(operation)
    else:
        return {"status": "unsupported", "type": op_type}

async def _handle_file_transfer(operation):
    """Handle file transfer operation."""
    direction = operation.get("direction")  # "upload" or "download"
    source = operation.get("source")
    destination = operation.get("destination")
    
    if direction == "upload":
        # Receive file from server
        content = operation.get("content")
        with open(destination, "wb") as f:
            f.write(content.encode())
        return {"status": "success", "bytes_written": len(content)}
    
    elif direction == "download":
        # Send file to server
        with open(source, "rb") as f:
            content = f.read()
        return {"status": "success", "content": content.decode()}

async def _handle_script_execution(operation):
    """Handle script execution operation."""
    script = operation.get("script")
    timeout = operation.get("timeout", 300)
    
    try:
        result = subprocess.run(
            script,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        return {
            "status": "success",
            "returncode": result.returncode,
            "stdout": result.stdout[:10000],
            "stderr": result.stderr[:10000]
        }
    except subprocess.TimeoutExpired:
        return {"status": "timeout"}

async def _handle_service_management(operation):
    """Handle service management operation."""
    action = operation.get("action")  # "start", "stop", "restart", "status"
    service = operation.get("service")
    
    if action == "status":
        result = subprocess.run(
            ["systemctl", "is-active", service],
            capture_output=True,
            text=True
        )
        return {"status": "success", "service_status": result.stdout.strip()}
    
    elif action in ["start", "stop", "restart"]:
        result = subprocess.run(
            ["systemctl", action, service],
            capture_output=True,
            text=True
        )
        return {"status": "success" if result.returncode == 0 else "error"}

async def _handle_system_info(operation):
    """Handle system info request."""
    import platform
    import psutil
    
    return {
        "status": "success",
        "info": {
            "hostname": platform.node(),
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "uptime": psutil.boot_time()
        }
    }
```

## Offline Behavior

Plugins continue operating when the server is unreachable:

```python
class OfflineManager:
    """Manage offline operations."""
    
    def __init__(self, agent):
        self.agent = agent
        self.pending_operations = []
        self.local_cache = {}
    
    async def queue_operation(self, operation):
        """Queue operation for when server is available."""
        self.pending_operations.append({
            "operation": operation,
            "timestamp": time.time(),
            "retry_count": 0
        })
        
        # Persist to disk
        await self._save_pending_operations()
    
    async def process_pending_operations(self):
        """Process queued operations when server is available."""
        if not self.pending_operations:
            return
        
        for op in self.pending_operations[:]:
            try:
                result = await self.agent.execute_operation(op["operation"])
                if result["status"] == "success":
                    self.pending_operations.remove(op)
            except Exception:
                op["retry_count"] += 1
                if op["retry_count"] >= 3:
                    self.pending_operations.remove(op)
        
        await self._save_pending_operations()
    
    async def _save_pending_operations(self):
        """Save pending operations to disk."""
        import json
        path = os.path.expanduser(
            "~/.config/mission-control-agent/pending_operations.json"
        )
        with open(path, "w") as f:
            json.dump(self.pending_operations, f)
    
    async def _load_pending_operations(self):
        """Load pending operations from disk."""
        import json
        path = os.path.expanduser(
            "~/.config/mission-control-agent/pending_operations.json"
        )
        if os.path.exists(path):
            with open(path, "r") as f:
                self.pending_operations = json.load(f)
```

## Entry Point Integration

Combine all components in the entry point:

```python
# index.py
import logging
from mission_control_agent.plugins import AgentPlugin
from inventory.system import collect_system_inventory
from inventory.network import collect_network_inventory
from inventory.services import collect_services_inventory
from commands.handlers import handle_execute_script
from health.checks import check_system_health
from remote.operations import handle_remote_operation

logger = logging.getLogger(__name__)

class MyAgentSidePlugin(AgentPlugin):
    """Agent-side plugin for system monitoring."""
    
    async def on_enable(self, agent):
        """Register all hooks."""
        # Register inventory collectors
        await agent.inventory.register_collector("system", collect_system_inventory)
        await agent.inventory.register_collector("network", collect_network_inventory)
        await agent.inventory.register_collector("services", collect_services_inventory)
        
        # Register command handlers
        await agent.commands.register_handler("execute_script", handle_execute_script)
        
        # Register health checks
        await agent.health.register_check("system", check_system_health)
        
        # Register remote operations
        agent.remote.register_handler(handle_remote_operation)
        
        logger.info("Agent-side plugin enabled with all hooks registered")
    
    async def on_disable(self, agent):
        """Unregister all hooks."""
        await agent.inventory.unregister_collector("system")
        await agent.inventory.unregister_collector("network")
        await agent.inventory.unregister_collector("services")
        await agent.commands.unregister_handler("execute_script")
        await agent.health.unregister_check("system")
        
        logger.info("Agent-side plugin disabled")

plugin = MyAgentSidePlugin()
```

## Testing

```python
import pytest
from mission_control.testing import AgentPluginTestHarness

@pytest.fixture
def harness():
    return AgentPluginTestHarness("my-agent-side-plugin")

@pytest.mark.asyncio
async def test_system_inventory(harness):
    result = await harness.invoke_hook("collect_system_inventory")
    assert "system" in result
    assert "hostname" in result["system"]
    assert "cpu_count" in result["system"]

@pytest.mark.asyncio
async def test_health_check(harness):
    result = await harness.invoke_hook("check_system_health")
    assert "healthy" in result
    assert "checks" in result
    assert len(result["checks"]) > 0

@pytest.mark.asyncio
async def test_command_execution(harness):
    command = {"script": "/bin/echo", "args": ["hello"], "timeout": 10}
    result = await harness.invoke_hook("handle_execute_script", command=command)
    assert result["status"] == "completed"
    assert "hello" in result["stdout"]
```

## Next Steps

- [AGENT_SDK.md](AGENT_SDK.md) — Agent SDK overview
- [HYBRID_PLUGINS.md](HYBRID_PLUGINS.md) — Hybrid plugin development
- [EVENTS.md](EVENTS.md) — Event system reference
- [PERMISSIONS.md](PERMISSIONS.md) — Permissions model
- [PLUGIN_SDK.md](PLUGIN_SDK.md) — SDK overview
