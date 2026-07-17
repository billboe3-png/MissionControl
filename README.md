# Mission Control

**v3.0.0** - A full-stack IT operations platform for managing remote infrastructure, monitoring system health, and executing commands across your environment from a single unified dashboard.

## Vision

One dashboard. One workflow. One place to manage everything.

## Overview

Mission Control is a production-grade operations platform built for senior IT professionals and system administrators. It provides multi-tenant company/site management, remote host management, secure credential storage, command execution, file browsing, automation playbooks, AI-assisted operations, and infrastructure monitoring through a modern web interface inspired by Windows Admin Center.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.14, FastAPI, SQLAlchemy ORM |
| Database | PostgreSQL, Alembic migrations (21) |
| Cache | Redis 5.x (rate limiting, session store) |
| Frontend | React 18, TypeScript (strict), Vite 5 |
| Styling | Tailwind-inspired custom CSS (dark theme) |
| Security | Fernet encryption (AES-128-CBC), HMAC-signed JWT tokens, credential vault |
| Remote | Paramiko (SSH), pywinrm (WinRM) |
| Testing | pytest (1062+ tests), ruff linting, TypeScript strict mode |
| Containerization | Docker Compose (dev + prod) |

## Features

### Dashboard
- Real-time system metrics (CPU, memory, disk, uptime)
- Docker container status and statistics
- Git repository health
- Project, task, and note summaries
- Remote host overview with recent command history
- Health status badges for all services

### Authentication & Multi-Tenancy
- JWT-based authentication with Bearer tokens
- Role-based access control (global_admin, company_admin, operator, viewer)
- Company and site scoping for multi-tenant isolation
- User management (CRUD, role assignment, enable/disable)

### Remote Operations
- **Host Management** - Full CRUD for SSH and WinRM hosts with credential assignment
- **Credential Vault** - Encrypted credential profiles (passwords, SSH keys, passphrases) with Fernet encryption at rest
- **Command Execution** - Execute commands on remote hosts with real-time output
- **Bulk Execution** - Run commands across multiple hosts simultaneously
- **Command Templates** - Reusable command library with category and protocol tagging
- **Scheduled Commands** - Cron-based scheduling with run-now capability
- **File Browser** - Browse, upload, download, create directories, and delete files on remote hosts
- **Command History** - Full audit trail with execution source tracking (manual, template, scheduled, bulk)
- **Connection Testing** - Verify host connectivity before execution
- **Session Metrics** - Track active sessions, command counts, and latency

### Automation & Playbooks
- **Playbooks** - Multi-step automation workflows with variable substitution
- **Playbook Steps** - Ordered steps with per-step command execution
- **Playbook Schedules** - Cron-based playbook scheduling
- **Playbook Execution Logs** - Full execution history with status tracking
- **Event Triggers** - Event-driven automation hooks
- **Execution Logs** - Audit trail for all automation activity

### Platform Integrations
- **Agent Management** - Register and authenticate remote agents via API keys
- **Integration Profiles** - Configure external platform connections (Zabbix, Proxmox, Hyper-V, Azure AD)
- **Zabbix** - Host monitoring integration
- **Proxmox** - Virtual machine management
- **Hyper-V** - Windows hypervisor management
- **Identity (Azure AD/M365)** - Directory and identity provider integration

### AI-Assisted Operations
- AI provider integration for operational assistance
- Natural language command suggestions

### Infrastructure Monitoring
- System overview (hostname, OS, CPU, memory, disk)
- Docker container details (status, ports, health, resources)
- Git repository status (branch, commits, working tree)
- Health check dashboard

