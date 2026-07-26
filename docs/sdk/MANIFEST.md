# Plugin Manifest Format

Every Mission Control plugin requires a `manifest.json` file at its root. The manifest defines the plugin's metadata, capabilities, permissions, dependencies, and configuration.

## Schema

```json
{
  "name": "string",
  "version": "string",
  "type": "string",
  "description": "string",
  "author": "string",
  "license": "string",
  "homepage": "string",
  "repository": "string",
  "minMissionControl": "string",
  "maxMissionControl": "string",
  "capabilities": ["string"],
  "permissions": ["string"],
  "entry": {
    "server": "string",
    "agent": "string"
  },
  "config": {
    "key": {
      "type": "string",
      "required": boolean,
      "default": "any",
      "description": "string",
      "enum": ["string"]
    }
  },
  "dependencies": {
    "plugin-name": "version-constraint"
  },
  "metadata": {
    "icon": "string",
    "categories": ["string"],
    "tags": ["string"],
    "screenshots": ["string"],
    "changelog": "string"
  }
}
```

## Required Fields

### name

Unique identifier for the plugin. Use lowercase letters, numbers, and hyphens.

```json
{
  "name": "my-custom-plugin"
}
```

**Rules:**
- Must be unique across the marketplace
- Maximum 64 characters
- Only lowercase letters, numbers, and hyphens
- Must start with a letter

### version

Semantic version number following semver.org spec.

```json
{
  "version": "1.2.3"
}
```

**Format:** `MAJOR.MINOR.PATCH`
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

See [VERSIONING.md](VERSIONING.md) for details.

### type

Plugin type indicating runtime environment.

```json
{
  "type": "hybrid"
}
```

**Valid values:**
- `server` — Runs on Mission Control server
- `agent` — Runs on agent hosts
- `hybrid` — Runs on both server and agents

### description

Brief description of the plugin's purpose (max 500 characters).

```json
{
  "description": "Advanced monitoring plugin for system metrics collection and alerting"
}
```

### author

Plugin author or organization name.

```json
{
  "author": "Mission Control Team"
}
```

### license

License identifier (SPDX format).

```json
{
  "license": "MIT"
}
```

**Common licenses:**
- `MIT`
- `Apache-2.0`
- `GPL-3.0`
- `BSD-3-Clause`
- `Proprietary`

## Optional Fields

### homepage

URL to the plugin's homepage or documentation.

```json
{
  "homepage": "https://github.com/mission-control/my-plugin"
}
```

### repository

URL to the plugin's source repository.

```json
{
  "repository": "https://github.com/mission-control/my-plugin"
}
```

### minMissionControl

Minimum required Mission Control version.

```json
{
  "minMissionControl": "2.0.0"
}
```

### maxMissionControl

Maximum supported Mission Control version.

```json
{
  "maxMissionControl": "3.0.0"
}
```

## Capabilities Array

Capabilities declare what the plugin can do. The runtime validates capabilities at install time and gates access accordingly.

```json
{
  "capabilities": [
    "event.subscribe",
    "event.publish",
    "rest.extend",
    "router.mount",
    "service.access",
    "database.access",
    "inventory.collect",
    "command.execute",
    "health.check",
    "config.read",
    "config.write",
    "websocket.connect",
    "middleware.register",
    "scheduler.register"
  ]
}
```

### Capability Reference

| Capability | Description | Plugin Type |
|------------|-------------|-------------|
| `event.subscribe` | Subscribe to event bus events | All |
| `event.publish` | Publish events to event bus | All |
| `rest.extend` | Add REST API routes | Server, Hybrid |
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

See [PLUGIN_SDK.md](PLUGIN_SDK.md) for capability details.

## Permissions

Permissions control what resources the plugin can access.

```json
{
  "permissions": [
    "read:agents",
    "read:inventory",
    "write:inventory",
    "execute:commands",
    "admin:plugins"
  ]
}
```

