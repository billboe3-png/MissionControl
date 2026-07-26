# Plugin Operations Guide

**Purpose:** Managing plugins, marketplace, and plugin health  
**Related:** [DASHBOARD.md](./DASHBOARD.md), [AGENTS.md](./AGENTS.md), [AUTOMATION.md](./AUTOMATION.md)

---

## Plugin Overview

Plugins extend Mission Control's capabilities by integrating with external systems and providing additional functionality. Plugins come in three types:

| Type | Description | Runs On | Use Case |
|------|-------------|---------|----------|
| `server` | Runs on the Mission Control server | Server | Data aggregation, API integrations, reporting |
| `agent` | Runs on managed hosts via agents | Agent | Host-level monitoring, local automation |
| `hybrid` | Has components on both server and agent | Both | End-to-end workflows requiring both server and host access |

Plugins are available through the Mission Control marketplace catalog.

---

## Viewing Installed Plugins

**API Endpoint:** `GET /api/v1/plugins`

### Plugin Record

Each installed plugin contains:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique plugin identifier |
| `name` | string | Plugin display name |
| `version` | string | Installed version |
| `latestVersion` | string | Latest available version in marketplace |
| `type` | string | `server`, `agent`, or `hybrid` |
| `status` | string | `active`, `disabled`, `error`, `updating` |
| `health` | object | Plugin health information |
| `description` | string | Plugin description |
| `author` | string | Plugin author |
| `installedAt` | ISO 8601 | Installation timestamp |
| `lastUpdated` | ISO 8601 | Last update timestamp |
| `configuration` | object | Plugin-specific configuration |
| `dependencies` | array | Other plugins this plugin depends on |

### Via Dashboard

1. Navigate to the Plugins section in the main navigation.
2. The installed plugins list shows all plugins with their status and health.
3. Use the filter panel to narrow by type, status, or search term.

---

## Plugin Health

Each plugin reports its own health status, which is aggregated into the overall dashboard health.

### Health Status

| Status | Description | Action |
|--------|-------------|--------|
| `healthy` | Plugin operating normally | None required |
| `degraded` | Plugin experiencing issues but still functional | Review plugin logs, check configuration |
| `error` | Plugin is not functioning correctly | Investigate immediately, check logs |
| `unknown` | Plugin health cannot be determined | Check plugin process, restart if needed |

### Health Check Details

Each plugin health check contains:

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Health status |
| `lastChecked` | ISO 8601 | When health was last verified |
| `checks` | array | Individual health check results |
| `uptime` | integer | Seconds since plugin started |
| `errorCount` | integer | Number of errors in the last hour |
| `warningCount` | integer | Number of warnings in the last hour |

### Viewing Plugin Health

**API Endpoint:** `GET /api/v1/plugins/{pluginId}/health`

**Via Dashboard:**
1. Navigate to the Plugins section.
2. Click on a plugin to open its detail view.
3. The "Health" tab shows detailed health information.

---

## Enabling and Disabling Plugins

### Disabling a Plugin

Use case: Temporarily stop a plugin during troubleshooting or when the plugin is causing issues.

**API Endpoint:** `POST /api/v1/plugins/{pluginId}/disable`

**Procedure:**
1. Navigate to the plugin detail view.
2. Click "Disable Plugin" or call the API endpoint.
3. Confirm the action.
4. The plugin status transitions to `disabled`.

**Considerations:**
- Disabling a plugin may affect features that depend on it.
- Check for dependent plugins before disabling.
- Automation tasks that rely on a disabled plugin will fail.
- Plugin data is preserved when disabled.

### Enabling a Plugin

**API Endpoint:** `POST /api/v1/plugins/{pluginId}/enable`

**Procedure:**
1. Navigate to the plugin detail view.
2. Click "Enable Plugin" or call the API endpoint.
3. The plugin status transitions to `active` after initialization.
4. Verify the plugin health check returns `healthy`.

---

## Plugin Configuration

Plugins may have their own configuration settings.

**API Endpoint:** `GET /api/v1/plugins/{pluginId}/config`  
**API Endpoint:** `PUT /api/v1/plugins/{pluginId}/config`

### Configuration Management

**Via Dashboard:**
1. Navigate to the plugin detail view.
2. Open the "Configuration" tab.
3. Edit configuration fields.
4. Click "Save" to apply changes.
5. The plugin may restart automatically to apply the new configuration.

