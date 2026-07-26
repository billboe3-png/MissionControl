# Repository Structure

This document maps the Mission Control repository layout and explains the purpose of every major directory and file.

## Root Directory

```
MissionControl/
├── .agents/                  # Autonomous agent framework
├── .github/                  # GitHub Actions CI workflows
├── backend/                  # Python FastAPI backend
├── deployment/               # LXC and Proxmox deployment configs
├── docs/                     # Project documentation
├── frontend/                 # TypeScript React frontend
├── nginx/                    # Nginx reverse proxy configuration
├── proxmox/                  # Proxmox template configs
├── scripts/                  # PowerShell utility scripts
├── tests/                    # Root-level integration tests
├── .env                      # Local environment variables (gitignored)
├── .env.example              # Template for .env
├── docker-compose.yml        # Development Docker stack
├── docker-compose.prod.yml   # Production Docker stack
├── CHANGELOG.md              # Release history
├── CONTRIBUTING.md           # Contribution guidelines
├── DEPLOYMENT.md             # Deployment instructions
├── README.md                 # Project overview
├── RELEASE_NOTES.md          # Latest release notes
├── VERSION                   # Current version string (3.0.0)
└── PLAN-agent-relay.md       # Agent relay design notes
```

## Backend — `backend/`

```
backend/
├── alembic/                  # Alembic migration framework
│   ├── versions/             # Individual migration scripts (21+)
│   └── env.py                # Alembic environment config
├── app/                      # Application source code
│   ├── main.py               # FastAPI app factory, middleware, router registration
│   ├── core/                 # Cross-cutting configuration
│   │   ├── config.py         # Pydantic Settings (env vars, defaults)
│   │   ├── security.py       # Fernet encryption, JWT signing
│   │   ├── auth_dependency.py # FastAPI Depends() for JWT auth
│   │   ├── company_context.py # Multi-tenant company/site context
│   │   └── startup_check.py  # Pre-startup validation
│   ├── db/                   # Database engine and session management
│   ├── models/db/            # SQLAlchemy 2.0 ORM models (29 models)
│   ├── schemas/              # Pydantic v2 request/response schemas
│   ├── routers/              # FastAPI routers (25 routers)
│   ├── services/             # Business logic layer (24 services)
│   ├── repositories/         # Data access layer (25 repositories)
│   ├── providers/            # Strategy pattern providers
│   │   ├── remote/           # SSH, WinRM, provider factory
│   │   ├── zabbix/           # Zabbix monitoring provider
│   │   ├── proxmox/          # Proxmox VE provider
│   │   ├── hyperv/           # Hyper-V provider
│   │   └── identity/         # Azure AD / M365 provider
│   ├── platform/             # Platform integration layer
│   ├── ai/                   # AI provider integration
│   ├── plugins/              # Plugin framework
│   ├── events/               # Event bus
│   ├── heartbeat/            # Heartbeat monitoring
│   ├── state/                # Application state management
│   ├── seed/                 # Idempotent seed framework
│   ├── storage/              # File storage utilities
│   └── utils/                # Shared utility functions
├── tests/                    # Pytest test suite (1062+ tests)
├── alembic.ini               # Alembic configuration
├── Dockerfile                # Backend container build
├── entrypoint.sh             # Container entrypoint (migrate, seed, start)
└── requirements.txt          # Python dependencies
```

### Key Backend Directories

| Directory | Purpose |
|-----------|---------|
| `app/routers/` | HTTP endpoint definitions. Each file maps to a domain (remote, auth, automation, etc.). |
| `app/services/` | Business logic. Services orchestrate repositories and providers. |
| `app/repositories/` | Static data-access methods. One repository per entity. |
| `app/models/db/` | SQLAlchemy ORM model definitions. One file per model or domain group. |
| `app/schemas/` | Pydantic v2 models for request validation and response serialization. |
| `app/providers/` | Platform-specific implementations behind ABC interfaces (SSH, WinRM, Zabbix, etc.). |
| `app/core/` | Configuration, security, auth dependency injection. |
| `app/seed/` | Idempotent database seeding (default admin user, sample data). |

