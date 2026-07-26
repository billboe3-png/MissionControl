# Mission Control Architecture Guide

**Version:** 3.0.0 — Community Edition v1.0
**Status:** Frozen
**Last Updated:** 2026-07-26

---

## 1. Mission Statement

Mission Control is an open-source IT Operations Platform built around a centralized web server and lightweight agents that monitor, manage, and automate infrastructure through a plugin-driven architecture.

It provides a single pane of glass for:

- **Multi-tenant infrastructure management** — companies, sites, and role-based access
- **Agent-first monitoring** — lightweight agents collect data; the server never polls directly
- **Automation** — playbook-driven execution with approval workflows and audit trails
- **AI Operations** — incident correlation, recommendations, and health scoring
- **Plugin ecosystem** — server plugins, agent plugins, and a marketplace for extensions
- **Remote operations** — SSH/WinRM fallback for devices that cannot run agents

Mission Control runs anywhere: Docker Compose on a single server, Google Cloud, AWS, Azure, Proxmox LXC, or a future high-availability cluster. Community and Enterprise share one codebase, differentiated by configuration.

---

## 2. Design Principles

| Principle | Description |
|-----------|-------------|
| **Agent-first** | All infrastructure data flows through agents. The server never directly polls infrastructure when an agent is available. SSH/WinRM are fallback-only. |
| **API-first** | Every feature is exposed through a REST API. The web dashboard is a consumer of the same API that agents and integrations use. |
| **Plugin-first** | Core platform provides authentication, scheduling, and orchestration. All infrastructure knowledge lives in plugins. |
| **Event-driven** | Components communicate through an internal event bus. No direct method calls between unrelated services. |
| **Secure by default** | JWT authentication, Fernet encryption for secrets, TLS for transport, API key authentication for agents. |
| **Multi-tenant** | Company → Site hierarchy with data isolation. Every query is scoped to the authenticated tenant. |
| **Cloud-ready** | Same codebase runs on Docker Compose (community) or cloud-managed infrastructure (enterprise). |
| **Single codebase** | Community and Enterprise editions share all source code. Edition is a configuration flag, not a fork. |
| **Configuration over customization** | Features are enabled/disabled through configuration, not code modifications. |
| **Dashboard aggregation** | The dashboard delegates to domain services. It never queries the database directly. |

---

## 3. High-Level Architecture

```
                    +----------------------+
                    |    Web Dashboard     |
                    |   (React / Vite)     |
                    +----------+-----------+
                               |
                         REST API / HTTPS
                               |
+--------------------------------------------------------------+
|                   Mission Control Server                      |
|  Python 3.12 · FastAPI · SQLAlchemy · Pydantic               |
|--------------------------------------------------------------|
|                                                               |
|  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐  |
|  │    Auth      │  │  Dashboard   │  │    Automation      │  |
|  │   (JWT)     │  │ Aggregator   │  │  (Playbooks/Steps) │  |
|  └─────────────┘  └──────────────┘  └────────────────────┘  |
|                                                               |
|  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐  |
|  │     AI       │  │   Plugin     │  │    Scheduler       │  |
|  │  Operations  │  │  Framework   │  │                    │  |
|  └─────────────┘  └──────────────┘  └────────────────────┘  |
|                                                               |
|  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐  |
|  │  Event Bus   │  │  Heartbeat   │  │  Agent State       │  |
|  │  (pub/sub)   │  │  Service     │  │  Engine            │  |
|  └─────────────┘  └──────────────┘  └────────────────────┘  |
|                                                               |
|  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐  |
|  │  Inventory   │  │ Notifications│  │   REST API         │  |
|  │              │  │              │  │  (286 endpoints)   │  |
|  └─────────────┘  └──────────────┘  └────────────────────┘  |
|                                                               |
+--------------------------------------------------------------+
           |                    |                    |
           |                    |                    |
    ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
    │  PostgreSQL  │   │    Redis     │   │  Plugin SDK  │
    │   (29 tables)│   │  (cache/queue)│   │              │
    └──────────────┘   └──────────────┘   └──────────────┘
           |
           |
  ┌────────────────────────────────────────────────────────┐
  |                    Agent Fleet                          |
  |--------------------------------------------------------|
  |  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐  |
  |  |Windows Agent  | | Linux Agent  | | Future Agent  |  |
  |  | (PowerShell)  | |   (Bash)     | |  (Python)     |  |
  |  └──────────────┘ └──────────────┘ └──────────────┘  |
  |                                                        |
  |  Capabilities:                                         |
  |  · Heartbeat · Inventory · Metrics · Health            |
  |  · Command Execution · Plugin Loading · Offline Queue  |
  |  · Remote Target Relay · Event Collection               |
  └────────────────────────────────────────────────────────┘
```

