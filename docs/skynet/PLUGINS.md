# PLUGINS

## Philosophy

Plugins are the extension mechanism for Mission Control.
They exist to isolate capability, enforce boundaries, and evolve functionality independently of the platform core.

Every plugin must:
- solve one problem well
- declare its inputs and outputs
- fail predictably under all conditions
- report health accurately
- expose telemetry for RCA and observability

## Lifecycle

Plugin lifecycle states:
```text
discovered
    │
    ▼
registered
    │
    ▼
configured
    │
    ▼
started
    │
    ▼
running
    │
    ▼
stopped / failed / disabled
```

Lifecycle rules:
- Transitions are explicit and auditable
- No silent bypass of lifecycle states
- Health checks run continuously for running plugins
- Failed plugins stop automatically
- Recovery requires explicit re-enable or server action
- Plugin execution does not block the server event loop

## Isolation

Plugins run in isolated processes where possible.
When not possible, they run in isolated contexts with:
- declared permission scope
- sandboxed filesystem access
- bounded resource usage
- scoped environment variables

Isolation prevents plugin failure from becoming platform failure.

## Versioning

Plugin versioning rules:
- Semantic versioning enforced
- Breaking changes require marketplace review period
- Version compatibility checked before installation
- Rollback supported to prior signed version
- Multiple versions may coexist during migration

## Marketplace

The marketplace is the only authorized distribution path for plugins.
Marketplace rules:
- All plugins signed by known key
- Author metadata mandatory
- License metadata mandatory
- Security review before publication
- Deprecation policy enforced
- Removal policy enforced
- Compatibility matrix published

## Signing

Plugin signing rules:
- Only signed plugins may load in production
- Unsigned plugins load only in explicit developer mode
- Signing keys rotated annually
- Compromised keys trigger immediate revocation and reissuance

## Dependencies

Plugin dependencies:
- Must be declared in plugin manifest
- Must pass compatibility check
- Must not conflict with core dependencies
- Must not introduce transitive supply chain risk
- Isolation preferred over shared state

## Health

Plugin health states:
- healthy: operating normally
- degraded: partial or delayed collection
- failed: non-recoverable error without intervention
- disabled: explicitly stopped by operator

Health transitions:
- emit events to Event Bus
- update plugin registry
- update agent plugin state if applicable
- trigger remediation automation when policy defines

## Compatibility

Compatibility rules:
- major version changes require migration path
- minor versions pass backward compatibility tests
- patch versions never change contract
- Deprecated interfaces remain supported for two minor release cycles
- Removal requires two-cycle deprecation notice

## SDK

The Plugin SDK provides:
- standardized interface contracts
- health, logging, and telemetry primitives
- authentication helpers
- error classification helpers
- testing harness
- packaging and manifest helpers

SDK versions are tied to platform versions.
Plugin authors must target supported SDK versions.

## Enterprise Plugins

Enterprise plugins:
- require enterprise contract
- include support SLAs
- include security review records
- include signed manifests
- include compatibility certification
- receive security patch communication

## Community Plugins

Community plugins:
- reviewed for basic security before publication
- marked as community-built
- carry community support model
- carry community liability understanding
- may be adopted or rejected by enterprise catalog

Community plugins that solve enterprise needs may be elevated to enterprise status.

## Failure Handling

Plugin failure rules:
- No panic or exception suppression
- No silent degradation
- No undefined behavior exposure to operators
- Failure reason published to telemetry
- Failure correlation flagged to RCA if repeated

```text
FAIL VISIBLY
FAIL LOUDLY
FAIL EARLY
FAIL RECOVERABLY
```