### Permission Types

- **read**: View data
- **write**: Create and modify data
- **execute**: Perform actions
- **admin**: Elevated access

See [PERMISSIONS.md](PERMISSIONS.md) for the complete permissions reference.

## Dependencies

Declare dependencies on other plugins.

```json
{
  "dependencies": {
    "base-plugin": "^1.0.0",
    "monitoring-core": ">=2.0.0",
    "optional-plugin": "~1.2.0"
  }
}
```

### Version Constraints

| Constraint | Description | Example |
|------------|-------------|---------|
| `^1.0.0` | Compatible with 1.0.0+ | `^1.0.0` matches 1.0.0, 1.2.3, but not 2.0.0 |
| `~1.2.0` | Patch-level updates | `~1.2.0` matches 1.2.0, 1.2.5, but not 1.3.0 |
| `>=2.0.0` | Minimum version | `>=2.0.0` matches 2.0.0, 3.0.0 |
| `1.x` | Major version range | `1.x` matches 1.0.0, 1.9.9 |
| `1.2.x` | Minor version range | `1.2.x` matches 1.2.0, 1.2.9 |

See [VERSIONING.md](VERSIONING.md) for versioning details.

## Entry Points

Define entry points for each plugin type.

```json
{
  "entry": {
    "server": "server/index.py",
    "agent": "agent/index.py"
  }
}
```

### Server Entry Point

```python
# server/index.py
from mission_control.plugins import ServerPlugin

class MyServerPlugin(ServerPlugin):
    async def on_enable(self, app, db, services):
        # Server plugin initialization
        pass
    
    async def on_disable(self, app, db, services):
        # Server plugin cleanup
        pass

plugin = MyServerPlugin()
```

See [SERVER_PLUGINS.md](SERVER_PLUGINS.md) for server plugin development.

### Agent Entry Point

```python
# agent/index.py
from mission_control_agent.plugins import AgentPlugin

class MyAgentPlugin(AgentPlugin):
    async def on_enable(self, agent):
        # Agent plugin initialization
        pass
    
    async def on_disable(self, agent):
        # Agent plugin cleanup
        pass

plugin = MyAgentPlugin()
```

See [AGENT_SDK.md](AGENT_SDK.md) for agent plugin development.

## Configuration

Declare configuration fields for the plugin.

```json
{
  "config": {
    "api_key": {
      "type": "string",
      "required": true,
      "description": "API key for external service"
    },
    "interval": {
      "type": "integer",
      "required": false,
      "default": 60,
      "description": "Collection interval in seconds"
    },
    "log_level": {
      "type": "string",
      "required": false,
      "default": "info",
      "enum": ["debug", "info", "warning", "error"],
      "description": "Logging level"
    },
    "enabled_features": {
      "type": "list",
      "required": false,
      "default": ["feature1"],
      "description": "List of enabled features"
    }
  }
}
```

### Configuration Types

| Type | Description | Example |
|------|-------------|---------|
| `string` | Text value | `"api-key-123"` |
| `integer` | Whole number | `60` |
| `float` | Decimal number | `1.5` |
| `boolean` | True/false | `true` |
| `list` | Array of values | `["a", "b"]` |
| `dict` | Key-value pairs | `{"key": "value"}` |

### Configuration Options

| Option | Description | Required |
|--------|-------------|----------|
| `type` | Field type | Yes |
| `required` | Whether field is required | Yes |
| `default` | Default value | No |
| `description` | Human-readable description | No |
| `enum` | Allowed values | No |
| `min` | Minimum value (integer/float) | No |
| `max` | Maximum value (integer/float) | No |
| `pattern` | Regex pattern (string) | No |

## Metadata

Additional plugin metadata for marketplace display.

```json
{
  "metadata": {
    "icon": "icon.png",
    "categories": ["monitoring", "utilities"],
    "tags": ["system", "metrics", "alerting"],
    "screenshots": ["screenshot1.png", "screenshot2.png"],
    "changelog": "CHANGELOG.md"
  }
}
```