---

## 4. Server Responsibilities

The server is the central orchestration point. It handles:

| Responsibility | Description |
|----------------|-------------|
| **Authentication** | JWT token issuance, refresh, and validation. API key authentication for agents. |
| **Authorization** | Role-based access control (RBAC) with company/site scoping. |
| **Dashboard** | Aggregates data from all domain services into a single API response. |
| **Heartbeat** | Receives and processes agent heartbeats. Updates agent state. Queues pending commands. |
| **Command Queue** | Queues commands for agents. Dispatches on next heartbeat. Tracks execution status. |
| **Automation** | Playbook engine with steps, variables, schedules, approvals, and audit trails. |
| **AI Operations** | Incident correlation, recommendation engine, health scoring, confidence engine. |
| **Plugin Framework** | Server plugin loading, lifecycle management, marketplace catalog. |
| **Inventory** | Aggregates agent-reported inventory data. |
| **Reporting** | Dashboard widgets, health views, automation summaries. |
| **Notifications** | Alert routing and notification delivery. |
| **Scheduler** | Cron-like scheduling for playbooks and periodic tasks. |
| **REST API** | 286 endpoints across 25 routers. OpenAPI/Swagger documentation. |
| **Database** | PostgreSQL with 29 tables, Alembic migrations, connection pooling. |

---

## 5. Agent Responsibilities

Agents are lightweight, self-updating processes that run on managed infrastructure.

| Responsibility | Description |
|----------------|-------------|
| **Heartbeat** | Sends periodic heartbeats to the server with health and metrics. |
| **Inventory** | Collects system inventory (OS, hardware, services, software). |
| **Metrics** | Reports CPU, memory, disk, and network metrics. |
| **Health** | Reports service health status and checks. |
| **Command Execution** | Executes commands received from the server via PowerShell or Bash. |
| **Service Monitoring** | Monitors Windows/Linux services and reports status changes. |
| **Event Collection** | Collects system events and forwards to the server. |
| **Hardware Inventory** | Reports hardware details (CPU, memory, disks, network adapters). |
| **Plugin Execution** | Loads and executes agent plugins for platform-specific collection. |
| **Local Playbooks** | Executes locally-cached playbooks when network is unavailable. |
| **Offline Queue** | Queues results and events when offline. Sends on reconnect. |
| **Remote Target Relay** | Connects to remote machines via SSH/WinRM and relays data to the server. |

---

## 6. Communication Model

All communication is agent-initiated. The server never initiates connections to agents.

```
Agent                                    Server
  |                                        |
  |──── POST /agents/{id}/register ──────>|  Registration
  |<──── API Key ─────────────────────────|  (one-time)
  |                                        |
  |──── POST /agents/{id}/heartbeat ─────>|  Heartbeat (every 30s)
  |<──── commands[] + remote_targets[] ───|  Response
  |                                        |
  |──── POST /agents/{id}/inventory ─────>|  Inventory upload
  |                                        |
  |──── POST /agents/{id}/commands/{id}──>|  Command result
  |                                        |
  |──── POST /agents/{id}/events ────────>|  Event upload
  |                                        |
```

### Communication Types

| Type | Direction | Frequency | Purpose |
|------|-----------|-----------|---------|
| **Registration** | Agent → Server | Once | Agent registers, receives API key |
| **Heartbeat** | Agent → Server | Every 30s | Health, metrics, pending commands |
| **Command Result** | Agent → Server | Per command | Execution output and status |
| **Inventory** | Agent → Server | On change | System inventory update |
| **Events** | Agent → Server | Real-time | System events and alerts |
| **Commands** | Server → Agent | Via heartbeat | Queued commands for execution |
| **Remote Targets** | Server → Agent | Via heartbeat | Machines the agent should relay |

---

## 7. Execution Flow

