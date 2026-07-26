# Mission Control — Components

**Version:** 3.0.0

---

## Overview

Mission Control is composed of 14 major components. Each component has a single responsibility and communicates through the event bus or well-defined service interfaces.

---

## Server Components

### 1. Authentication Service

**Path:** `backend/app/services/auth_service.py`
**Router:** `backend/app/routers/auth.py`

Handles JWT-based authentication, token refresh, and user management.

- JWT access tokens (HS256, configurable expiry)
- Refresh tokens with rotation
- API key authentication for agents
- Password hashing (bcrypt)
- Company-scoped user isolation

### 2. Dashboard Aggregator

**Path:** `backend/app/services/dashboard_service.py`
**Router:** `backend/app/routers/dashboard.py`

Orchestrates all dashboard data through domain services. Never queries the database directly.

```
Dashboard Router
    → DashboardService
        → AgentService.get_dashboard_summary()
        → AutomationService.get_automation_summary()
        → IntegrationService.get_dashboard_summary()
        → AIService.get_overview()
        → HealthProvider.get_health()
        → ProjectProvider, TaskProvider, NoteProvider, etc.
```

### 3. Automation Engine

**Path:** `backend/app/services/automation_service.py`
**Router:** `backend/app/routers/automation.py`

Playbook-driven execution engine with approval workflows.

- Playbooks with ordered steps
- Step types: script, HTTP, agent command, conditional
- Variables and templating
- Approval workflows with multi-level sign-off
- Execution history and audit trail
- Cron-based scheduling
- Event triggers

### 4. AI Operations

**Path:** `backend/app/ai/`

AI-powered operations intelligence.

| Module | Purpose |
|--------|---------|
| `ai_engine.py` | Orchestrates AI analysis |
| `ai_provider.py` | LLM provider abstraction (OpenAI, Anthropic, etc.) |
| `ai_service.py` | Service layer for AI endpoints |
| `confidence_engine.py` | Confidence scoring for recommendations |
| `correlation_engine.py` | Alert correlation across sources |
| `incident_classifier.py` | Incident severity classification |
| `recommendation_engine.py` | Actionable recommendation generation |

### 5. Plugin Framework

**Path:** `backend/app/plugins/`

| Module | Purpose |
|--------|---------|
| `base.py` | Abstract base class for all plugins |
| `server.py` | Server plugin SDK |
| `agent.py` | Agent plugin SDK |
| `communication.py` | Plugin communication protocol |
| `loader.py` | Dynamic plugin loading |

See [PLUGINS.md](PLUGINS.md) for full details.

### 6. Event Bus

**Path:** `backend/app/events/__init__.py`

In-process async pub/sub system for decoupled component communication.

- 34 typed event types across 8 categories
- Decorator-based subscription
- Event history with configurable retention
- Error isolation (one failing handler doesn't affect others)

See [EVENT_BUS.md](EVENT_BUS.md) for full details.

### 7. Heartbeat Service

**Path:** `backend/app/heartbeat/__init__.py`

Processes all agent heartbeats through a single pipeline.

- Authenticates agent via API key
- Updates agent status, health, and metrics
- Fetches pending commands for delivery
- Returns remote targets for relay
- Publishes heartbeat events to the event bus

See [HEARTBEAT.md](HEARTBEAT.md) for full details.

### 8. Agent State Engine

**Path:** `backend/app/state/__init__.py`

Centralized state management for all agents.

- 9 possible states: Online, Offline, Warning, Healthy, Unhealthy, Updating, Pending, Executing, Disabled
- State transition tracking with event publishing
- In-memory cache for fast lookups
- Bulk refresh for dashboard queries

### 9. Scheduler

**Path:** `backend/app/services/automation_service.py` (playbook schedules)

Cron-like scheduling for automation playbooks and periodic tasks.

- Cron expression parsing
- Playbook schedule management
- Execution history tracking
- Missed schedule recovery

### 10. Notifications

**Path:** `backend/app/services/` (integrated into automation and agent services)

Alert routing and notification delivery.

- Alert creation from agent health changes
- Alert resolution tracking
- Notification routing (email, webhook, future: Slack/Teams)

### 11. Inventory

**Path:** `backend/app/services/agent_service.py` (inventory endpoints)

Aggregates agent-reported inventory data.

- System inventory (OS, hardware, network)
- Software inventory
- Service inventory
- Remote target inventory

### 12. REST API

**Path:** `backend/app/routers/` (25 routers, 286 endpoints)

FastAPI-based REST API with OpenAPI documentation.

See [API.md](API.md) for full details.

---

## Agent Components

### 13. Agent Orchestrator

**Path:** `.agents/agent/agent.py`

Main agent process that coordinates all agent activities.

- Heartbeat loop (configurable interval)
- Command queue processing
- Plugin lifecycle management
- Inventory collection
- Offline queue management

See [AGENTS.md](AGENTS.md) for full details.

### 14. Database

**Path:** `backend/app/db/`, `backend/app/models/db/`

PostgreSQL database with 29 tables and Alembic migrations.

See [DATABASE.md](DATABASE.md) for full details.

---

## Provider Subsystems

Providers are integration-specific modules that handle communication with external platforms.

| Provider | Path | Purpose |
|----------|------|---------|
| **Hyper-V** | `providers/hyperv/` | VM management, checkpoints, replication |
| **Proxmox** | `providers/proxmox/` | VE nodes, VMs, containers, storage |
| **Zabbix** | `providers/zabbix/` | Monitoring host data, problems, triggers |
| **Veeam** | `providers/veeam/` | Backup jobs, sessions, repositories |
| **Identity** | `providers/identity/` | Active Directory, Microsoft 365 |
| **Remote** | `providers/remote/` | SSH, WinRM (fallback only) |
| **Automation** | `providers/automation/` | Execution providers (agent, SSH, WinRM, HTTP) |
| **Virtualization** | `providers/virtualization/` | Shared virtualization models |

Each provider follows the factory pattern:

```
Provider Factory → Agent Provider (primary) or Direct Provider (fallback)
```

---

## Component Count Summary

| Category | Count |
|----------|-------|
| Backend directories | 14 |
| Routers | 25 |
| Services | 24 |
| Database models | 29 |
| Provider subsystems | 8 |
| Plugin files | 6 |
| Event types | 34 |
| Agent states | 9 |
| API endpoints | 286 |
| Frontend pages | 78 |
| Config settings | 42 |