### Settings
- General application settings
- Appearance customization
- About page with version and stack info

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend                        │
│  ┌──────────┬──────────┬──────────┬──────────┐         │
│  │ Sidebar  │  TopBar  │ Content  │ StatusBar│         │
│  │ (v3)     │ (bread)  │ (Outlet) │ (clock)  │         │
│  └──────────┴──────────┴──────────┴──────────┘         │
│                                                         │
│  Pages: Dashboard | Hosts | Credentials | Execute |     │
│         History | Files | Infrastructure | Settings |   │
│         Auth | Agents | Automation | AI |                │
│         Companies | Identity | Zabbix | Proxmox | HyperV│
├─────────────────────────────────────────────────────────┤
│                    FastAPI Backend                       │
│  ┌──────────────────────────────────────────────┐      │
│  │                  Routers                      │      │
│  │  /remote /dashboard /projects /tasks          │      │
│  │  /auth /agents /automation /integration       │      │
│  │  /identity /zabbix /proxmox /hyperv /ai      │      │
│  └──────────────────┬───────────────────────────┘      │
│  ┌──────────────────┴───────────────────────────┐      │
│  │               Service Layer                   │      │
│  │  RemoteService | AuthService | AgentService   │      │
│  │  AutomationService | PlaybookService | etc.   │      │
│  └──────────────────┬───────────────────────────┘      │
│  ┌──────────────────┴───────────────────────────┐      │
│  │              Repository Layer                 │      │
│  │  25 repositories (host, credential, agent,    │      │
│  │  playbook, integration, approval, etc.)       │      │
│  └──────────────────┬───────────────────────────┘      │
│  ┌──────────────────┴───────────────────────────┐      │
│  │           Provider Layer (Strategy)           │      │
│  │  SSHProvider | WinRMProvider | ProviderFactory │      │
│  │  ZabbixProvider | ProxmoxProvider | etc.       │      │
│  └──────────────────┬───────────────────────────┘      │
│  ┌──────────────────┴───────────────────────────┐      │
│  │              SQLAlchemy ORM                   │      │
│  │  27 models across all domains                 │      │
│  └──────────────────────────────────────────────┘      │
│  ┌──────────────────────────────────────────────┐      │
│  │           Middleware & Security               │      │
│  │  JWT auth | Rate limiting | CORS | Fernet     │      │
│  └──────────────────────────────────────────────┘      │
├─────────────────────────────────────────────────────────┤
│                    Data Layer                            │
│  ┌────────────────────┬────────────────────────┐       │
│  │    PostgreSQL       │       Redis            │       │
│  │  21 migrations      │  Rate limiting cache   │       │
│  │  27 ORM models      │  Session store         │       │
│  └────────────────────┴────────────────────────┘       │
└─────────────────────────────────────────────────────────┘
```

### Design Patterns

- **Repository Pattern** - Each entity has its own repository class with static methods
- **Service Layer** - Business logic between routers and repositories
- **Provider Pattern (Strategy)** - ABC base classes for each infrastructure domain, SDK implementations, provider adapters, factory singletons
- **Dependency Injection** - FastAPI `Depends()` for DB sessions and services
- **Encrypted Vault** - Fernet encryption for all credential data at rest

### ORM Models

| Model | Table | Purpose |
|-------|-------|---------|
| **Core** | | |
| `User` | `users` | User accounts with role-based access |
| `Company` | `companies` | Tenant company definitions |
| `Site` | `sites` | Site locations within companies |
| **Remote Operations** | | |
| `RemoteHost` | `remote_hosts` | SSH/WinRM host definitions |
| `CredentialProfile` | `credential_profiles` | Encrypted auth credentials |
| `CommandHistory` | `command_history` | Execution audit trail |
| `CommandTemplate` | `command_templates` | Reusable command library |
| `ScheduledCommand` | `scheduled_commands` | Cron-based command scheduling |
| **Agent & Integration** | | |
| `Agent` | `agents` | Registered remote agent instances |
| `AgentCommand` | `agent_commands` | Commands dispatched to agents |
| `AgentRegistrationToken` | `agent_registration_tokens` | Agent API key management |
| `IntegrationProfile` | `integration_profiles` | External platform connections |
| **Automation** | | |
| `Playbook` | `playbooks` | Multi-step automation workflows |
| `PlaybookStep` | `playbook_steps` | Individual workflow steps |
| `PlaybookVariable` | `playbook_variables` | Workflow variable definitions |
| `PlaybookSchedule` | `playbook_schedules` | Cron-based playbook scheduling |
| `PlaybookExecution` | `playbook_executions` | Workflow execution history |
| `EventTrigger` | `event_triggers` | Event-driven automation hooks |
| `ExecutionLog` | `execution_logs` | Automation activity audit trail |
| **Approval** | | |
| `ApprovalWorkflow` | `approval_workflows` | Approval process definitions |
| `ApprovalRequest` | `approval_requests` | Pending approval records |
| **Project Management** | | |
| `Project` | `projects` | Project management |
| `Task` | `tasks` | Task tracking |
| `Note` | `notes` | Notes and documentation |
| `ParkingLot` | `parking_lot` | Backlog parking lot |
| `Resume` | `resumes` | Resume context |
| **Audit** | | |
| `AuditTrail` | `audit_trail` | System-wide audit logging |

## UI Design

Mission Control v3 uses a **Windows Admin Center-inspired layout**:

- **Persistent Sidebar** - Collapsible nav groups (Dashboard, Infrastructure, Remote Operations, Automation, Platform, Settings)
- **Top Bar** - Breadcrumb navigation with route labels
- **Status Bar** - Live clock, connection status, version info
- **Content Area** - Full-width page content with `<Outlet />` routing

All pages follow consistent patterns:
- `PageHeader` with title, subtitle, and action buttons
- `DataTable` for tabular data with row click support
- `EmptyState` for zero-data scenarios
- `StatusBadge` for state visualization
- `SearchInput` for filtering
- Modals for create/edit operations

## Repository Layout

```
MissionControl/
├── .agents/                      # Autonomous agent framework
│   ├── agent/                    # Agent implementation
│   ├── skills/                   # Agent skill modules
│   └── tests/                    # Agent test suite
├── .github/
│   └── workflows/ci.yml          # GitHub Actions CI pipeline
├── backend/
│   ├── alembic/versions/         # 21 migrations
│   ├── app/
│   │   ├── ai/                   # AI provider integration
│   │   ├── api/                  # API utilities
│   │   ├── core/                 # Config, security, auth dependency
│   │   ├── db/                   # Database engine, session
│   │   ├── infrastructure/       # Infrastructure utilities
│   │   ├── models/db/            # 27 SQLAlchemy ORM models
│   │   ├── platform/             # Platform integration layer
│   │   ├── providers/            # Strategy pattern providers
│   │   │   ├── remote/           # SSH, WinRM, provider factory
│   │   │   ├── zabbix/           # Zabbix monitoring
│   │   │   ├── proxmox/          # Proxmox VE
│   │   │   ├── hyperv/           # Hyper-V
│   │   │   └── identity/         # Azure AD / M365
│   │   ├── repositories/         # Data access layer (25 repos)
│   │   ├── routers/              # FastAPI routers (26 endpoints)
│   │   ├── schemas/              # Pydantic request/response models
│   │   ├── seed/                 # Idempotent seed framework
│   │   ├── services/             # Business logic layer
│   │   ├── storage/              # File storage utilities
│   │   └── utils/                # Shared utilities
│   ├── tests/                    # 1062+ pytest tests
│   ├── Dockerfile
│   ├── entrypoint.sh
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/           # DataTable, EmptyState, PageHeader, etc.
│   │   │   ├── dashboard/        # StatCard, HealthBadges, QuickActions
│   │   │   ├── modals/           # HostModal, CredentialModal
│   │   │   └── sidebar/          # NavGroup, NavItem, UserBadge
│   │   ├── contexts/             # SidebarContext, ToastContext
│   │   ├── layouts/              # AppLayout, Sidebar, TopBar, StatusBar
│   │   ├── pages/
│   │   │   ├── agents/           # Agent management
│   │   │   ├── ai/               # AI assistant
│   │   │   ├── auth/             # Login, user management
│   │   │   ├── automation/       # Playbook management
│   │   │   ├── companies/        # Company management
│   │   │   ├── hyperv/           # Hyper-V management
│   │   │   ├── identity/         # Identity provider
│   │   │   ├── infrastructure/   # Overview, System, Docker, Git, Health
│   │   │   ├── proxmox/          # Proxmox management
│   │   │   ├── remote/           # Hosts, Credentials, Execute, History, Files
│   │   │   ├── settings/         # General, Appearance, About
│   │   │   └── zabbix/           # Zabbix monitoring
│   │   ├── services/             # API clients
│   │   ├── styles.css            # Dark theme
│   │   └── types/                # TypeScript type definitions
│   ├── package.json
│   └── vite.config.ts
├── docker/                       # Docker build context
├── nginx/                        # Nginx reverse proxy config
├── scripts/                      # PowerShell utility scripts
├── tests/                        # Root-level integration tests
├── .env.example
├── docker-compose.yml            # Development stack
├── docker-compose.prod.yml       # Production stack
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.14+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

