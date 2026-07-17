# SDK Governance

## SDK Versioning

The Plugin SDK follows Semantic Versioning (SemVer):

- **MAJOR** (X.0.0): Breaking changes to public interfaces
- **MINOR** (0.X.0): New extension points, capabilities, or features
- **PATCH** (0.0.X): Bug fixes, documentation, internal improvements

Current version: **3.0.0**

## Compatibility Rules

### Forward Compatibility
- Plugins built for SDK 3.x will work with any SDK 3.x release
- Plugins built for SDK 3.0 will work with SDK 3.1, 3.2, etc.

### Backward Compatibility
- SDK 3.x will not break plugins built for SDK 3.0
- Deprecated features remain available for at least 2 minor versions

### Cross-Version Compatibility
- Plugins built for SDK 3.x may NOT work with SDK 4.x
- Migration guides are provided for major version upgrades

## Deprecation Policy

1. Feature marked with `@deprecated` decorator or docstring
2. Deprecation warning emitted in logs on use
3. Documented in release notes with migration path
4. Remains functional for minimum 2 minor versions
5. Removed in next major version

## Extension Points

Extension points are the public API surface that plugins use to extend the platform.

| Extension Point | Added In | Status |
|----------------|----------|--------|
| `PluginSDK.setup/start/stop` | 3.0.0 | Stable |
| `ServerPluginSDK.get_dashboard_widgets` | 3.0.0 | Stable |
| `ServerPluginSDK.get_routes` | 3.0.0 | Stable |
| `ServerPluginSDK.get_navigation_items` | 3.0.0 | Stable |
| `ServerPluginSDK.get_settings_schema` | 3.0.0 | Stable |
| `ServerPluginSDK.get_providers` | 3.0.0 | Stable |
| `ServerPluginSDK.send_notification` | 3.0.0 | Stable |
| `ServerPluginSDK.get_scheduled_jobs` | 3.0.0 | Stable |
| `ServerPluginSDK.get_models` | 3.0.0 | Stable |
| `AgentPluginSDK.get_commands` | 3.0.0 | Stable |
| `AgentPluginSDK.execute_command` | 3.0.0 | Stable |
| `AgentPluginSDK.get_scheduled_tasks` | 3.0.0 | Stable |
| `AgentPluginSDK.get_health_status` | 3.0.0 | Stable |
| `AgentPluginSDK.collect_inventory` | 3.0.0 | Stable |
| `AgentPluginSDK.collect_performance_counters` | 3.0.0 | Stable |
| `AgentPluginSDK.collect_events` | 3.0.0 | Stable |

## Public vs Private Interfaces

### Public (Stable)
- All methods defined in `PluginSDK`, `ServerPluginSDK`, `AgentPluginSDK`
- `PluginMessageBus` API
- `PluginTokenManager` API
- `PluginManifest` schema
- `PluginCreate/Update/Response` schemas

### Private (Unstable)
- Internal service methods
- Repository implementations
- Database session internals
- Middleware internals
- Router registration internals

## Breaking Changes Policy

A breaking change is any modification to a public interface that causes existing plugins to fail.

Breaking changes require:
1. Major version bump (3.0 → 4.0)
2. Migration guide in release notes
3. Minimum 6-month overlap period where both versions are supported
4. Automated migration tooling when feasible
