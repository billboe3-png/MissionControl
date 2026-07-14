# Mission Control

A full-stack IT operations platform for managing remote infrastructure, monitoring system health, and executing commands across your environment from a single unified dashboard.

## Vision

One dashboard. One workflow. One place to manage everything.

## Overview

Mission Control is a production-grade operations platform built for senior IT professionals and system administrators. It provides remote host management, secure credential storage, command execution, file browsing, and infrastructure monitoring through a modern web interface inspired by Windows Admin Center.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.14, FastAPI, SQLAlchemy ORM |
| Database | PostgreSQL, Alembic migrations |
| Frontend | React 18, TypeScript (strict), Vite 5 |
| Styling | Tailwind-inspired custom CSS (dark theme) |
| Security | Fernet encryption (AES-128-CBC), credential vault |
| Remote | Paramiko (SSH), pywinrm (WinRM) |
| Testing | pytest (307 tests), TypeScript strict mode |
| Containerization | Docker Compose |

## Current Status

**Sprint 2.1.9** - Production-Readiness Finalization

All remote operations are production-complete. The platform is ready for Sprint 2.2.

## Features

### Dashboard
- Real-time system metrics (CPU, memory, disk, uptime)
- Docker container status and statistics
- Git repository health
- Project, task, and note summaries
- Remote host overview with recent command history
- Health status badges for all services

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
│         History | Files | Infrastructure | Settings     │
├─────────────────────────────────────────────────────────┤
│                    FastAPI Backend                       │
│  ┌──────────────────────────────────────────────┐      │
│  │                  Routers                      │      │
│  │  /remote  /dashboard  /projects  /tasks       │      │
│  └──────────────────┬───────────────────────────┘      │
│  ┌──────────────────┴───────────────────────────┐      │
│  │               Service Layer                   │      │
│  │  RemoteService | DashboardService | etc.      │      │
│  └──────────────────┬───────────────────────────┘      │
│  ┌──────────────────┴───────────────────────────┐      │
│  │              Repository Layer                 │      │
│  │  RemoteHostRepo | CredentialRepo | HistoryRepo│      │
│  └──────────────────┬───────────────────────────┘      │
│  ┌──────────────────┴───────────────────────────┐      │
│  │           Provider Layer (Strategy)           │      │
│  │  SSHProvider | WinRMProvider | ProviderFactory │      │
│  └──────────────────┬───────────────────────────┘      │
│  ┌──────────────────┴───────────────────────────┐      │
│  │              SQLAlchemy ORM                   │      │
│  │  RemoteHost | CredentialProfile | CommandHistory│     │
│  │  CommandTemplate | ScheduledCommand | etc.    │      │
│  └──────────────────────────────────────────────┘      │
├─────────────────────────────────────────────────────────┤
│                    PostgreSQL                           │
│  9 Alembic migrations | 10 ORM models                  │
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
| `RemoteHost` | `remote_hosts` | SSH/WinRM host definitions |
| `CredentialProfile` | `credential_profiles` | Encrypted auth credentials |
| `CommandHistory` | `command_history` | Execution audit trail |
| `CommandTemplate` | `command_templates` | Reusable command library |
| `ScheduledCommand` | `scheduled_commands` | Cron-based command scheduling |
| `Project` | `projects` | Project management |
| `Task` | `tasks` | Task tracking |
| `Note` | `notes` | Notes and documentation |
| `ParkingLot` | `parking_lot` | Backlog parking lot |
| `Resume` | `resumes` | Resume context |

## UI Design

Mission Control v3 uses a **Windows Admin Center-inspired layout**:

