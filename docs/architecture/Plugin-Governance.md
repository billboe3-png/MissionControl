# Plugin Governance

Rules for plugin lifecycle, compatibility, and policy.

## Plugin Policy

### What MUST Be a Plugin

Any functionality that is:
- Vendor-specific
- Optional (not required by every customer)
- Independently updatable
- Vendor-dependent on external APIs

### What MUST NOT Be a Plugin

Core platform functionality:
- Authentication and authorization
- User and role management
- Multi-tenancy
- Dashboard framework
- Navigation framework
- Plugin management itself
- REST API infrastructure
- Database and caching
- Logging and health checks
- Configuration management

## Compatibility Rules

### SDK Compatibility

- Plugins declare `min_core_version` in their manifest
- Server checks compatibility before loading
- Incompatible plugins are rejected with clear error messages

### Breaking Changes

- Plugins must not depend on internal server implementation details
- Only SDK public interfaces are guaranteed stable
- Private interfaces may change without notice

## Deprecation Policy

1. Feature is marked `@deprecated` in the SDK
2. Deprecation is documented in release notes
3. Minimum two minor versions of support after deprecation
4. Feature is removed in next major version

## Plugin Upgrades

- Plugin upgrades are independent of core platform upgrades
- Plugins may upgrade their own database migrations
- Configuration schema changes are backward-compatible within major versions
- Plugin version follows semver: `MAJOR.MINOR.PATCH`

## Plugin Removal

When removing a plugin from the marketplace:
1. Announce removal 90 days in advance
2. Provide migration guide if alternative exists
3. Mark plugin as deprecated in catalog
4. After 90 days, remove from catalog
5. Existing installations continue to work

## Support Levels

| Level | Description |
|-------|-------------|
| Official | Maintained by Mission Control team |
| Certified | Reviewed and approved by Mission Control |
| Community | Community-contributed, not reviewed |
| Private | Organization-internal, not published |
