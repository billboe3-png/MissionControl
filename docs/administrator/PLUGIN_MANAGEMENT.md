# Plugin Management

**Version:** 3.0.0

Mission Control supports a plugin architecture for extending functionality. Plugins are managed through the dashboard and the plugin API.

---

## Plugin Types

| Type | Description | Runs On |
|---|---|---|
| **Server** | Extends the API server. Adds new endpoints, event handlers, or scheduled tasks. | API server process |
| **Agent** | Extends agent capabilities. Adds new metrics collection, health checks, or remote commands. | Agent host |
| **Hybrid** | Combines server and agent components. Server side coordinates; agent side executes. | Both |

---

## Installing Plugins

### Via Dashboard

1. Navigate to **Plugins → Marketplace**.
2. Browse or search the marketplace catalog.
3. Click **Install** on the desired plugin.
4. Configure any required settings.
5. Click **Enable**.

### Via API

```bash
# Install from marketplace
curl -X POST http://localhost:8000/api/v1/plugins/install \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "zabbix-monitor",
    "version": "1.2.0",
    "source": "marketplace"
  }'
```

### Manual Installation

For custom or internal plugins:

```bash
# Place the plugin package in the plugins directory
cp my-custom-plugin.tar.gz /opt/mission-control/plugins/

# Install via API
curl -X POST http://localhost:8000/api/v1/plugins/install \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-custom-plugin",
    "source": "local",
    "path": "/opt/mission-control/plugins/my-custom-plugin.tar.gz"
  }'
```

---

## Updating Plugins

```bash
# Update a specific plugin
curl -X PUT http://localhost:8000/api/v1/plugins/zabbix-monitor/update \
  -H "Authorization: Bearer <admin-token>"
```

Updates are applied without restarting the API server. Agent-side plugins are pushed to agents automatically on the next heartbeat.

---

## Removing Plugins

```bash
curl -X DELETE http://localhost:8000/api/v1/plugins/zabbix-monitor \
  -H "Authorization: Bearer <admin-token>"
```

Removing a plugin:

1. Disables the plugin.
2. Removes plugin data and configuration.
3. Unregisters any scheduled tasks or event handlers.

Plugin removal does not affect existing data collected by the plugin.

---

## Plugin Permissions

Plugins can request the following permissions during installation:

| Permission | Description |
|---|---|
| `read:agents` | Read agent status and metrics. |
| `write:agents` | Send commands to agents. |
| `read:users` | Read user information. |
| `write:users` | Modify user data. |
| `read:plugins` | Read plugin metadata. |
| `write:plugins` | Install, update, or remove plugins. |
| `execute:remote` | Execute remote commands on agents. |
| `access:database` | Direct database access (restricted). |

Permission requests are displayed during installation and must be approved by an administrator.

---

## Plugin Compatibility

Plugins declare compatibility with specific Mission Control versions:

```yaml
# plugin.yaml
name: zabbix-monitor
version: 1.2.0
compatibility:
  min_version: "3.0.0"
  max_version: "3.x"
  python: ">=3.12"
```

The plugin system validates compatibility before installation and prevents installation of incompatible plugins.

---

## Plugin Health Monitoring

Each plugin's health is monitored continuously:

- **Healthy** — Plugin is running normally.
- **Degraded** — Plugin is running but experiencing issues.
- **Unhealthy** — Plugin has failed.
- **Disabled** — Plugin is installed but not active.

Health status is available on the dashboard under **Plugins → Health** and via the `/subsystems` endpoint. See [Monitoring](MONITORING.md) for health check details.

```bash
curl http://localhost:8000/api/v1/plugins/health \
  -H "Authorization: Bearer <admin-token>"
```

---

## Marketplace Catalog

The plugin marketplace provides a curated catalog of vetted plugins. Available categories:

- **Monitoring** — Zabbix, Prometheus, Nagios integrations.
- **Authentication** — LDAP, OAuth, SAML providers.
- **Notification** — Email, Slack, Microsoft Teams, PagerDuty.
- **Compliance** — CIS benchmarks, SOX reporting.
- **Backup** — Automated backup orchestration.

Enterprise edition provides access to the full marketplace catalog. Community edition includes core plugins only.

---

## Developing Plugins

Plugins follow a standard interface:

```python
# plugin.py
from mission_control.plugins import PluginBase

class MyPlugin(PluginBase):
    name = "my-plugin"
    version = "1.0.0"
    plugin_type = "server"  # server, agent, or hybrid

    async def on_load(self):
        """Called when the plugin is loaded."""
        self.register_event_handler("agent.heartbeat", self.handle_heartbeat)
        self.register_endpoint("GET", "/my-plugin/status", self.get_status)

    async def on_unload(self):
        """Called when the plugin is unloaded."""
        pass

    async def handle_heartbeat(self, event):
        """Handle agent heartbeat events."""
        pass

    async def get_status(self, request):
        """Custom API endpoint."""
        return {"status": "active"}
```

See the plugin SDK documentation for the complete development guide.
