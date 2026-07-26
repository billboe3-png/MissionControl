# Plugin Versioning

Mission Control plugins follow semantic versioning (semver.org) with additional compatibility rules and constraints.

## Semantic Versioning

### Version Format

```
MAJOR.MINOR.PATCH
```

- **MAJOR**: Breaking changes (incompatible API changes)
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Examples

| Version | Description |
|---------|-------------|
| `1.0.0` | Initial stable release |
| `1.0.1` | Bug fix |
| `1.1.0` | New feature (backward compatible) |
| `2.0.0` | Breaking changes |
| `2.0.1` | Bug fix for 2.0.0 |
| `2.1.0` | New feature for 2.x |

### Pre-release Versions

```
MAJOR.MINOR.PATCH-tag.N
```

- **tag**: Pre-release identifier (alpha, beta, rc)
- **N**: Pre-release number

**Examples:**
- `1.0.0-alpha.1` — First alpha release
- `1.0.0-beta.2` — Second beta release
- `1.0.0-rc.1` — Release candidate

### Build Metadata

```
MAJOR.MINOR.PATCH+build.N
```

**Examples:**
- `1.0.0+build.123`
- `1.0.0+20230101`

Build metadata is ignored for version precedence.

## Compatibility Rules

### Mission Control Compatibility

Plugins declare compatibility with Mission Control versions:

```json
{
  "minMissionControl": "2.0.0",
  "maxMissionControl": "3.0.0"
}
```

| Constraint | Description | Example |
|------------|-------------|---------|
| `^2.0.0` | Compatible with 2.0.0+ | Matches 2.0.0, 2.5.0, but not 3.0.0 |
| `~2.2.0` | Patch-level updates | Matches 2.2.0, 2.2.5, but not 2.3.0 |
| `>=2.0.0` | Minimum version | Matches 2.0.0, 3.0.0 |
| `2.x` | Major version range | Matches 2.0.0, 2.9.9 |
| `2.0.x` | Minor version range | Matches 2.0.0, 2.0.9 |

### Plugin Dependencies

Plugins declare dependencies on other plugins:

```json
{
  "dependencies": {
    "base-plugin": "^1.0.0",
    "monitoring-core": ">=2.0.0",
    "optional-plugin": "~1.2.0"
  }
}
```

### Version Resolution

The runtime resolves versions using these rules:

1. **Exact match**: `1.0.0` matches only `1.0.0`
2. **Caret range**: `^1.0.0` matches `>=1.0.0 <2.0.0`
3. **Tilde range**: `~1.2.0` matches `>=1.2.0 <1.3.0`
4. **Greater than or equal**: `>=1.0.0` matches `1.0.0+`
5. **Less than**: `<2.0.0` matches `<2.0.0`
6. **Range**: `>=1.0.0 <2.0.0` matches within range
7. **Or**: `^1.0.0 || ^2.0.0` matches either range

## Upgrade Paths

### Automatic Upgrades

The runtime automatically upgrades plugins when:

- New patch version is available
- New minor version is available (if configured)
- No breaking changes detected

### Manual Upgrades

Upgrade plugins manually:

```bash
# Upgrade to latest version
mission-control plugin upgrade my-plugin

# Upgrade to specific version
mission-control plugin upgrade my-plugin@1.2.0

# Upgrade all plugins
mission-control plugin upgrade --all
```

### Upgrade Process

1. **Compatibility check**: Verify new version is compatible
2. **Backup**: Create backup of current plugin state
3. **Download**: Fetch new version from marketplace
4. **Validate**: Validate manifest and dependencies
5. **Install**: Extract and install new files
6. **Migrate**: Run migration scripts if needed
7. **Enable**: Enable new version
8. **Verify**: Verify plugin is working correctly

### Migration Scripts

Plugins can include migration scripts for upgrades:

```python
# migrations/upgrade_1_0_to_1_1.py
async def migrate(db):
    """Migrate from 1.0.x to 1.1.x."""
    # Add new column
    await db.execute(
        "ALTER TABLE plugin_data ADD COLUMN new_field TEXT"
    )
    
    # Migrate existing data
    records = await db.fetch_all("SELECT * FROM plugin_data")
    for record in records:
        await db.execute(
            "UPDATE plugin_data SET new_field = ? WHERE id = ?",
            [transform(record.old_field), record.id]
        )
```

