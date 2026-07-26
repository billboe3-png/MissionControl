# Mission Control Developer Guide

Welcome to Mission Control — a full-stack IT operations platform for managing remote infrastructure, monitoring system health, and executing commands from a unified dashboard.

This guide is the central entry point for all developer documentation. Whether you are onboarding for the first time or looking for a specific workflow, start here.

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.12+ | Backend runtime |
| Node.js | 20+ | Frontend build tooling |
| Docker & Docker Compose | Latest | Containerised dev/prod stacks |
| Git | 2.30+ | Version control |
| PostgreSQL | 16 | Primary data store |
| Redis | 7.2 | Rate limiting, cache |

## How to Use This Guide

| Document | When to Read |
|----------|-------------|
| [REPOSITORY_STRUCTURE.md](REPOSITORY_STRUCTURE.md) | First day — understand where everything lives |
| [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md) | First day — get the stack running locally |
| [CODING_STANDARDS.md](CODING_STANDARDS.md) | Before writing any code |
| [BACKEND.md](BACKEND.md) | Working on API, services, models, or providers |
| [FRONTEND.md](FRONTEND.md) | Working on React components, pages, or styles |
| [DATABASE.md](DATABASE.md) | Modifying models, running migrations, seeding data |
| [API.md](API.md) | Creating or modifying API endpoints |
| [TESTING.md](TESTING.md) | Writing or running tests |
| [CI_CD.md](CI_CD.md) | Understanding the build and deploy pipeline |
| [RELEASE_PROCESS.md](RELEASE_PROCESS.md) | Cutting a release or bumping versions |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Opening PRs and participating in code review |

## Codebase at a Glance

```
MissionControl/
├── backend/          Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic
├── frontend/         TypeScript, React 18, Vite, React Router
├── .agents/          Autonomous agent framework (Python 3.12)
├── deployment/       LXC and Proxmox deployment configs
├── docker-compose.yml        Dev stack (5 services)
├── docker-compose.prod.yml   Production stack
└── VERSION                    Current version (3.0.0)
```

| Metric | Count |
|--------|-------|
| Backend Python files | 251 |
| Database models | 29 |
| API routers | 25 |
| Service modules | 24 |
| Frontend pages | 78 |
| Pytest tests | 1062+ |

## Architecture Overview

The backend follows a layered architecture:

```
Router → Service → Repository → SQLAlchemy Model
                ↕
         Provider (Strategy pattern)
```

- **Routers** handle HTTP requests and delegate to services.
- **Services** contain business logic and orchestration.
- **Repositories** provide static data-access methods per entity.
- **Providers** implement platform-specific logic (SSH, WinRM, Zabbix, Proxmox, etc.) behind ABC interfaces.
- **Schemas** (Pydantic v2) define request/response contracts.

The frontend uses React 18 with React Router for client-side routing, Vite for bundling, and a dark-theme CSS layer.

## Git Workflow

```
main ─────────────────────── production
  └── develop ────────────── integration
        └── feature/* ────── work branches
```

- `main` is always deployable.
- `develop` is the integration branch for the next release.
- Feature branches fork from `develop` and merge back via PR.

## Docker Services

| Service | Port | Purpose |
|---------|------|---------|
| nginx | 80 | Reverse proxy |
| backend | 8000 (internal) | FastAPI application |
| frontend | 3000 (internal) | React dev/build server |
| postgres | 5432 (internal) | PostgreSQL 16 |
| redis | 6379 (internal) | Redis 7.2 |

## Getting Help

- Run `ruff check app/ tests/` to lint the backend.
- Run `npx tsc --noEmit` in `frontend/` to type-check the frontend.
- Visit `/api/docs` for the interactive Swagger UI.
- Check the [operations manual](../operations/MissionControl-v2-Operations-Manual.md) for deployment runbooks.