## Frontend — `frontend/`

```
frontend/
├── src/
│   ├── main.tsx              # React entry point
│   ├── App.tsx               # Root component, React Router setup
│   ├── styles.css            # Global dark-theme CSS
│   ├── vite-env.d.ts         # Vite type declarations
│   ├── components/           # Reusable UI components
│   │   ├── common/           # DataTable, EmptyState, PageHeader, SearchInput, StatusBadge
│   │   ├── dashboard/        # StatCard, HealthBadges, QuickActions
│   │   ├── modals/           # HostModal, CredentialModal, and other dialog components
│   │   └── sidebar/          # NavGroup, NavItem, UserBadge
│   ├── contexts/             # React contexts (SidebarContext, ToastContext)
│   ├── hooks/                # Custom React hooks
│   ├── layouts/              # AppLayout, Sidebar, TopBar, StatusBar
│   ├── pages/                # Page components (78 pages)
│   │   ├── agents/           # Agent management
│   │   ├── ai/               # AI assistant
│   │   ├── auth/             # Login, user management
│   │   ├── automation/       # Playbook management
│   │   ├── companies/        # Company management
│   │   ├── dashboard/        # Main dashboard
│   │   ├── hyperv/           # Hyper-V management
│   │   ├── identity/         # Identity provider
│   │   ├── infrastructure/   # Overview, System, Docker, Git, Health
│   │   ├── proxmox/          # Proxmox management
│   │   ├── remote/           # Hosts, Credentials, Execute, History, Files
│   │   ├── settings/         # General, Appearance, About
│   │   └── zabbix/           # Zabbix monitoring
│   ├── services/             # API client modules
│   ├── types/                # TypeScript type definitions
│   ├── config/               # App configuration constants
│   └── utils/                # Shared utility functions
├── package.json              # npm dependencies and scripts
├── vite.config.ts            # Vite build configuration
├── tsconfig.json             # TypeScript project references
├── tsconfig.app.json         # App TypeScript config (strict mode, ES2020)
├── tsconfig.node.json        # Node TypeScript config
├── Dockerfile                # Frontend container build
└── index.html                # HTML entry point
```

## Agent — `.agents/`

```
.agents/
├── agent/                    # Agent implementation (Python 3.12)
│   ├── main.py               # Agent entry point
│   ├── plugins/              # Runtime plugins (Zabbix, AD, M365)
│   └── collectors/           # Remote inventory collectors
├── skills/                   # Agent skill modules
└── tests/                    # Agent test suite
```

The agent runs on remote machines and communicates with the backend via API keys. It provides inventory data, executes commands, and runs plugins.

## Deployment — `deployment/`

```
deployment/
└── lxc/                      # LXC container deployment
    ├── docker/               # Production docker-compose for LXC
    ├── docs/                 # LXC operations docs (install, upgrade, backup, restore)
    └── README.md             # LXC deployment overview
```

## Supporting Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Development stack: backend, frontend (Vite), nginx, postgres, redis |
| `docker-compose.prod.yml` | Production stack: no bind mounts, no docker.sock, resource limits |
| `nginx/default.conf` | Nginx reverse proxy routes (frontend + backend) |
| `scripts/` | PowerShell utilities (backup, restore, quality gate) |
| `VERSION` | Single source of truth for the current version string |
| `.env.example` | Template for all environment variables |
| `.github/workflows/ci.yml` | GitHub Actions CI pipeline |

## Cross-References

- For local development setup, see [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md).
- For coding standards, see [CODING_STANDARDS.md](CODING_STANDARDS.md).
- For backend architecture details, see [BACKEND.md](BACKEND.md).
- For frontend architecture details, see [FRONTEND.md](FRONTEND.md).
