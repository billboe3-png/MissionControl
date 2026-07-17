# Plugin Architecture

Mission Control uses a distributed plugin architecture with three execution targets. Plugins extend the platform without modifying the core.

## Execution Targets

### Server Plugins
Run inside the Mission Control Server process.

**Use cases:**
- Dashboard widgets and data providers
- REST API extensions
- Navigation items and pages
- Settings panels
- Provider integrations (Zabbix, Grafana, Prometheus)
- Background jobs and scheduled tasks
- Database models and migrations

**Examples:** Veeam, GitHub, GitLab, Jira, ServiceNow, Azure, AWS, Grafana, Prometheus, Zabbix, SQL Server, PostgreSQL

### Agent Plugins
Run inside the Mission Control Agent on managed hosts.

**Use cases:**
- Local command execution
- System monitoring and inventory
- Health checks
- Performance counters
- File collection
- Event log collection
- Local script execution

**Examples:** TeamViewer, RustDesk, Windows Event Logs, Windows Services, Linux Services, SMART Disk Monitoring, Hardware Inventory, Performance Counters

### Hybrid Plugins
Contain both server and agent components.

**Flow:**
1. Server sends task to agent
2. Agent executes locally
3. Agent returns results
4. Server presents results on dashboard

**Use cases:**
- Remote desktop access
- Backup verification
- Patch management
- Security audits
- Endpoint compliance
- Inventory collection across fleet

**Examples:** Remote Desktop, Certificate Management, Patch Management, Security Scans, Backup Verification

## Plugin Lifecycle

```
Registered → Initializing → Running → Stopped
                         ↘ Error ↗
```

| State | Description |
|-------|-------------|
| `registered` | Plugin metadata saved, not yet loaded |
| `initializing` | Plugin setup() is executing |
| `running` | Plugin is active and serving |
| `stopped` | Plugin has been gracefully stopped |
| `error` | Plugin encountered an error |

## Plugin Discovery

1. **Filesystem Discovery**: `PluginLoader` scans `plugins/installed/` for directories containing `plugin.json`
2. **Manifest Validation**: `plugin.json` is parsed and validated against `PluginManifest` schema
3. **Module Import**: The plugin's Python module is dynamically imported via `importlib`
4. **Class Discovery**: The `PluginSDK` subclass is located in the module
5. **Instantiation**: The plugin is instantiated with manifest and config

## Plugin Loading

Plugins are loaded at server startup:

1. Server calls `plugin_loader.discover()` to find all valid plugin directories
2. For each discovered plugin, `plugin_loader.load(slug)` imports and instantiates it
3. After all plugins are loaded, `plugin_loader.setup_all()` calls each plugin's `setup()`
4. Then `plugin_loader.start_all()` calls each plugin's `start()`

## Plugin Isolation

- Plugins run in the same process as the server (server plugins)
- Plugins cannot access other plugins' internal state
- Plugins communicate through the message bus, not direct calls
- Plugin errors are caught and logged without crashing the server
- Plugin configuration is stored in the database, not shared memory

## Plugin Configuration

Each plugin has a `config_json` column in the `plugins` table storing JSON-serialized configuration.

Plugins access their config via `self.config` or `self.get_config(key, default)`.

Configuration changes trigger `on_config_changed(new_config)`.

## Plugin Permissions

Plugins declare required permissions in their manifest:

```json
{
  "permissions": ["read:dashboard", "read:integrations", "execute:commands"]
}
```

Permission format: `action:resource`

Standard actions: `read`, `manage`, `execute`, `collect`
Standard resources: `dashboard`, `integrations`, `commands`, `inventory`, `events`, `projects`

## Plugin Dependencies

Plugins can declare dependencies on other plugins:

```json
{
  "dependencies": ["zabbix", "agent-manager"]
}
```

Dependencies are checked before plugin startup. If a dependency is not installed or not running, the plugin fails to start.

## Plugin Storage

- **Metadata**: PostgreSQL `plugins` table (ORM model: `Plugin`)
- **Configuration**: JSON in `config_json` column
- **Capabilities**: JSON in `capabilities_json` column
- **Filesystem**: `backend/app/plugins/installed/{slug}/` directory

## Plugin Communication

Server ↔ Agent communication uses `PluginMessageBus`:

- Message types: heartbeat, command, result, progress, log, inventory, health, cancel, error
- Priorities: low, normal, high, critical
- Retry logic with exponential backoff
- Dead letter queue for failed messages
- Token-based authentication via `PluginTokenManager`

## Plugin Health

Plugins report health via:
1. **Heartbeat**: Periodic `POST /api/v1/plugins/{id}/heartbeat`
2. **Health Check**: Override `health_check()` to return custom health data
3. **Error Recording**: `record_error()` marks plugin as errored with message

## Plugin Upgrades

1. Replace plugin files in `plugins/installed/{slug}/`
2. Update version in `plugin.json`
3. Server detects version change on next restart
4. Plugin `setup()` runs with new configuration
5. Database migrations (if any) are applied

## Plugin Removal

1. Disable the plugin (stops background tasks)
2. Call `stop()` for graceful shutdown
3. Delete plugin files from filesystem
4. Remove plugin record from database
5. Clean up any plugin-specific database tables
