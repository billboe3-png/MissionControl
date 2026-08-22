# ARCHITECTURE

## Mission Control from SKYNET's Perspective

SKYNET operates across the complete Mission Control stack.
This document describes topology, data flow, and the immutable rules that govern platform design.

---

## Topology

```text
Operators
   │
   ▼
Dexter UI ──► Mission Control Server ──► Agents
                │
                ├── FastAPI
                ├── Plugin Runtime
                ├── Event Bus
                ├── Redis
                ├── PostgreSQL
                └── Remote Targets
```

### Components

**Mission Control Server**
- Central truth source
- API authority
- Plugin lifecycle manager
- Heartbeat processor
- Inventory aggregator
- Automation dispatcher
- Audit authority

**Agents**
- Lightweight, outbound-only daemons
- Collect local telemetry
- Execute authorized commands
- Report inventory and health
- Sync plugins from server on demand
- Never receive inbound connections

**Heartbeat**
- Periodic signal from agent to server
- Carries health, metrics, plugins, telemetry
- Returns pending commands, targets, and pending plugins
- Establishes operational state
- Drives plugin sync when authorized server-side

**Fleet State Engine**
- Aggregates heartbeats into fleet truth
- Maintains agent status, health, last seen
- Publishes state changes to Event Bus
- Never trusts a single agent report as final truth

**Event Bus**
- Internal pub/sub transport
- Decouples producers from consumers
- Enables correlation across domains
- Maintains replay for RCA and audit

**Automation Engine**
- Executes approved playbooks
- Validates preconditions
- Enforces maintenance windows
- Records execution results
- Never acts without authorization

**Dashboard**
- Operator-facing visualization layer
- Derives from server truth only
- Never bypasses API or access control
- Reflects real data, not cached assumptions

**Plugin Framework**
- Defines lifecycle: discover, load, configure, start, stop, health
- Provides plugin SDK
- Enforces isolation and versioning
- Registers routes via plugin registry

**Marketplace**
- Catalog of available plugins
- Installation lifecycle
- Version compatibility checks
- Integrity verification

**AI Operations Assistant (Dexter)**
- Operates atop SKYNET reasoning
- Never bypasses audit or authorization
- Surfaces evidence, explanations, and recommendations
- Maintains transparent reasoning chains

**Databases**
- PostgreSQL is the persistent truth store
- All schemas are versioned via migrations
- Access is server-side only
- Agents never speak SQL

**Redis**
- Session, cache, queue
- Transient state only
- Not authoritative for business data
- Backed by PostgreSQL for durability

**API**
- Single public contract
- Documented and versioned
- Rate-limited
- Authenticated
- Audited
- Immutable between releases

**Remote Operations**
- Server dispatches commands via agent relay
- Agents target remote systems under explicit server authorization
- Credentials are encrypted, scoped, and rotated per policy
- All remote actions emit audit records

**Enterprise Cloud**
- Multi-tenant, multi-site capable
- Isolation enforced at data and policy layer
- Company and site scoping
- Encrypted secrets at rest
- RBAC enforced server-side

**Community Edition**
- Same core architecture
- Transparent redistribution rights
- Same security and operational posture
- No weakened defaults

---

## Information Flow

```text
Agent ───heartbeat────► Server
Agent ───inventory────► Server
Agent ◄──commands───── Server
Agent ◄──plugins────── Server

Operator ──UI──► Server ◄──API── Services
Services ◄──Event Bus── Plugins
Automation ──dispatch──► Agents (via server)
Audit ───write──► PostgreSQL
Metrics ──emit──► Redis/Cache
```

### Immutable Flow Rules

1. Agents never push directly to databases.
2. UI never reads agent state from anywhere except the server API.
3. Plugins never bypass the plugin framework.
4. Remote targets never connect back to agents.
5. Automation never bypasses authorization.
6. No component may create policy; only operators and configuration may.

---

## Architecture Rules That Must Never Be Violated

- The server is always the truth source.
- Agents are stateless executors of server instructions.
- All secrets are encrypted and scoped.
- All changes are auditable.
- All operations are reversible when possible.
- Security cannot be disabled for convenience.
- Performance optimization never overrides correctness.
- No silent data loss is acceptable.
- Observability is architectural, not optional.
- No AI action is irreversible without human confirmation.

---

## Decision Log

Major architectural decisions are recorded in `docs/decisions/`.
Any change to topology or flow must update this document and the decision log.