### Icon

Path to plugin icon (PNG format, recommended 128x128).

```json
{
  "icon": "assets/icon.png"
}
```

### Categories

Marketplace categories for the plugin.

```json
{
  "categories": ["monitoring", "utilities", "security"]
}
```

**Available categories:**
- `monitoring` — System and application monitoring
- `utilities` — General utilities and tools
- `security` — Security and access control
- `automation` — Workflow automation
- `integration` — Third-party integrations
- `backup` — Backup and recovery
- `networking` — Network management
- `database` — Database operations
- `development` — Development tools

### Tags

Searchable tags for the plugin.

```json
{
  "tags": ["system", "metrics", "alerting", "prometheus"]
}
```

### Screenshots

Paths to marketplace screenshots.

```json
{
  "screenshots": [
    "assets/screenshot1.png",
    "assets/screenshot2.png"
  ]
}
```

### Changelog

Path to changelog file.

```json
{
  "changelog": "CHANGELOG.md"
}
```

## Complete Example

```json
{
  "name": "advanced-monitoring",
  "version": "2.1.0",
  "type": "hybrid",
  "description": "Advanced monitoring plugin with custom metrics, alerting, and dashboard integration",
  "author": "Mission Control Team",
  "license": "MIT",
  "homepage": "https://github.com/mission-control/advanced-monitoring",
  "repository": "https://github.com/mission-control/advanced-monitoring",
  "minMissionControl": "2.0.0",
  "maxMissionControl": "3.0.0",
  "capabilities": [
    "event.subscribe",
    "event.publish",
    "rest.extend",
    "router.mount",
    "service.access",
    "database.access",
    "inventory.collect",
    "command.execute",
    "health.check",
    "config.read",
    "config.write",
    "scheduler.register"
  ],
  "permissions": [
    "read:agents",
    "read:inventory",
    "write:inventory",
    "execute:commands",
    "read:alerts",
    "write:alerts"
  ],
  "entry": {
    "server": "server/index.py",
    "agent": "agent/index.py"
  },
  "config": {
    "server": {
      "api_key": {
        "type": "string",
        "required": true,
        "description": "API key for external monitoring service"
      },
      "sync_interval": {
        "type": "integer",
        "required": false,
        "default": 300,
        "description": "Data sync interval in seconds"
      }
    },
    "agent": {
      "collect_interval": {
        "type": "integer",
        "required": false,
        "default": 60,
        "description": "Metrics collection interval in seconds"
      },
      "batch_size": {
        "type": "integer",
        "required": false,
        "default": 100,
        "description": "Number of metrics to batch before sending"
      }
    }
  },
  "dependencies": {
    "base-monitoring": "^1.0.0"
  },
  "metadata": {
    "icon": "assets/icon.png",
    "categories": ["monitoring", "utilities"],
    "tags": ["system", "metrics", "alerting", "prometheus", "grafana"],
    "screenshots": [
      "assets/dashboard.png",
      "assets/alerts.png"
    ],
    "changelog": "CHANGELOG.md"
  }
}
```

## Validation

Validate manifest before publishing:

```python
from mission_control.plugins import ManifestValidator

validator = ManifestValidator()
errors = validator.validate(manifest)

if errors:
    for error in errors:
        print(f"Error: {error}")
else:
    print("Manifest is valid")
```

## Next Steps

- [PLUGIN_SDK.md](PLUGIN_SDK.md) — SDK overview
- [VERSIONING.md](VERSIONING.md) — Versioning details
- [PERMISSIONS.md](PERMISSIONS.md) — Permissions reference
- [AGENT_SDK.md](AGENT_SDK.md) — Agent plugin development
- [SERVER_PLUGINS.md](SERVER_PLUGINS.md) — Server plugin development
- [MARKETPLACE.md](MARKETPLACE.md) — Marketplace publishing