- **Persistent Sidebar** - Collapsible nav groups (Dashboard, Infrastructure, Remote Operations, Settings)
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
├── backend/
│   ├── alembic/versions/        # 9 migrations
│   ├── app/
│   │   ├── core/                # Config, security (Fernet cipher)
│   │   ├── db/                  # Database engine, session
│   │   ├── models/db/           # 10 SQLAlchemy ORM models
│   │   ├── providers/           # Strategy pattern providers
│   │   │   ├── remote/          # SSH, WinRM, provider factory
│   │   │   ├── health_provider.py
│   │   │   ├── system_provider.py
│   │   │   ├── docker_provider.py
│   │   │   └── git_provider.py
│   │   ├── repositories/        # Data access layer (8 repos)
│   │   ├── routers/             # FastAPI routers
│   │   ├── schemas/             # Pydantic request/response models
│   │   ├── seed/                # Idempotent seed framework
│   │   └── services/            # Business logic layer
│   ├── tests/                   # 307 pytest tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/          # DataTable, EmptyState, PageHeader, etc.
│   │   │   ├── dashboard/       # StatCard, HealthBadges, QuickActions
│   │   │   ├── modals/          # HostModal, CredentialModal
│   │   │   └── sidebar/         # NavGroup, NavItem, UserBadge
│   │   ├── contexts/            # SidebarContext, ToastContext
│   │   ├── layouts/             # AppLayout, Sidebar, TopBar, StatusBar, Breadcrumb
│   │   ├── pages/
│   │   │   ├── infrastructure/  # Overview, System, Docker, Git, Health
│   │   │   ├── remote/          # Hosts, Credentials, Execute, History, Files
│   │   │   └── settings/        # General, Appearance, About
│   │   ├── services/            # API clients (remote.ts, files.ts, api.ts)
│   │   ├── styles.css           # 2425-line dark theme
│   │   └── types/               # TypeScript type definitions
│   ├── package.json
│   └── vite.config.ts
├── docker/                      # Docker Compose configuration
├── .env.example
├── docker-compose.yml
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.14+
- Node.js 18+
- PostgreSQL 15+
- Docker & Docker Compose (optional)

### Docker (Recommended)

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
| GET | `/api/v1/dashboard` | Full dashboard data |
| GET | `/remote/metrics` | Session and provider metrics |
| GET | `/health` | Health check |

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MISSIONCONTROL_SECRET_KEY` | **Yes** | - | Fernet key for credential encryption |
| `POSTGRES_DB` | No | `mission_control` | PostgreSQL database name |
| `POSTGRES_USER` | No | `mission_control` | PostgreSQL user |
| `POSTGRES_PASSWORD` | No | `mission_control` | PostgreSQL password |
| `POSTGRES_HOST` | No | `postgres` | PostgreSQL host |
| `POSTGRES_PORT` | No | `5432` | PostgreSQL port |
| `BACKEND_CORS_ORIGINS` | No | `http://localhost:5173` | Allowed CORS origins |
| `SSH_CONNECT_TIMEOUT` | No | `10` | SSH connection timeout (seconds) |
| `SSH_COMMAND_TIMEOUT` | No | `60` | SSH command timeout (seconds) |
| `WINRM_CONNECT_TIMEOUT` | No | `10` | WinRM connection timeout (seconds) |
| `WINRM_OPERATION_TIMEOUT` | No | `60` | WinRM operation timeout (seconds) |
| `REMOTE_RETRY_COUNT` | No | `1` | Retries for transient remote failures |

## Testing

```bash
# Backend (307 tests)
cd backend
python -m pytest tests/ -v

# Frontend type checking
cd frontend
npx tsc --noEmit

# Frontend production build
cd frontend
npm run build
```

### Test Coverage

| Area | Tests | Description |
|------|-------|-------------|
| API Integration | 68 | CRUD endpoints, auth, remote operations |
| Repositories | 45 | Data access, search, encryption |
| Services | 89 | Business logic, validation, credential handling |
| Providers | 52 | SSH, WinRM, provider factory, dummy provider |
| History & Audit | 53 | Command history, templates, schedules, bulk execution |

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

### Planned (Sprint 2.2+)
- Connection pooling with idle cleanup
- Streaming command output (SSE/WebSocket)
- Command cancellation support
- Host/credential validation module
- Standalone metrics provider
- Monitoring integration
- Identity & Access management
- Automation workflows
- AI-powered operations assistant

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on contributing to Mission Control.

## License

See [LICENSE](LICENSE) for license information.