```
User clicks "Execute" in Dashboard
        |
        v
Dashboard POST /api/v1/remote/execute
        |
        v
Remote Service checks for online agent
        |
        +--- Agent available? ──> Queue command for agent
        |                              |
        |                              v
        |                    Agent heartbeat picks up command
        |                              |
        |                              v
        |                    Agent executes via local plugin
        |                              |
        |                              v
        |                    Agent posts result to server
        |                              |
        |                              v
        |                    Server updates command history
        |                              |
        v                              v
   Fallback to SSH/WinRM        Dashboard shows result
   (direct connection)
```

---

## 8. Deployment Models

### Community Edition

```
Docker Compose
    |
    ├── Mission Control Server (FastAPI + Uvicorn)
    ├── PostgreSQL 16
    ├── Redis 7
    └── Nginx (reverse proxy)

Agents run on managed infrastructure
    |
    ├── Windows Agent (PowerShell)
    └── Linux Agent (Bash)
```

### Enterprise Edition

```
Cloud (GCP / AWS / Azure)
    |
    ├── Mission Control Server (Docker or K8s)
    ├── Managed PostgreSQL
    ├── Managed Redis
    └── Load Balancer

Agents run on managed infrastructure
    |
    ├── Windows Agent
    ├── Linux Agent
    └── Agent Relay Chains (multi-region)
```

### Future: High Availability

```
Load Balancer
    |
    ├── Mission Control Server (replica 1)
    ├── Mission Control Server (replica 2)
    ├── Mission Control Server (replica 3)
    ├── Shared PostgreSQL (primary + replicas)
    └── Shared Redis (sentinel)
```

---

## 9. Technology Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2.0, Pydantic v2 |
| **Frontend** | TypeScript, React 18, Vite, React Router |
| **Database** | PostgreSQL 16 |
| **Cache** | Redis 7 |
| **Agent** | Python 3.12 (no external dependencies) |
| **Agent Plugins** | PowerShell (Windows), Bash (Linux) |
| **Encryption** | Fernet (AES-128-CBC), JWT (HS256) |
| **Deployment** | Docker Compose, Google Cloud, LXC |
| **CI/CD** | GitHub Actions |

---

## 10. File Structure

```
MissionControl/
├── backend/
│   ├── app/
│   │   ├── ai/                  # AI operations engine
│   │   ├── core/                # Config, security, auth
│   │   ├── db/                  # Database engine, Redis
│   │   ├── events/              # Event bus (pub/sub)
│   │   ├── heartbeat/           # Heartbeat service
│   │   ├── models/db/           # 29 ORM models
│   │   ├── plugins/             # Plugin framework
│   │   ├── providers/           # Integration providers
│   │   ├── repositories/        # Data access layer
│   │   ├── routers/             # 25 API routers
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── seed/                # Demo data seeder
│   │   ├── services/            # 24 business services
│   │   ├── state/               # Agent state engine
│   │   └── main.py              # FastAPI app factory
│   ├── alembic/                 # Database migrations
│   ├── tests/                   # Backend tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/          # Reusable UI components
│   │   ├── contexts/            # React contexts
│   │   ├── layouts/             # App layout, sidebar
│   │   ├── pages/               # 78 page components
│   │   ├── services/            # API client
│   │   └── config/              # Navigation, theme
│   └── package.json
├── .agents/
│   └── agent/                   # Agent source code
│       ├── agent.py             # Main orchestrator
│       ├── client.py            # HTTP client
│       ├── heartbeat.py         # Heartbeat loop
│       ├── inventory.py         # Inventory collector
│       ├── executor.py          # Command executor
│       ├── connectors/          # SSH, WinRM, PS Remoting
│       └── plugins/             # Agent plugins
├── docker-compose.yml           # Development
├── docker-compose.prod.yml      # Production
└── VERSION                      # 3.0.0
```

---

## 11. Cross-References

| Document | Description |
|----------|-------------|
| [COMPONENTS.md](COMPONENTS.md) | Detailed component descriptions |
| [DATA_FLOW.md](DATA_FLOW.md) | Information flow diagrams |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Deployment models and guides |
| [SECURITY.md](SECURITY.md) | Security architecture |
| [PLUGINS.md](PLUGINS.md) | Plugin framework and SDK |
| [AGENTS.md](AGENTS.md) | Agent architecture |
| [EVENT_BUS.md](EVENT_BUS.md) | Event bus architecture |
| [HEARTBEAT.md](HEARTBEAT.md) | Heartbeat protocol |
| [DATABASE.md](DATABASE.md) | Database schema |
| [API.md](API.md) | REST API conventions |
| [ADR.md](ADR.md) | Architecture Decision Records |