### Configuration Fields

Each plugin defines its own configuration schema. Common fields include:

| Field | Type | Description |
|-------|------|-------------|
| `apiKey` | secret | API key for external service authentication |
| `endpoint` | string | External service URL |
| `pollingInterval` | integer | How often to poll for data (seconds) |
| `enabled` | boolean | Whether the feature is enabled |
| `logLevel` | string | Logging verbosity (`debug`, `info`, `warn`, `error`) |

### Configuration Security

- Sensitive fields (API keys, passwords) are marked as `secret` type.
- Secret values are masked in the UI and API responses.
- Changes to secret fields are logged in the audit trail.
- Never commit plugin configuration files containing secrets to version control.

---

## Marketplace Browsing

The Mission Control marketplace provides a catalog of available plugins.

**API Endpoint:** `GET /api/v1/plugins/marketplace`

### Marketplace Categories

| Category | Description |
|----------|-------------|
| `monitoring` | Host and service monitoring plugins |
| `automation` | Automation and orchestration plugins |
| `security` | Security scanning and compliance plugins |
| `backup` | Backup and recovery plugins |
| `cloud` | Cloud platform integration plugins |
| `networking` | Network management and monitoring plugins |
| `database` | Database management plugins |
| `logging` | Log collection and analysis plugins |

### Marketplace Entry

Each marketplace entry contains:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Plugin identifier |
| `name` | string | Plugin name |
| `description` | string | What the plugin does |
| `version` | string | Latest version |
| `author` | string | Plugin author or organization |
| `type` | string | `server`, `agent`, or `hybrid` |
| `rating` | float | Community rating (1-5) |
| `downloads` | integer | Total downloads |
| `category` | string | Plugin category |
| `compatibility` | object | Version compatibility information |
| `documentation` | string | Link to plugin documentation |
| `installed` | boolean | Whether the plugin is already installed |

### Installing a Plugin

**API Endpoint:** `POST /api/v1/plugins/marketplace/{pluginId}/install`

**Via Dashboard:**
1. Navigate to the Marketplace section.
2. Browse or search for the desired plugin.
3. Review the plugin description, documentation, and compatibility.
4. Click "Install" to begin installation.
5. Confirm the installation when prompted.
6. Wait for installation to complete.
7. Configure the plugin if required.
8. Verify the plugin health status is `healthy`.

### Updating a Plugin

**API Endpoint:** `POST /api/v1/plugins/{pluginId}/update`

**Via Dashboard:**
1. Navigate to the Plugins section.
2. Plugins with available updates show an "Update Available" badge.
3. Click on the plugin and select "Update".
4. Review the changelog for the new version.
5. Confirm the update.
6. Wait for the update to complete.
7. Verify the plugin is functioning correctly after the update.

---

## Plugin Lifecycle

### Installation Flow

```
Browse Marketplace → Install → Configure → Active
```

### Update Flow

```
Update Available → Review Changelog → Update → Verify Health
```

### Removal Flow

```
Disable → Uninstall → Data Cleanup
```

**API Endpoint:** `DELETE /api/v1/plugins/{pluginId}`

---

## Plugin Troubleshooting

### Plugin Status: Error

1. Navigate to the plugin detail view.
2. Open the "Logs" tab to review error messages.
3. Check the plugin configuration for incorrect values.
4. Verify external service connectivity (for integration plugins).
5. Restart the plugin via the "Restart" button.
6. If the error persists, check the plugin documentation for known issues.

### Plugin Status: Degraded

1. Review the health check details for specific warnings.
2. Check plugin resource usage (CPU, memory).
3. Review plugin logs for recurring warnings.
4. Consider restarting the plugin to clear transient issues.

### Plugin Not Appearing in Marketplace

1. Verify network connectivity from the Mission Control server.
2. Check that the marketplace API endpoint is accessible.
3. Verify the Mission Control version meets the plugin's compatibility requirements.
4. Refresh the marketplace catalog.

### Plugin Causing Performance Issues

1. Check the plugin's resource usage in the health tab.
2. Review the plugin's polling interval and adjust if too frequent.
3. Check for memory leaks by monitoring usage over time.
4. Consider disabling the plugin temporarily while investigating.
5. Report persistent performance issues to the plugin author.