### Docker - Development

```bash
git clone <repository>
cd MissionControl

# Generate a secret key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Set it in .env
cp .env.example .env
# Edit .env and set MISSIONCONTROL_SECRET_KEY

# Start everything
docker compose up -d
```

The backend entrypoint will:
1. Validate `MISSIONCONTROL_SECRET_KEY`
2. Run Alembic migrations
3. Seed the database
4. Start the API server

**Frontend:** http://localhost:5173
**Backend API:** http://localhost:8000/api/v1
**API Docs:** http://localhost:8000/docs

### Docker - Production

```bash
# Copy and configure production env
cp .env.example .env
# Edit .env with production values (see Environment Variables below)

# Start production stack (Nginx reverse proxy, no Vite dev server)
docker compose -f docker-compose.prod.yml up -d
```

**Application:** http://localhost:80 (via Nginx)
**Backend API:** http://localhost:8000/api/v1
**API Docs:** http://localhost:8000/docs

### Local Development

```bash
# Backend
cd backend
python -m venv .venv
.venv/Scripts/activate  # Windows
pip install -r requirements.txt
alembic upgrade head
python -m app.seed.runner
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

## Security

### Credential Encryption

All credential data (passwords, SSH keys, passphrases) is encrypted at rest using **Fernet symmetric encryption** (AES-128-CBC). The encryption key is derived from `MISSIONCONTROL_SECRET_KEY`.

- Passwords are encrypted on save, decrypted only in the service layer before passing to providers
- Response schemas never expose sensitive fields
- Key versioning supports secret rotation

### JWT Authentication

Users authenticate via `/api/v1/auth/login` and receive an HMAC-signed access token. All protected endpoints require a `Bearer` token in the `Authorization` header.

- Tokens are lightweight HMAC-signed JWTs (no external JWT library dependency)
- Role-based access control: `global_admin`, `company_admin`, `operator`, `viewer`
- Company and site scoping enforced at the service layer

### Rate Limiting

In-memory sliding-window rate limiting protects the API:

- General endpoints: 60 requests/minute per IP
- Authentication endpoints: 5 requests/minute per IP (brute-force protection)

### CORS

Production CORS origins are configurable via `BACKEND_CORS_ORIGINS`. The default allows `localhost`, `localhost:3000`, and `localhost:5173`.

### Generating a Secret Key

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Secret Rotation

1. Generate a new key
2. Update `MISSIONCONTROL_SECRET_KEY` in `.env`
3. Re-create credential profiles (or run a migration script for production)
4. Restart the stack

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Authenticate and receive access token |
| GET | `/auth/me` | Get current authenticated user |
| POST | `/auth/change-password` | Change current user's password |
| GET | `/auth/users` | List users (company_admin+) |
| POST | `/auth/users` | Create user (company_admin+) |
| PUT | `/auth/users/{id}` | Update user (company_admin+) |
| DELETE | `/auth/users/{id}` | Delete user (company_admin+) |

### Hosts
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/remote/hosts` | List all hosts (optional search) |
| GET | `/remote/hosts/{id}` | Get host by ID |
| POST | `/remote/hosts` | Create new host |
| PUT | `/remote/hosts/{id}` | Update host |
| DELETE | `/remote/hosts/{id}` | Delete host |