## Deprecation Policy

### Deprecation Process

1. **Announce**: Add deprecation notice to changelog
2. **Mark**: Mark deprecated features in documentation
3. **Warn**: Add runtime warnings when deprecated features are used
4. **Remove**: Remove deprecated features in next major version

### Deprecation Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| Announce | 0 months | Deprecation announced in release notes |
| Warn | 3 months | Runtime warnings for deprecated features |
| Remove | 6 months | Deprecated features removed |

### Deprecation Warnings

```python
import warnings

def deprecated_feature():
    """Deprecated feature."""
    warnings.warn(
        "This feature is deprecated and will be removed in v2.0.0. "
        "Use new_feature() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Still works but logs warning
    return new_feature()
```

### Deprecation in Manifest

```json
{
  "deprecated": true,
  "deprecation_message": "This plugin is deprecated. Use advanced-monitoring instead.",
  "replacement": "advanced-monitoring"
}
```

## Version Constraints

### Constraint Syntax

| Syntax | Description | Matches |
|--------|-------------|---------|
| `1.0.0` | Exact version | 1.0.0 |
| `^1.0.0` | Compatible with | >=1.0.0 <2.0.0 |
| `~1.2.0` | Patch updates | >=1.2.0 <1.3.0 |
| `>=1.0.0` | Minimum | >=1.0.0 |
| `<=2.0.0` | Maximum | <=2.0.0 |
| `>1.0.0` | Greater than | >1.0.0 |
| `<2.0.0` | Less than | <2.0.0 |
| `>=1.0.0 <2.0.0` | Range | >=1.0.0 <2.0.0 |
| `^1.0.0 \|\| ^2.0.0` | Or | Either range |

### Examples

```python
from mission_control.versioning import satisfies

# Check version compatibility
satisfies("1.2.3", "^1.0.0")  # True
satisfies("2.0.0", "^1.0.0")  # False
satisfies("1.2.3", "~1.2.0")  # True
satisfies("1.3.0", "~1.2.0")  # False
```

### Conflict Resolution

When multiple plugins have conflicting version requirements:

```python
from mission_control.versioning import resolve_conflicts

# Resolve version conflicts
requirements = [
    "^1.0.0",  # Plugin A requires
    ">=1.5.0", # Plugin B requires
    "~1.2.0"   # Plugin C requires
]

# Find compatible version
version = resolve_conflicts(requirements)
# Result: 1.2.5 (satisfies all constraints)
```

## Version Management

### Checking Versions

```bash
# List installed plugins and versions
mission-control plugin list

# Check for updates
mission-control plugin check-updates

# Show version history
mission-control plugin history my-plugin
```

### Version Pinning

Pin plugin versions in configuration:

```yaml
# mission-control.yaml
plugins:
  my-plugin:
    version: "1.2.3"  # Pinned version
  another-plugin:
    version: "^1.0.0"  # Flexible version
```

### Rollback

Rollback to previous version:

```bash
# Rollback to previous version
mission-control plugin rollback my-plugin

# Rollback to specific version
mission-control plugin rollback my-plugin@1.1.0
```

## Best Practices

1. **Follow semver**: Use semantic versioning strictly
2. **Document changes**: Maintain comprehensive changelog
3. **Test upgrades**: Test upgrade paths thoroughly
4. **Communicate deprecations**: Announce deprecations early
5. **Provide migration guides**: Help users upgrade smoothly
6. **Pin critical plugins**: Pin versions for production stability

## Next Steps

- [MANIFEST.md](MANIFEST.md) — Manifest format reference
- [PLUGIN_SDK.md](PLUGIN_SDK.md) — SDK overview
- [MARKETPLACE.md](MARKETPLACE.md) — Marketplace publishing
- [AGENT_SDK.md](AGENT_SDK.md) — Agent plugin development
- [SERVER_PLUGINS.md](SERVER_PLUGINS.md) — Server plugin development
