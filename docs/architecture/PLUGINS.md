# Mission Control — Plugins

**Version:** 3.0.0

---

## Overview

Mission Control uses a plugin-first architecture. The core platform provides authentication, scheduling, and orchestration. All infrastructure knowledge lives in plugins.

---

## 1. Plugin Types

### Server Plugins

Run on the Mission Control server. Provide API endpoints, dashboard data, and server-side logic.

**Examples:** Veeam backup integration, Zabbix monitoring, Hyper-V management, Proxmox management, Active Directory, Microsoft 365.

### Agent Plugins

Run on managed agents. Collect platform-specific data and execute local commands.

**Examples:** Windows system collection, Linux system collection, Docker container monitoring, Hyper-V agent relay, Zabbix agent relay.

### Hybrid Plugins

Both server and agent components. The server plugin provides the API and dashboard; the agent plugin collects data.

**Examples:** Hyper-V (server plugin for API, agent plugin for VM data), Proxmox (same pattern).

---

## 2. Plugin Framework

### Base Classes

**Path:** `backend/app/plugins/base.py`

```python
class PluginBase(ABC):
    """Abstract base class for all plugins."""
    
    @abstractmethod
    def get_metadata(self) -> dict: ...
    
    @abstractmethod
    async def initialize(self) -> None: ...
    
    @abstractmethod
    async def shutdown(self) -> None: ...
```

### Server Plugin SDK

**Path:** `backend/app/plugins/server.py`

```python
class ServerPlugin(PluginBase):
    """Base class for server-side plugins."""
    
    def get_routes(self) -> list[APIRoute]: ...
    def get_dashboard_data(self, db: Session) -> dict: ...
    def get_health(self) -> dict: ...
```

### Agent Plugin SDK

**Path:** `backend/app/plugins/agent.py`

```python
class AgentPlugin(PluginBase):
    """Base class for agent-side plugins."""
    
    def collect_inventory(self) -> dict: ...
    def collect_metrics(self) -> dict: ...
    def execute_command(self, command: str) -> dict: ...
```

---

## 3. Plugin Communication

**Path:** `backend/app/plugins/communication.py`

Plugins communicate with the server through a defined protocol:

```
Agent Plugin                    Server
    |                              |
    |── collect_inventory() ──────>|
    |── collect_metrics() ────────>|
    |── execute_command() ────────>|
    |                              |
    |<── get_pending_commands() ───|
    |<── get_configuration() ─────|
```

---

## 4. Plugin Lifecycle

### Installation

```
1. Plugin package uploaded or marketplace selected
2. Plugin loader validates package
3. Plugin metadata stored in database
4. Plugin initialized (initialize() called)
5. Plugin enabled
6. PLUGIN_INSTALLED event published
```

### Enable/Disable

```
Enable:
  1. Plugin record updated (enabled=True)
  2. Plugin.initialize() called
  3. PLUGIN_ENABLED event published

Disable:
  1. Plugin.shutdown() called
  2. Plugin record updated (enabled=False)
  3. PLUGIN_DISABLED event published
```

### Removal

```
1. Plugin.shutdown() called
2. Plugin record deleted
3. PLUGIN_REMOVED event published
```

---

## 5. Plugin Loader

**Path:** `backend/app/plugins/loader.py`

Dynamic plugin loading from the plugins directory.

```python
from app.plugins.loader import PluginLoader

loader = PluginLoader()

# Load all plugins
plugins = loader.load_all()

# Load specific plugin
plugin = loader.load("veeam")

# Get plugin by name
plugin = loader.get_plugin("zabbix")
```

---

## 6. Plugin Permissions

Plugins declare required permissions:

| Permission | Description |
|------------|-------------|
| `database:read` | Read database tables |
| `database:write` | Write to database tables |
| `agent:read` | Read agent data |
| `agent:write` | Send commands to agents |
| `network:outbound` | Make outbound HTTP requests |
| `filesystem:read` | Read local filesystem |
| `filesystem:write` | Write to local filesystem |

---

## 7. Plugin Marketplace

**Path:** `backend/app/services/plugin_marketplace_service.py`

The marketplace provides a catalog of available plugins.

### Catalog

| Plugin | Type | Description |
|--------|------|-------------|
| Hyper-V | Hybrid | VM management and monitoring |
| Proxmox VE | Hybrid | VE nodes, VMs, containers |
| Zabbix | Hybrid | Monitoring integration |
| Veeam | Server | Backup job management |
| Active Directory | Hybrid | AD user/group management |
| Microsoft 365 | Hybrid | M365 tenant management |
| Docker | Agent | Container monitoring |
| Windows | Agent | Windows system collection |
| Linux | Agent | Linux system collection |

---

## 8. Built-in Plugins

### Agent Plugins

| Plugin | Path | Purpose |
|--------|------|---------|
| `windows_plugin.py` | `.agents/agent/plugins/` | Windows system, services, events |
| `linux_plugin.py` | `.agents/agent/plugins/` | Linux system, services, journal |
| `docker_plugin.py` | `.agents/agent/plugins/` | Docker containers, images |
| `hyperv_plugin.py` | `.agents/agent/plugins/` | Hyper-V VM relay |
| `zabbix_plugin.py` | `.agents/agent/plugins/` | Zabbix proxy relay |
| `ad_plugin.py` | `.agents/agent/plugins/` | Active Directory collection |
| `m365_plugin.py` | `.agents/agent/plugins/` | Microsoft 365 collection |

### Server Providers

| Provider | Path | Purpose |
|----------|------|---------|
| Hyper-V | `providers/hyperv/` | VM API, mock, agent relay |
| Proxmox | `providers/proxmox/` | VE API, mock, agent relay |
| Zabbix | `providers/zabbix/` | Zabbix API, mock, agent relay |
| Veeam | `providers/veeam/` | Veeam API, PowerShell, DB bridge |
| Identity | `providers/identity/` | LDAP, Graph API, agent relay |
| Remote | `providers/remote/` | SSH, WinRM (fallback) |
| Automation | `providers/automation/` | Agent, SSH, WinRM, HTTP execution |

---

## 9. Provider Factory Pattern

Each integration uses a factory pattern that resolves the best available provider:

```python
# Agent-first resolution
def get_hyperv_provider(db: Session):
    # 1. Check for agent-based provider (primary)
    agent_provider = HyperVAgentProvider(db)
    if agent_provider.is_available():
        return agent_provider
    
    # 2. Fallback to direct provider
    return HyperVRealProvider()
```

---

## 10. Plugin Configuration

Plugins store configuration in the `integration_profiles` table.

```json
{
  "name": "Zabbix Production",
  "integration_type": "zabbix",
  "enabled": true,
  "config": {
    "url": "https://zabbix.example.com",
    "username": "Admin",
    "verify_ssl": true
  }
}
```

Credentials are encrypted with Fernet before storage.