### Credentials
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/remote/credentials` | List all credentials |
| GET | `/remote/credentials/{id}` | Get credential by ID |
| POST | `/remote/credentials` | Create credential (encrypted) |
| PUT | `/remote/credentials/{id}` | Update credential |
| DELETE | `/remote/credentials/{id}` | Delete credential |

### Command Execution
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/remote/test` | Test connection to a host |
| POST | `/remote/execute` | Execute a command on a host |
| POST | `/remote/bulk-execute` | Execute across multiple hosts |
| GET | `/remote/history` | Query command history |

### Templates & Schedules
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/remote/templates` | List/create command templates |
| PUT/DELETE | `/remote/templates/{id}` | Update/delete template |
| POST | `/remote/templates/{id}/execute` | Execute template on host |
| GET/POST | `/remote/schedules` | List/create scheduled commands |
| PUT/DELETE | `/remote/schedules/{id}` | Update/delete schedule |
| POST | `/remote/schedules/{id}/run-now` | Run schedule immediately |

### File Transfer
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/remote/files/list` | List directory contents |
| POST | `/remote/files/upload` | Upload file (base64) |
| POST | `/remote/files/download` | Download file (base64) |
| POST | `/remote/files/mkdir` | Create directory |
| POST | `/remote/files/delete` | Delete file or directory |

