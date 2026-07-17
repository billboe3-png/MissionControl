# Architecture Decision Records (ADRs)

This document records key architectural decisions made in Mission Control v3.

## ADR-001: Provider Pattern

**Decision:** Use abstract base classes (ABC) + factory pattern for infrastructure integrations.

**Context:** Mission Control integrates with Zabbix, Hyper-V, Proxmox, and identity providers. Each has different APIs and authentication methods.

**Consequences:**
- Each provider domain has an ABC base class
- Concrete implementations for each vendor
- Mock providers for testing
- Singleton factories with DB/env/mock resolution
- Adding a new vendor requires a new implementation only

## ADR-002: Repository Pattern

**Decision:** Static-method repositories for data access.

**Context:** Need consistent data access across all entities.

**Consequences:**
- Each entity has a repository class with `@staticmethod` methods
- `db: Session` passed as first parameter
- Standard CRUD methods: `get_all`, `get_by_id`, `create`, `update`, `delete`
- No generic base repository (explicit over clever)
- Multi-tenancy filtering via optional parameters

## ADR-003: Service Layer

**Decision:** Service layer between routers and repositories.

**Context:** Business logic should not live in routers or repositories.

**Consequences:**
- Services handle validation, business rules, and orchestration
- Module-level singleton pattern (`service = Service()`)
- Services raise `HTTPException` for API errors
- Services convert ORM objects to Pydantic responses

## ADR-004: Plugin Architecture

**Decision:** Core + Plugin architecture with three execution targets.

**Context:** Mission Control must support vendor-specific integrations without bloating the core.

**Consequences:**
- Core provides frameworks, not features
- Server plugins extend the backend
- Agent plugins extend managed hosts
- Hybrid plugins span both
- All plugins use the SDK public interfaces
- Plugin lifecycle managed by PluginManager

## ADR-005: Distributed Agent Architecture

**Decision:** Agents run on managed hosts, communicate via HTTPS.

**Context:** Direct SSH/WinRM is limited; agents provide richer local capabilities.

**Consequences:**
- Agents register via API key
- Poll-based communication (heartbeat + command pickup)
- Agent plugins execute locally
- Server orchestrates, agent executes
- Agent inventory reported via heartbeat

## ADR-006: Automation Engine

**Decision:** Playbook-based automation with step execution.

**Context:** IT operations require repeatable, auditable procedures.

**Consequences:**
- Playbooks contain ordered steps
- Steps support variable substitution
- Approval workflows for sensitive operations
- Cron and event-based triggers
- Full execution audit trail

## ADR-007: Message Bus

**Decision:** In-memory message bus for plugin communication.

**Context:** Plugins need to communicate without direct coupling.

**Consequences:**
- `PluginMessageBus` with publish/subscribe
- Retry logic with exponential backoff
- Dead letter queue for failed messages
- Token-based authentication
- Scalable to Redis Pub/Sub for production

## ADR-008: Multi-Tenant Design

**Decision:** Company → Site → Resource hierarchy.

**Context:** Enterprise and MSP customers need tenant isolation.

**Consequences:**
- `company_id` and `site_id` on most models
- Queries filtered by tenant context
- Cross-tenant access blocked at service layer
- Dashboard aggregations respect tenant scope

## ADR-009: Dashboard Architecture

**Decision:** Widget-based dashboard with provider data sources.

**Context:** Dashboard needs to show data from multiple sources.

**Consequences:**
- Dashboard service aggregates from providers
- Each provider returns a data dict
- Widgets render provider data
- Graceful error handling per provider
- Plugin-contributed widgets via SDK

## ADR-010: REST API Structure

**Decision:** `/api/v1/` prefix with domain-based routing.

**Context:** Need consistent API structure for frontend and plugins.

**Consequences:**
- All endpoints under `/api/v1/`
- One router per domain
- Standard CRUD + action endpoints
- OpenAPI documentation auto-generated
- Rate limiting on all endpoints