### System
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard` | Full dashboard data |
| GET | `/remote/metrics` | Session and provider metrics |
| GET | `/health` | Health check |
| GET | `/doctor` | System diagnostics |
| GET | `/version` | Version info |

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MISSIONCONTROL_SECRET_KEY` | **Yes** | - | Fernet key for credential encryption |
| `POSTGRES_DB` | No | `mission_control` | PostgreSQL database name |
| `POSTGRES_USER` | No | `mission_control` | PostgreSQL user |
| `POSTGRES_PASSWORD` | No | `mission_control` | PostgreSQL password |
| `POSTGRES_HOST` | No | `postgres` | PostgreSQL host |
| `POSTGRES_PORT` | No | `5432` | PostgreSQL port |
| `REDIS_HOST` | No | `redis` | Redis host |
| `REDIS_PORT` | No | `6379` | Redis port |
| `BACKEND_CORS_ORIGINS` | No | `http://localhost,http://localhost:3000,http://localhost:5173` | Allowed CORS origins |
| `RATE_LIMIT_PER_MINUTE` | No | `60` | Max API requests per minute per IP |
| `RATE_LIMIT_AUTH_PER_MINUTE` | No | `5` | Max login attempts per minute per IP |
| `SSH_CONNECT_TIMEOUT` | No | `10` | SSH connection timeout (seconds) |
| `SSH_COMMAND_TIMEOUT` | No | `60` | SSH command timeout (seconds) |
| `WINRM_CONNECT_TIMEOUT` | No | `10` | WinRM connection timeout (seconds) |
| `WINRM_OPERATION_TIMEOUT` | No | `60` | WinRM operation timeout (seconds) |
| `REMOTE_RETRY_COUNT` | No | `1` | Retries for transient remote failures |

## Testing

```bash
# Backend (1062+ tests)
cd backend
python -m pytest tests/ -v

# Linting
ruff check app/ tests/

# Frontend type checking
cd frontend
npx tsc --noEmit

# Frontend production build
cd frontend
npm run build
```

### Test Coverage

| Area | Description |
|------|-------------|
| API Integration | CRUD endpoints, auth, remote operations |
| Repositories | Data access, search, encryption |
| Services | Business logic, validation, credential handling |
| Providers | SSH, WinRM, provider factory, platform integrations |
| History & Audit | Command history, templates, schedules, bulk execution |
| Automation | Playbook execution, scheduling, event triggers |
| Auth & Multi-Tenancy | Login, JWT, role-based access, company/site scoping |
| Agent Management | Agent registration, command dispatch, authentication |

## Roadmap

### Completed
- **Sprint 1.x** - CLI framework, project/task/note CRUD, dashboard, parking lot
- **Sprint 2.0** - Real-time dashboard, Docker/Git integration, system health
- **Sprint 2.1.0** - Remote operations framework (hosts, credentials, execution)
- **Sprint 2.1.2** - Production SSH execution (Paramiko)
- **Sprint 2.1.4** - Secure credential vault (Fernet encryption)
- **Sprint 2.1.5** - Production remote execution (connection reuse, retry, timeouts)
- **Sprint 2.1.8** - Templates, bulk execution, scheduled commands, file transfer, metrics
- **Sprint 2.1.9** - Production readiness (migrations, UI completion, dead code removal)
- **UI v3** - Windows Admin Center-inspired layout
- **Sprint 2.2** - Connection pooling with idle cleanup
- **Sprint 2.3** - Streaming command output (SSE/WebSocket)
- **Sprint 2.5** - Command cancellation support
- **Sprint 2.7** - Host/credential validation module
- **Sprint 2.8** - Standalone metrics provider
- **Sprint 3.0** - Multi-tenant platform (JWT auth, companies, sites, agents, automation playbooks, platform integrations, AI operations)

### Future
- Monitoring integration (extended Zabbix/Proxmox/Hyper-V coverage)
- Identity & Access management (expanded Azure AD/M365)
- Advanced automation workflows
- AI-powered operations assistant (expanded)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on contributing to Mission Control.

### Quick Reference

```bash
# Lint
ruff check app/ tests/

# Format
ruff format app/ tests/

# Test
python -m pytest tests/ -v

# Frontend type check
npx tsc --noEmit
```

## Deployment

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for architecture details and [docs/operations/](docs/operations/) for operational runbooks.

For production deployment, use `docker-compose.prod.yml` which runs the backend and Nginx reverse proxy without the Vite dev server.

## License

See [LICENSE](LICENSE) for license information.
