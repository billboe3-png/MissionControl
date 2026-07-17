# Mission Control v2 — Developer Guide

> **Version:** 0.1.0 · **Sprint:** 2.1.9 · **Status:** Production-Readiness Finalization
> **Audience:** New developers joining the Mission Control project
> **Last Updated:** July 2026

---

## Table of Contents

- [1. Introduction](#1-introduction)
  - [1.1 Vision](#11-vision)
  - [1.2 What Mission Control Does](#12-what-mission-control-does)
  - [1.3 How to Use This Guide](#13-how-to-use-this-guide)
- [2. Repository Structure](#2-repository-structure)
  - [2.1 Top-Level Layout](#21-top-level-layout)
  - [2.2 Backend Layout](#22-backend-layout)
  - [2.3 Frontend Layout](#23-frontend-layout)
  - [2.4 Infrastructure Layout](#24-infrastructure-layout)
- [3. Technology Stack](#3-technology-stack)
  - [3.1 Backend Stack](#31-backend-stack)
  - [3.2 Frontend Stack](#32-frontend-stack)
  - [3.3 Infrastructure Stack](#33-infrastructure-stack)
  - [3.4 Development Tools](#34-development-tools)
- [4. Coding Standards](#4-coding-standards)
  - [4.1 Python Standards](#41-python-standards)
  - [4.2 TypeScript Standards](#42-typescript-standards)
  - [4.3 Naming Conventions](#43-naming-conventions)
  - [4.4 File Organization](#44-file-organization)
- [5. Project Architecture](#5-project-architecture)
  - [5.1 Architecture Overview](#51-architecture-overview)
  - [5.2 Backend Structure](#52-backend-structure)
  - [5.3 Frontend Structure](#53-frontend-structure)
  - [5.4 Request Lifecycle](#54-request-lifecycle)
- [6. Backend Patterns](#6-backend-patterns)
  - [6.1 Router Pattern](#61-router-pattern)
  - [6.2 Service Pattern](#62-service-pattern)
  - [6.3 Repository Pattern](#63-repository-pattern)
  - [6.4 Provider Pattern](#64-provider-pattern)
  - [6.5 Dependency Injection](#65-dependency-injection)
  - [6.6 Factories](#66-factories)
- [7. Database Layer](#7-database-layer)
  - [7.1 SQLAlchemy Models](#71-sqlalchemy-models)
  - [7.2 Pydantic Schemas](#72-pydantic-schemas)
  - [7.3 Alembic Migrations](#73-alembic-migrations)
  - [7.4 Multi-Tenancy](#74-multi-tenancy)
  - [7.5 Database ERD](#75-database-erd)
- [8. FastAPI](#8-fastapi)
  - [8.1 Application Entry Point](#81-application-entry-point)
  - [8.2 Middleware](#82-middleware)
  - [8.3 Error Handling](#83-error-handling)
  - [8.4 Validation](#84-validation)
- [9. React Frontend](#9-react-frontend)
  - [9.1 Application Bootstrap](#91-application-bootstrap)
  - [9.2 Routing](#92-routing)
  - [9.3 Contexts](#93-contexts)
  - [9.4 Layouts](#94-layouts)
  - [9.5 Pages](#95-pages)
  - [9.6 Components](#96-components)
  - [9.7 Navigation](#97-navigation)
  - [9.8 Dashboard](#98-dashboard)
  - [9.9 Modals](#99-modals)
  - [9.10 API Client Pattern](#910-api-client-pattern)
  - [9.11 CSS and Styling](#911-css-and-styling)
- [10. Configuration](#10-configuration)
  - [10.1 Environment Management](#101-environment-management)
  - [10.2 Settings Class](#102-settings-class)
  - [10.3 Startup Sequence](#103-startup-sequence)
- [11. Authentication and Authorization](#11-authentication-and-authorization)
  - [11.1 Token-Based Auth](#111-token-based-auth)
  - [11.2 Password Hashing](#112-password-hashing)
  - [11.3 Role-Based Access Control](#113-role-based-access-control)
  - [11.4 Multi-Tenant Context](#114-multi-tenant-context)
- [12. Security](#12-security)
  - [12.1 Credential Encryption](#121-credential-encryption)
  - [12.2 Secrets Management](#122-secrets-management)
  - [12.3 Security Best Practices](#123-security-best-practices)
- [13. REST APIs](#13-rest-apis)
  - [13.1 API Standards](#131-api-standards)
  - [13.2 Endpoint Conventions](#132-endpoint-conventions)
  - [13.3 Response Formats](#133-response-formats)
  - [13.4 API Reference](#134-api-reference)
- [14. Logging](#14-logging)
- [15. Caching](#15-caching)
  - [15.1 Redis](#151-redis)
- [16. Testing Strategy](#16-testing-strategy)
  - [16.1 Backend Testing (pytest)](#161-backend-testing-pytest)
  - [16.2 Test Fixtures](#162-test-fixtures)
  - [16.3 Writing Backend Tests](#163-writing-backend-tests)
  - [16.4 Frontend Testing](#164-frontend-testing)
  - [16.5 Quality Gates](#165-quality-gates)
- [17. CI/CD](#17-cicd)
  - [17.1 GitHub Actions](#171-github-actions)
  - [17.2 Quality Gate Script](#172-quality-gate-script)
  - [17.3 Future CI/CD Improvements](#173-future-cicd-improvements)
- [18. Docker](#18-docker)
  - [18.1 Docker Compose Architecture](#181-docker-compose-architecture)
  - [18.2 Service Descriptions](#182-service-descriptions)
  - [18.3 Backend Dockerfile](#183-backend-dockerfile)
  - [18.4 Frontend Dockerfile](#184-frontend-dockerfile)
  - [18.5 Nginx Configuration](#185-nginx-configuration)
- [19. Debugging](#19-debugging)
- [20. Performance](#20-performance)
- [21. Provider Development](#21-provider-development)
  - [21.1 How to Build a Provider](#211-how-to-build-a-provider)
  - [21.2 How to Build a Service](#212-how-to-build-a-service)
  - [21.3 How to Build a Repository](#213-how-to-build-a-repository)
  - [21.4 How to Build a Router](#214-how-to-build-a-router)
- [22. Frontend Development](#22-frontend-development)
  - [22.1 How to Build Dashboard Widgets](#221-how-to-build-dashboard-widgets)
  - [22.2 How to Add Navigation](#222-how-to-add-navigation)
  - [22.3 How to Add Pages](#223-how-to-add-pages)
  - [22.4 How to Add Tests](#224-how-to-add-tests)
- [23. Mission Control Agent Development](#23-mission-control-agent-development)
- [24. Automation Engine Development](#24-automation-engine-development)
- [25. AI Operations Development](#25-ai-operations-development)
- [26. Plugin Development](#26-plugin-development)
  - [26.1 Plugin SDK](#261-plugin-sdk)
  - [26.2 Plugin Manifest](#262-plugin-manifest)
  - [26.3 Plugin Registration](#263-plugin-registration)
  - [26.4 Plugin Lifecycle](#264-plugin-lifecycle)
  - [26.5 Plugin Security](#265-plugin-security)
  - [26.6 Plugin Examples](#266-plugin-examples)
- [27. Migration Guide](#27-migration-guide)
- [28. Release Process](#28-release-process)
  - [28.1 Versioning](#281-versioning)
  - [28.2 Git Workflow](#282-git-workflow)
  - [28.3 Branch Strategy](#283-branch-strategy)
  - [28.4 Pull Requests](#284-pull-requests)
  - [28.5 Code Reviews](#285-code-reviews)
- [29. Future Development Standards](#29-future-development-standards)
  - [29.1 Architecture Principles](#291-architecture-principles)
  - [29.2 Future Kubernetes Deployment](#292-future-kubernetes-deployment)
- [30. Appendices](#30-appendices)
  - [30.1 Directory Structure](#301-directory-structure)
  - [30.2 Glossary](#302-glossary)
  - [30.3 Useful Commands](#303-useful-commands)

---

## 1. Introduction

### 1.1 Vision

**One dashboard. One workflow. One place to manage everything.**

Mission Control is a full-stack IT operations platform for managing remote infrastructure, monitoring system health, and executing commands from a unified dashboard. It is built for senior IT professionals and system administrators who need to manage heterogeneous environments from a single pane of glass.

### 1.2 What Mission Control Does

Mission Control provides:

- **Remote Operations** — SSH/WinRM host management, encrypted credential vault, command execution, file browsing, bulk execution, and scheduled commands
- **Infrastructure Monitoring** — System metrics (CPU, memory, disk), Docker container status, Git repository health
- **Virtualization Management** — Hyper-V and Proxmox VE VM lifecycle, networking, storage, and snapshots
- **Identity Integration** — Active Directory and Microsoft 365 directory browsing
- **Monitoring Integration** — Zabbix host monitoring, triggers, events, and dashboards
- **Automation Engine** — Playbook-based automation with multi-provider execution, approval workflows, and audit trails
- **AI Operations** — Incident classification, correlation analysis, and recommendation engine
- **Agent System** — Remote agent registration, heartbeat, and command dispatch
- **Multi-Tenancy** — Company and site-based tenant isolation

### 1.3 How to Use This Guide

This guide is organized from high-level architecture to implementation details:

1. **Start with Sections 1–3** for project overview, structure, and technology
2. **Read Sections 4–6** for coding standards and architectural patterns
3. **Reference Sections 7–12** as needed for database, API, and security details
4. **Follow Sections 21–22** as step-by-step tutorials for common development tasks

---

## 2. Repository Structure

### 2.1 Top-Level Layout

```
MissionControl/
├── backend/                  # Python/FastAPI backend application
├── frontend/                 # React/Vite/TypeScript frontend application
├── nginx/                    # Reverse proxy configuration
├── website/                  # Marketing website (Next.js, separate)
├── scripts/                  # PowerShell CLI and development scripts
├── tests/                    # PowerShell Pester tests for CLI
├── docs/                     # Architecture docs, roadmap, decisions
├── .github/                  # GitHub Actions CI/CD
├── docker-compose.yml        # 5-service Docker Compose stack
├── .env.example              # Environment variable template
├── CONTRIBUTING.md           # Contribution guidelines
├── CHANGELOG.md              # Sprint changelog
├── README.md                 # Project overview
└── VERSION                   # Current version (0.1.0)
```

### 2.2 Backend Layout

```
backend/
├── app/                      # Main application package
│   ├── main.py               # FastAPI application entry point
│   ├── core/                 # Configuration, security, auth
│   │   ├── config.py         # Pydantic Settings (env management)
│   │   ├── security.py       # Fernet credential encryption
│   │   ├── auth_dependency.py # FastAPI auth dependency
│   │   └── company_context.py # Multi-tenant context
│   ├── db/                   # Database engine, sessions, health
│   │   ├── database.py       # Engine, session factory, Base
│   │   ├── postgres.py       # Async PostgreSQL health check
│   │   └── redis.py          # Async Redis health check
│   ├── models/db/            # 27 SQLAlchemy ORM models
│   ├── schemas/              # 33 Pydantic request/response schemas
│   ├── repositories/         # 24 data access repositories
│   ├── services/             # 27 business logic services
│   ├── routers/              # 26 FastAPI route handlers
│   ├── providers/            # Domain-specific providers
│   │   ├── automation/       # Automation execution providers
│   │   ├── hyperv/           # Hyper-V virtualization providers
│   │   ├── identity/         # AD/M365 identity providers
│   │   ├── proxmox/          # Proxmox VE providers
│   │   ├── remote/           # SSH/WinRM remote providers
│   │   ├── virtualization/   # Virtualization base classes
│   │   └── zabbix/           # Zabbix monitoring providers
│   ├── infrastructure/       # Docker SDK provider
│   ├── platform/             # OS platform abstraction
│   ├── ai/                   # AI operations engine
│   ├── seed/                 # Idempotent database seeders
│   └── utils/                # Shared utilities
├── alembic/                  # Database migrations (20+ versions)
│   ├── env.py                # Alembic environment config
│   ├── script.py.mako        # Migration template
│   └── versions/             # Migration files
├── tests/                    # 32 pytest test files
│   ├── conftest.py           # Shared fixtures
│   └── api/                  # API integration tests
├── alembic.ini               # Alembic configuration
├── pyproject.toml            # Ruff/Black config
├── pytest.ini                # pytest configuration
├── requirements.txt          # Python dependencies
├── Dockerfile                # Python 3.12-slim image
└── entrypoint.sh             # Startup script (migrate, seed, serve)
```

### 2.3 Frontend Layout

```
frontend/
├── src/
│   ├── main.tsx              # React entry point
│   ├── App.tsx               # Router + Provider tree + all routes
│   ├── styles.css            # Monolithic dark-theme CSS (4200+ lines)
│   ├── config/
│   │   └── navigation.ts     # Static navigation tree
│   ├── types/                # TypeScript type definitions
│   │   ├── dashboard.ts      # Dashboard response interfaces
│   │   ├── navigation.ts     # NavItem/NavGroup interfaces
│   │   └── automation.ts     # Playbook/Execution types
│   ├── services/             # 14 API client modules
│   │   ├── api.ts            # Dashboard API
│   │   ├── auth.ts           # Authentication API
│   │   ├── remote.ts         # Remote operations API
│   │   ├── automation.ts     # Automation/playbook API
│   │   └── ...               # One file per domain
│   ├── contexts/             # 3 React Context providers
│   │   ├── AuthContext.tsx    # Authentication state
│   │   ├── SidebarContext.tsx # Sidebar collapse state
│   │   └── ToastContext.tsx   # Toast notifications
│   ├── hooks/                # Custom hooks (currently empty)
│   ├── layouts/              # Layout shell components
│   │   ├── AppLayout.tsx     # Main layout (sidebar + content)
│   │   ├── Sidebar.tsx       # Collapsible sidebar navigation
│   │   ├── TopBar.tsx        # Top header with breadcrumb
│   │   ├── Breadcrumb.tsx    # Auto-generated breadcrumb
│   │   └── StatusBar.tsx     # Bottom status bar
│   ├── components/
│   │   ├── Toast.tsx         # Toast notification system
│   │   ├── common/           # Reusable UI primitives
│   │   ├── dashboard/        # Dashboard card components
│   │   ├── modals/           # Domain-specific modals
│   │   ├── sidebar/          # Sidebar sub-components
│   │   ├── hyperv/           # Hyper-V specific components
│   │   └── zabbix/           # Zabbix specific components
│   └── pages/                # 65+ page components
│       ├── auth/             # LoginPage
│       ├── infrastructure/   # System, Docker, Git, Health
│       ├── remote/           # Hosts, Credentials, Console, etc.
│       ├── identity/         # AD, M365
│       ├── zabbix/           # Hosts, Problems, Triggers, etc.
│       ├── hyperv/           # VMs, Networks, Storage, etc.
│       ├── proxmox/          # Nodes, VMs, Containers, etc.
│       ├── ai/               # Recommendations, Incidents, etc.
│       ├── agents/           # Agent management
│       ├── automation/       # Playbooks, Executions, etc.
│       ├── settings/         # General, Users, Integrations
│       └── companies/        # Company management
├── package.json
├── vite.config.ts
├── tsconfig.json
├── eslint.config.js
├── Dockerfile                # Multi-stage: Node build → Nginx serve
└── nginx.conf                # SPA fallback config
```

### 2.4 Infrastructure Layout

```
nginx/
└── default.conf              # Reverse proxy routing rules

scripts/
├── mc.ps1                    # Main CLI entry point (PowerShell 7+)
├── Invoke-Quality.ps1        # Quality gate runner
├── verify.ps1                # Environment verification
├── rebuild.ps1               # Docker clean rebuild
├── lib/                      # 12 CLI framework modules
│   ├── Registry.ps1          # Command registry
│   ├── Bootstrap.ps1         # Context/option parsing
│   ├── Config.ps1            # Configuration management
│   ├── Output.ps1            # Output formatting
│   ├── Logger.ps1            # Log file management
│   ├── Validation.ps1        # Argument validation
│   └── ...                   # Docker, Git, Http, etc.
└── commands/                 # 13 CLI command modules
    ├── Build.ps1, Clean.ps1, Dev.ps1, Docker.ps1
    ├── Doctor.ps1, Git.ps1, Help.ps1, Lint.ps1
    ├── Project.ps1, Sprint.ps1, Status.ps1
    ├── Test.ps1, Version.ps1
```

---

## 3. Technology Stack

### 3.1 Backend Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Language | Python | 3.12 | Backend runtime |
| Framework | FastAPI | 0.115+ | Async HTTP framework |
| ORM | SQLAlchemy | 2.0 | Database access (mapped_column style) |
| Validation | Pydantic v2 | 2.x | Request/response validation |
| Database | PostgreSQL | 16 | Primary data store |
| Cache | Redis | 7.2 | Health checks, caching |
| Migrations | Alembic | 1.13+ | Schema versioning |
| Encryption | cryptography (Fernet) | 43+ | Credential at-rest encryption |
| Remote | Paramiko / pywinrm | — | SSH and WinRM execution |
| Server | Uvicorn | — | ASGI server |
| Docker SDK | docker | 7+ | Container management |

### 3.2 Frontend Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Language | TypeScript | 5.5 | Type-safe JavaScript |
| Framework | React | 18.3 | UI framework |
| Bundler | Vite | 5.4 | Build tool and dev server |
| Router | react-router-dom | 7.18 | Client-side routing |
| Styling | Custom CSS | — | Dark-theme monolithic CSS |
| Terminal | @xterm/xterm | 6.x | Interactive SSH console |
| Linting | ESLint | 9.x | Code quality |
| Type Checking | TypeScript strict | — | Strict mode enabled |

### 3.3 Infrastructure Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Containerization | Docker Compose | Multi-service orchestration |
| Reverse Proxy | Nginx 1.27 | Static files + API proxy |
| CI/CD | GitHub Actions | Quality gate automation |
| CLI | PowerShell 7 | Developer tooling |

### 3.4 Development Tools

| Tool | Purpose | Config |
|------|---------|--------|
| Ruff | Python linting | `backend/pyproject.toml` |
| Black | Python formatting | `backend/pyproject.toml` |
| ESLint | TypeScript linting | `frontend/eslint.config.js` |
| pytest | Python testing | `backend/pytest.ini` |
| Pester | PowerShell testing | Inline `Describe`/`It` blocks |

---

## 4. Coding Standards

### 4.1 Python Standards

- **Python version:** 3.12+
- **Line length:** 88 characters (Black/Ruff default)
- **Formatter:** Black
- **Linter:** Ruff with rules: `E`, `F`, `I`, `UP`, `B`
- **Imports:** Sorted by isort convention (via Ruff `I` rule)
- **Type hints:** Used on all function signatures and class attributes
- **Docstrings:** Google-style, present on all public methods
- **String quotes:** Double quotes for strings (Black default)
- **f-strings:** Preferred for string interpolation
- **Async/await:** Used for all I/O-bound operations (providers, services)

**Ruff Configuration:**

```toml
# backend/pyproject.toml
[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
extend-ignore = ["E501", "B008"]
```

### 4.2 TypeScript Standards

- **TypeScript version:** 5.5+
- **Strict mode:** Enabled (`"strict": true`)
- **Target:** ES2020
- **Module:** ESNext with Bundler resolution
- **React:** Function components only (no class components)
- **JSX:** `react-jsx` (automatic runtime)
- **Unused variables:** Error on unused vars (ignores `_` prefixed)
- **Exports:** Default exports for components and pages

### 4.3 Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Python files | `snake_case.py` | `task_service.py` |
| Python classes | `PascalCase` | `TaskService`, `RemoteHost` |
| Python functions | `snake_case` | `get_by_id`, `create_task` |
| Python constants | `UPPER_SNAKE` | `ROLE_HIERARCHY` |
| Python modules | `snake_case` | `task_repository.py` |
| TypeScript files | `PascalCase.tsx` / `camelCase.ts` | `TaskPage.tsx`, `remote.ts` |
| TypeScript interfaces | `PascalCase` | `TaskData`, `HostCreateInput` |
| TypeScript functions | `camelCase` | `handleSave`, `loadData` |
| React components | `PascalCase` | `TaskPage`, `DataTable` |
| CSS classes | BEM-like | `.stat-card-value`, `.sidebar-nav-item` |
| Database tables | `snake_case` | `tasks`, `remote_hosts` |
| API endpoints | `kebab-case` | `/remote/hosts`, `/playbook-executions` |

### 4.4 File Organization

**Backend file naming pattern:**
```
models/db/{entity}.py          → SQLAlchemy ORM model
schemas/{entity}.py            → Pydantic request/response schemas
repositories/{entity}_repository.py → Data access layer
services/{entity}_service.py   → Business logic
routers/{entity}.py            → API route handlers
providers/{domain}/            → Provider implementations
```

**Frontend file naming pattern:**
```
pages/{Domain}/{Entity}Page.tsx    → Page components
components/{domain}/{Entity}.tsx   → Reusable components
services/{domain}.ts               → API client modules
contexts/{Name}Context.tsx         → Context providers
config/navigation.ts               → Navigation tree
types/{domain}.ts                  → TypeScript interfaces
```

---

## 5. Project Architecture

### 5.1 Architecture Overview

Mission Control follows a **Modular Monolith** architecture with clear layered separation:

```mermaid
graph TB
    subgraph Frontend["React Frontend"]
        Pages["Pages (65+)"]
        Components["Components"]
        Services["API Services (14)"]
        Contexts["Contexts (3)"]
    end

    subgraph Backend["FastAPI Backend"]
        Routers["Routers (26)"]
        Services2["Services (27)"]
        Repositories["Repositories (24)"]
        Providers["Providers (12+ domains)"]
        Models["ORM Models (27)"]
        Schemas["Pydantic Schemas (33)"]
    end

    subgraph Data["Data Layer"]
        PostgreSQL["PostgreSQL 16"]
        Redis["Redis 7.2"]
    end

    subgraph External["External Systems"]
        SSH["SSH Hosts"]
        WinRM["WinRM Hosts"]
        Docker["Docker Engine"]
        Zabbix["Zabbix"]
        HyperV["Hyper-V"]
        Proxmox["Proxmox VE"]
        AD["Active Directory"]
        M365["Microsoft 365"]
        LLM["LLM Providers"]
    end

    Pages --> Services
    Services --> Routers
    Routers --> Services2
    Services2 --> Repositories
    Services2 --> Providers
    Repositories --> Models
    Models --> PostgreSQL
    Providers --> External
    Redis -.-> Backend
```

**Key architectural principles:**

1. **Layered Separation** — Routers never access the database directly; they delegate to Services
2. **Strategy Pattern** — Infrastructure integrations use abstract base classes with concrete implementations
3. **Convention over Configuration** — Patterns are followed by convention, not enforced by a framework
4. **Convention-Based DI** — FastAPI `Depends()` for dependency injection, module-level singletons for services

### 5.2 Backend Structure

The backend follows a strict **four-layer architecture**:

```
HTTP Request
    ↓
┌─────────────┐
│   Router     │  ← Validates HTTP, delegates to service
├─────────────┤
│   Service    │  ← Business logic, validation, orchestration
├─────────────┤
│  Repository  │  ← Data access, SQLAlchemy queries
├─────────────┤
│ ORM Model    │  ← Database table definition
└─────────────┘
    ↓
PostgreSQL
```

Additionally, **Providers** sit alongside Services to encapsulate external system interactions (SSH, Docker, Zabbix, etc.). Providers are consumed by Services, never by Routers.

### 5.3 Frontend Structure

```
User Interaction
    ↓
┌─────────────┐
│    Page      │  ← Route-specific component
├─────────────┤
│  Component   │  ← Reusable UI building blocks
├─────────────┤
│   Service    │  ← API client (fetch wrapper)
├─────────────┤
│    API       │  ← Backend REST endpoint
└─────────────┘
    ↓
FastAPI Backend
```

### 5.4 Request Lifecycle

```mermaid
sequenceDiagram
    participant Browser
    participant Nginx
    participant FastAPI
    participant Router
    participant Service
    participant Repository
    participant PostgreSQL

    Browser->>Nginx: GET /api/v1/tasks
    Nginx->>FastAPI: Proxy to backend:8000
    FastAPI->>Router: Route handler
    Router->>Router: Depends(get_db), Depends(get_task_service)
    Router->>Service: service.get_all(db)
    Service->>Repository: TaskRepository.get_all(db)
    Repository->>PostgreSQL: SELECT * FROM tasks
    PostgreSQL-->>Repository: Row results
    Repository-->>Service: List[Task] ORM objects
    Service-->>Router: TaskListResponse (Pydantic)
    Router-->>FastAPI: JSON response
    FastAPI-->>Nginx: HTTP 200
    Nginx-->>Browser: JSON response
```

---

## 6. Backend Patterns

### 6.1 Router Pattern

Routers are thin FastAPI `APIRouter` instances that define HTTP endpoints and delegate all logic to services.

**Characteristics:**
- Each router defines its own `APIRouter` with `prefix` and `tags`
- Route handlers use `Depends(get_db)` for database sessions
- Route handlers use `Depends(get_*_service)` for service injection
- No business logic in routers — only HTTP concerns
- Explicit response models and status codes

**Example — `backend/app/routers/tasks.py`:**

```python
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.task import TaskCreate, TaskListResponse, TaskResponse, TaskUpdate
from app.services.task_service import TaskService, task_service

router = APIRouter(prefix="/tasks", tags=["Tasks"])


def get_task_service() -> TaskService:
    """Provide the shared task service instance."""
    return task_service


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    db: Session = Depends(get_db),
    service: TaskService = Depends(get_task_service),
) -> TaskListResponse:
    return await service.get_all(db)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    return await service.get_by_id(db, task_id)


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    return await service.create(db, payload)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    return await service.update(db, task_id, payload)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    service: TaskService = Depends(get_task_service),
) -> None:
    await service.delete(db, task_id)
```

**Key conventions:**

| Convention | Detail |
|-----------|--------|
| Module-level singleton | `task_service = TaskService()` |
| Factory function | `def get_task_service() -> TaskService:` |
| Dependency injection | `Depends(get_task_service)` in route signature |
| Status codes | 200 for success, 201 for creation, 204 for deletion |
| Response models | Explicit `response_model=` on every endpoint |
| Docstrings | `summary` and `description` on router decorators |

**All 26 routers are registered in `backend/app/main.py`:**

```python
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(remote.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
# ... 23 more routers
```

### 6.2 Service Pattern

Services contain all business logic between the API layer and data access layer.

**Characteristics:**
- Stateless classes instantiated as module-level singletons
- Accept `db: Session` as the first parameter
- Use repositories for data access
- Use providers for external system interaction
- Return Pydantic response models
- Raise `HTTPException` for business errors (404, 409, 422)
- No abstract base class — convention-based

**Example — `backend/app/services/task_service.py`:**

```python
import logging
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.db.task import Task
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.task import TaskCreate, TaskListResponse, TaskResponse, TaskUpdate

logger = logging.getLogger(__name__)


class TaskService:
    """Task dashboard section."""

    def __init__(self, repository: TaskRepository | None = None) -> None:
        self._repository = repository or TaskRepository()

    async def get_all(self, db: Session) -> TaskListResponse:
        """Return all tasks as API response models."""
        logger.info("Fetching all tasks")
        tasks = self._repository.get_all(db)
        items = [TaskResponse.model_validate(task) for task in tasks]
        return TaskListResponse(count=len(items), items=items)

    async def get_by_id(self, db: Session, task_id: int) -> TaskResponse:
        """Return a single task as an API response model."""
        logger.info("Fetching task id=%s", task_id)
        task = self._repository.get_by_id(db, task_id)
        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )
        return TaskResponse.model_validate(task)

    async def create(self, db: Session, data: TaskCreate) -> TaskResponse:
        """Create a new task and return the API response model."""
        logger.info("Creating task: %s", data.title)

        # Validate parent project exists
        if ProjectRepository().get_by_id(db, data.project_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # Check for duplicates
        if self._repository.get_by_project_and_title(db, data.project_id, data.title) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Task already exists",
            )

        task = self._repository.create(db, data)
        return TaskResponse.model_validate(task)

    async def update(self, db: Session, task_id: int, data: TaskUpdate) -> TaskResponse:
        """Update an existing task."""
        existing = self._repository.get_by_id(db, task_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )
        # ... validation logic ...
        updated = self._repository.update(db, task_id, data)
        return TaskResponse.model_validate(updated)

    async def delete(self, db: Session, task_id: int) -> None:
        """Delete a task by identifier."""
        deleted = self._repository.delete(db, task_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )


task_service = TaskService()
```

**Error handling convention:**

| HTTP Status | When |
|-------------|------|
| `404 Not Found` | Entity does not exist |
| `409 Conflict` | Duplicate entity (unique constraint) |
| `422 Unprocessable Entity` | Validation error (Pydantic) |
| `400 Bad Request` | Invalid input for business rule |

### 6.3 Repository Pattern

Repositories encapsulate all database access for a single entity using **static methods**.

**Characteristics:**
- All methods are `@staticmethod` taking `db: Session` as first argument
- No base class — pure convention
- Accept Pydantic schemas for create/update operations
- Return ORM entities (not dicts)
- Return `None` or `False` for not-found (never raise exceptions)
- Commit and refresh after mutations

**Example — `backend/app/repositories/task_repository.py`:**

```python
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.db.task import Task
from app.schemas.task import TaskCreate, TaskUpdate


class TaskRepository:
    """Data access layer for tasks stored in PostgreSQL."""

    @staticmethod
    def get_all(db: Session) -> list[Task]:
        """Return all tasks ordered by creation date descending."""
        stmt = (
            select(Task)
            .options(selectinload(Task.project))
            .order_by(Task.created_at.desc())
        )
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_id(db: Session, task_id: int) -> Task | None:
        """Return a single task by identifier."""
        stmt = select(Task).where(Task.id == task_id)
        return db.scalar(stmt)

    @staticmethod
    def create(db: Session, task: TaskCreate) -> Task:
        """Persist a new task."""
        entity = Task(
            project_id=task.project_id,
            title=task.title.strip(),
            description=task.description,
            status=task.status,
            priority=task.priority,
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def update(db: Session, task_id: int, task: TaskUpdate) -> Task | None:
        """Update an existing task with only the supplied fields."""
        entity = TaskRepository.get_by_id(db, task_id)
        if entity is None:
            return None

        updates = task.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(entity, field, value)

        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def delete(db: Session, task_id: int) -> bool:
        """Delete a task by identifier."""
        entity = TaskRepository.get_by_id(db, task_id)
        if entity is None:
            return False
        db.delete(entity)
        db.commit()
        return True

    @staticmethod
    def get_count(db: Session) -> int:
        """Return the total number of tasks."""
        stmt = select(func.count()).select_from(Task)
        return db.scalar(stmt) or 0
```

**Standard CRUD method signatures:**

| Method | Returns | Not Found |
|--------|---------|-----------|
| `get_all(db)` | `list[Entity]` | Empty list |
| `get_by_id(db, id)` | `Entity \| None` | `None` |
| `create(db, schema)` | `Entity` | N/A |
| `update(db, id, schema)` | `Entity \| None` | `None` |
| `delete(db, id)` | `bool` | `False` |

### 6.4 Provider Pattern

Providers encapsulate interaction with external systems. The codebase uses two distinct provider styles:

#### 6.4.1 Dashboard Providers (Stateless Singletons)

Dashboard providers are stateless classes with no abstract base. They return dicts and never raise exceptions.

**Example:**

```python
class DockerProvider:
    async def get_docker_data(self) -> dict:
        try:
            docker = get_docker_provider()
            info = await docker.info()
            return {
                "available": True,
                "engine": "running",
                "docker_version": info.get("version", "unknown"),
                "container_count": info.get("containers", 0),
            }
        except Exception as exc:
            return self._unavailable(str(exc))

    @staticmethod
    def _unavailable(reason: str) -> dict:
        return {"available": False, "reason": reason}


docker_provider = DockerProvider()
```

#### 6.4.2 Subsystem Providers (ABC + Factory)

Subsystem providers use a full OOP hierarchy with abstract base classes, concrete implementations, mock implementations, and factory functions.

**Base class example — `backend/app/providers/automation/base_provider.py`:**

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class StepResult:
    """Result of executing a single playbook step."""
    success: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    duration_ms: int = 0
    error: str | None = None


@dataclass
class ExecutionContext:
    """Context passed to providers during step execution."""
    playbook_id: int
    execution_id: int
    step_id: int
    step_name: str
    command: str
    provider: str
    target_host: str | None = None
    shell: str | None = None
    timeout_seconds: int = 300
    variables: dict[str, str] | None = None


class AutomationProvider(ABC):
    """Abstract base class for automation execution providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @property
    @abstractmethod
    def supported_step_types(self) -> list[str]: ...

    @abstractmethod
    async def execute_step(self, context: ExecutionContext) -> StepResult: ...

    @abstractmethod
    async def validate_step(self, context: ExecutionContext) -> dict: ...

    @abstractmethod
    async def rollback_step(self, context: ExecutionContext, rollback_command: str) -> StepResult: ...
```

**Factory example:**

```python
# backend/app/providers/automation/provider_factory.py

_provider_cache: dict[str, AutomationProvider] = {}

PROVIDER_MAP: dict[str, type[AutomationProvider]] = {
    "bash": BashAutomationProvider,
    "powershell": PowerShellAutomationProvider,
    "http": HTTPAutomationProvider,
    "ssh": SSHAutomationProvider,
    "winrm": WinRMAutomationProvider,
    "agent": AgentAutomationProvider,
    "hyperv": HyperVAutomationProvider,
    "proxmox": ProxmoxAutomationProvider,
}


def get_automation_provider(name: str) -> AutomationProvider:
    """Return a cached singleton provider by name."""
    if name not in _provider_cache:
        cls = PROVIDER_MAP.get(name)
        if cls is None:
            raise ValueError(f"Unknown automation provider: {name}")
        _provider_cache[name] = cls()
    return _provider_cache[name]
```

**Complete provider hierarchy:**

| Domain | Base Class | Implementations | Factory |
|--------|-----------|----------------|---------|
| Automation | `AutomationProvider` (ABC) | Bash, PowerShell, HTTP, SSH, WinRM, Agent, Hyper-V, Proxmox | `get_automation_provider(name)` |
| Remote | `RemoteBaseProvider` (ABC) | SSH, WinRM | `get_remote_provider(type)` |
| Identity | `ActiveDirectoryProvider` (ABC), `Microsoft365Provider` (ABC) | LDAP, Graph, Mock | `get_active_directory_provider()` |
| Hyper-V | `VirtualizationProvider` → `HyperVProvider` (ABC) | Production, Mock | `get_hyperv_provider(profile_id)` |
| Proxmox | `VirtualizationProvider` → `ProxmoxProvider` (ABC) | Production, Mock | `get_proxmox_provider(profile_id)` |
| Zabbix | `ZabbixProvider` (ABC) | Production, Mock | `get_zabbix_provider(profile_id)` |
| AI | `AIProvider` (ABC) | Ollama, OpenAI, Azure, Anthropic, Local, RuleBased | Factory from DB profile |
| Infrastructure | `DockerProvider` (ABC) | DockerSdkProvider | `get_docker_provider()` |

### 6.5 Dependency Injection

Mission Control uses **FastAPI's built-in `Depends()`** as its DI mechanism. There is no external DI container.

**DI patterns in use:**

```python
# 1. Database session injection
@router.get("")
async def list_tasks(db: Session = Depends(get_db)): ...

# 2. Service injection via factory function
def get_task_service() -> TaskService:
    return task_service

@router.get("")
async def list_tasks(service: TaskService = Depends(get_task_service)): ...

# 3. Authentication injection
@router.get("")
async def list_tasks(user: User = Depends(get_current_user)): ...

# 4. Multi-tenant context injection
@router.get("")
async def list_tasks(ctx: CompanyContext = Depends(get_company_ctx)): ...
```

**Singleton instantiation pattern:**

```python
# Module-level singleton (most common)
task_service = TaskService()
docker_provider = DockerProvider()

# Factory function for DI
def get_task_service() -> TaskService:
    return task_service
```

### 6.6 Factories

Factories are used extensively for subsystem providers that have multiple implementations:

| Factory | Location | Returns |
|---------|----------|---------|
| `get_automation_provider(name)` | `providers/automation/provider_factory.py` | `AutomationProvider` subclass |
| `get_remote_provider(type)` | `providers/remote/provider_factory.py` | `SSHProvider` or `WinRMProvider` |
| `get_active_directory_provider()` | `providers/identity/provider_factory.py` | `LDAPActiveDirectoryProvider` or `MockActiveDirectoryProvider` |
| `get_hyperv_provider(profile_id)` | `providers/hyperv/provider_factory.py` | `HyperVProvider` subclass |
| `get_proxmox_provider(profile_id)` | `providers/proxmox/provider_factory.py` | `ProxmoxProvider` subclass |
| `get_zabbix_provider(profile_id)` | `providers/zabbix/provider_factory.py` | `ZabbixProvider` subclass |
| `get_docker_provider()` | `infrastructure/docker/factory.py` | `DockerSdkProvider` |

**Factory pattern characteristics:**
- Caches singleton instances (never recreates)
- Checks configuration/DB profile before returning production provider
- Falls back to Mock provider when external system is not configured
- Profiles are keyed by `IntegrationProfile.id` for per-site isolation

---

## 7. Database Layer

### 7.1 SQLAlchemy Models

All 27 models inherit from `Base` (SQLAlchemy 2.0 `DeclarativeBase`) and use the modern `Mapped`/`mapped_column` style.

**Location:** `backend/app/models/db/`

**Example — `backend/app/models/db/task.py`:**

```python
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.db.project import Project


class Task(Base):
    """Task belonging to a project."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    company_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    site_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    priority: Mapped[str] = mapped_column(String(50), nullable=False, default="medium")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    project: Mapped["Project"] = relationship("Project", back_populates="tasks")
```

**Model conventions:**

| Convention | Detail |
|-----------|--------|
| Primary key | `id: Mapped[int]` with `primary_key=True, index=True` |
| Multi-tenancy | `company_id` and `site_id` on most entities (nullable) |
| Timestamps | `created_at` and `updated_at` with `datetime.now(UTC)` lambdas |
| Foreign keys | `ForeignKey("table.id", ondelete="CASCADE")` or `"SET NULL"` |
| Relationships | Use `TYPE_CHECKING` imports to avoid circular imports |
| Table name | `snake_case` plural (`tasks`, `remote_hosts`) |
| String columns | Explicit `String(N)` length |

**Complete model inventory (27 models):**

| Model | Table | Category |
|-------|-------|----------|
| `Company` | `companies` | Multi-tenancy |
| `Site` | `sites` | Multi-tenancy |
| `User` | `users` | Authentication |
| `Project` | `projects` | Project management |
| `Task` | `tasks` | Project management |
| `Note` | `notes` | Project management |
| `Resume` | `resumes` | Project management |
| `ParkingLot` | `parking_lot` | Project management |
| `RemoteHost` | `remote_hosts` | Remote operations |
| `CredentialProfile` | `credential_profiles` | Remote operations |
| `CommandHistory` | `command_history` | Remote operations |
| `CommandTemplate` | `command_templates` | Remote operations |
| `ScheduledCommand` | `scheduled_commands` | Remote operations |
| `Agent` | `agents` | Agent system |
| `AgentCommand` | `agent_commands` | Agent system |
| `AgentRegistrationToken` | `agent_registration_tokens` | Agent system |
| `Playbook` | `playbooks` | Automation |
| `PlaybookStep` | `playbook_steps` | Automation |
| `PlaybookVariable` | `playbook_variables` | Automation |
| `PlaybookExecution` | `playbook_executions` | Automation |
| `PlaybookSchedule` | `playbook_schedules` | Automation |
| `EventTrigger` | `event_triggers` | Automation |
| `ApprovalWorkflow` | `approval_workflows` | Automation |
| `ApprovalRequest` | `approval_requests` | Automation |
| `ExecutionLog` | `execution_logs` | Automation |
| `AuditTrail` | `audit_trail` | Audit |
| `IntegrationProfile` | `integration_profiles` | Integration |

### 7.2 Pydantic Schemas

Every entity follows a consistent **four-schema pattern**:

| Schema | Purpose | Convention |
|--------|---------|-----------|
| `{Entity}Create` | POST request body | Required fields with `Field(...)`, validation rules |
| `{Entity}Update` | PATCH request body | All fields optional (`str \| None = None`) |
| `{Entity}Response` | Single entity response | `model_config = ConfigDict(from_attributes=True)` |
| `{Entity}ListResponse` | Paginated list | `{ count: int, items: list[{Entity}Response] }` |

**Example — `backend/app/schemas/task.py`:**

```python
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class TaskCreate(BaseModel):
    """Payload for creating a new task."""

    project_id: int = Field(..., description="Identifier of the parent project.")
    title: str = Field(..., min_length=1, max_length=200, description="Short task title.")
    description: str | None = Field(default=None, max_length=1000)
    status: str = Field(default="pending", max_length=50)
    priority: str = Field(default="medium", max_length=50)


class TaskUpdate(BaseModel):
    """Payload for updating an existing task."""

    project_id: int | None = Field(default=None)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    status: str | None = Field(default=None, max_length=50)
    priority: str | None = Field(default=None, max_length=50)


class TaskResponse(BaseModel):
    """Task returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    title: str
    description: str | None = None
    status: str
    priority: str
    created_at: datetime
    updated_at: datetime


class TaskListResponse(BaseModel):
    """Paginated-style list of tasks."""

    count: int
    items: list[TaskResponse]
```

**Schema conventions:**
- Every field includes `Field(...)` with `description` and `examples`
- `TaskCreate` uses `Field(...)` for required fields
- `TaskUpdate` uses `Field(default=None)` for all fields
- `TaskResponse` includes `model_config = ConfigDict(from_attributes=True)` for ORM compatibility
- Sensitive fields (passwords, keys) are excluded from Response schemas

### 7.3 Alembic Migrations

**Location:** `backend/alembic/`

Alembic manages all schema changes with versioned migration files.

**Configuration:** `backend/alembic.ini`

```ini
[alembic]
script_location = alembic
sqlalchemy.url = postgresql+psycopg://mission_control:mission_control@postgres:5432/mission_control
```

The URL is overridden at runtime in `env.py` via `get_settings().database_url`.

**Migration chain (20+ versions):**

| Migration | Description |
|-----------|-------------|
| `c80e36246a04` | Initial schema — `projects` table |
| `d91f47357b15` | Add `tasks` table |
| `e02a58468c26` | Add `notes` table |
| `c1d2e3f4a5b6` | Create `companies` table |
| `e3f4a5b6c7d8` | Tenant isolation — add `company_id`/`site_id` to 20+ tables |
| `f4a5b6c7d8e9` | Create `users` table |
| `i9j0k1l2m3n4` | Create remote operations tables |
| `o5p6q7r8s9t0` | Add encrypted credential columns |
| `x3y4z5a6b7c8` | Add automation and playbooks |
| `x1y2z3a4b5c6` | Add agent tables |
| `n1a2b3c4d5e6` | Add automation performance indexes |
| `w1x2y3z4a5b6` | Add integration profiles |

**Creating a new migration:**

```bash
cd backend
alembic revision --autogenerate -m "description of changes"
alembic upgrade head
```

**Important:** The `env.py` imports all models via `from app.models.db import *` for autogenerate support. Always ensure new models are imported in `models/db/__init__.py`.

### 7.4 Multi-Tenancy

Mission Control uses a **two-level multi-tenancy model**: Company → Site.

**Tenant isolation is enforced at the query level**, not via database row-level security:

```python
# Repository-level tenant filtering
@staticmethod
def get_all(db: Session, company_id: int | None = None, site_id: int | None = None) -> list[Task]:
    stmt = select(Task)
    if company_id is not None:
        stmt = stmt.where(Task.company_id == company_id)
    if site_id is not None:
        stmt = stmt.where(Task.site_id == site_id)
    return list(db.scalars(stmt).all())
```

**Tenant context is injected via HTTP headers:**

```python
# Headers: X-Company-Id, X-Site-Id
@dataclass
class CompanyContext:
    company_id: int | None = None
    site_id: int | None = None
    is_global: bool = False
```

### 7.5 Database ERD

```mermaid
erDiagram
    companies {
        int id PK
        uuid uuid
        string name UK
        string status
        string license_type
        int max_sites
        int max_agents
        int max_users
        bool is_global
        bool enabled
    }

    sites {
        int id PK
        int company_id
        string name UK
        string code UK
        string address
        string city
        string country
        bool is_default
    }

    users {
        int id PK
        int company_id FK
        int site_id FK
        string email UK
        string password_hash
        string role
        bool enabled
    }

    projects {
        int id PK
        int company_id
        int site_id
        string name
        string description
        bool active
    }

    tasks {
        int id PK
        int company_id
        int site_id
        int project_id FK
        string title
        string description
        string status
        string priority
        datetime created_at
        datetime updated_at
    }

    remote_hosts {
        int id PK
        int company_id
        int site_id
        string name
        string hostname
        string connection_type
        int port
        bool enabled
        int credential_profile_id FK
    }

    credential_profiles {
        int id PK
        int company_id
        int site_id
        string name
        string authentication_type
        string username
        string password_encrypted
        string private_key_encrypted
    }

    playbooks {
        int id PK
        string name UK
        string version
        string category
        bool requires_approval
        int timeout_seconds
    }

    playbook_steps {
        int id PK
        int playbook_id FK
        string step_type
        string provider
        string command
        int step_order
    }

    playbook_executions {
        int id PK
        int playbook_id FK
        string status
        string mode
        string trigger_type
    }

    agents {
        int id PK
        string hostname
        string api_key UK
        string status
        datetime last_heartbeat
    }

    integration_profiles {
        int id PK
        int site_id FK
        string integration_type
        string encrypted_secret
    }

    companies ||--o{ sites : "has"
    companies ||--o{ users : "has"
    sites ||--o{ users : "has"
    projects ||--o{ tasks : "has"
    projects ||--o{ notes : "has"
    credential_profiles ||--o{ remote_hosts : "linked"
    playbooks ||--o{ playbook_steps : "contains"
    playbooks ||--o{ playbook_executions : "generates"
```

---

## 8. FastAPI

### 8.1 Application Entry Point

**File:** `backend/app/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.project_name,
    version="0.1.1",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all 26 routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
# ... 23 more routers


@app.get("/api/v1")
async def api_root() -> dict[str, str]:
    return {
        "name": settings.project_name,
        "status": "online",
        "environment": settings.environment,
        "version": "0.1.1",
    }
```

### 8.2 Middleware

The application uses minimal middleware:

| Middleware | Purpose |
|-----------|---------|
| `CORSMiddleware` | Cross-origin resource sharing for frontend |

Authentication is handled per-route via `Depends(get_current_user)`, not via middleware.

### 8.3 Error Handling

Errors are handled at the service layer via `HTTPException`:

```python
from fastapi import HTTPException, status

# Service layer raises exceptions
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Task not found",
)

raise HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Task already exists",
)
```

FastAPI automatically serializes these into the standard error response format:

```json
{
    "detail": "Task not found"
}
```

### 8.4 Validation

Validation happens at three levels:

1. **Pydantic schema validation** — Automatic request body validation via `TaskCreate`, `TaskUpdate`
2. **Service-level business validation** — Checks for existence, duplicates, constraints
3. **Repository-level data integrity** — Database constraints (unique, foreign key)

---

## 9. React Frontend

### 9.1 Application Bootstrap

**File:** `frontend/src/main.tsx`

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
        <App />
    </React.StrictMode>
);
```

**File:** `frontend/src/App.tsx`

```tsx
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { SidebarProvider } from "./contexts/SidebarContext";
import { ToastProvider } from "./contexts/ToastContext";
import AppLayout from "./layouts/AppLayout";
import LoginPage from "./pages/auth/LoginPage";
import DashboardPage from "./pages/DashboardPage";
// ... 60+ page imports

export default function App() {
    return (
        <BrowserRouter>
            <AuthProvider>
                <SidebarProvider>
                    <ToastProvider>
                        <Routes>
                            <Route path="/login" element={<LoginPage />} />
                            <Route element={<AppLayout />}>
                                <Route path="/" element={<DashboardPage />} />
                                <Route path="/tasks" element={<TasksPage />} />
                                {/* ... 60+ routes */}
                            </Route>
                        </Routes>
                    </ToastProvider>
                </SidebarProvider>
            </AuthProvider>
        </BrowserRouter>
    );
}
```

**Provider nesting order:**
```
BrowserRouter
  └── AuthProvider
       └── SidebarProvider
            └── ToastProvider
                 └── Routes
                      ├── /login → LoginPage (no layout)
                      └── AppLayout (sidebar + topbar + content + statusbar)
                           ├── / → DashboardPage
                           ├── /tasks → TasksPage
                           └── ...
```

### 9.2 Routing

Routes use `react-router-dom` v7 with `BrowserRouter` + `Routes` + `Route`:

```tsx
// Static routes
<Route path="/" element={<DashboardPage />} />
<Route path="/tasks" element={<TasksPage />} />

// Dynamic routes
<Route path="/companies/:id" element={<CompanyDetailPage />} />
<Route path="/automation/playbooks/:id" element={<PlaybookDetailPage />} />
<Route path="/agents/:id" element={<AgentDetailPage />} />

// Login route (outside layout)
<Route path="/login" element={<LoginPage />} />
```

**Route count:** 65+ routes across 12 functional domains.

### 9.3 Contexts

Three React Context providers manage cross-cutting state:

#### AuthContext

```tsx
// frontend/src/contexts/AuthContext.tsx
interface AuthState {
    token: string | null;
    user: UserInfo | null;
    loading: boolean;
}

interface AuthContextType extends AuthState {
    login: (email: string, password: string) => Promise<void>;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function useAuth(): AuthContextType {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error("useAuth must be used within AuthProvider");
    return ctx;
}

export function AuthProvider({ children }: { children: ReactNode }) {
    const [state, setState] = useState<AuthState>({
        token: getStoredToken(),
        user: getStoredUser(),
        loading: true,
    });

    const login = async (email: string, password: string) => {
        const result = await authApi.login(email, password);
        storeAuth(result.access_token, result.user);
        setState({ token: result.access_token, user: result.user, loading: false });
    };

    const logout = () => {
        clearAuth();
        setState({ token: null, user: null, loading: false });
    };

    return (
        <AuthContext.Provider value={{ ...state, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
}
```

#### SidebarContext

```tsx
// Manages sidebar collapse state, persists to localStorage
interface SidebarContextType {
    collapsed: boolean;
    toggle: () => void;
}
```

#### ToastContext

```tsx
// Manages toast notification array
interface ToastContextType {
    showToast: (message: string, type?: "success" | "error") => void;
}
```

**Context usage convention:**
- Always define a custom hook (`useAuth`, `useSidebar`, `useToast`)
- Custom hook throws if used outside its provider
- State is managed via `useState` — no external state libraries

### 9.4 Layouts

The main layout is a classic **sidebar + main content** shell:

```tsx
// frontend/src/layouts/AppLayout.tsx
export default function AppLayout() {
    return (
        <div className="app-layout">
            <Sidebar />
            <div className="app-main">
                <TopBar />
                <main className="app-content">
                    <Outlet />
                </main>
                <StatusBar />
            </div>
        </div>
    );
}
```

**Layout components:**

| Component | Location | Purpose |
|-----------|----------|---------|
| `AppLayout` | `layouts/AppLayout.tsx` | Main shell (sidebar + content area) |
| `Sidebar` | `layouts/Sidebar.tsx` | Collapsible navigation sidebar (260px → 56px) |
| `TopBar` | `layouts/TopBar.tsx` | Header with breadcrumb and search |
| `Breadcrumb` | `layouts/Breadcrumb.tsx` | Auto-generated from URL path |
| `StatusBar` | `layouts/StatusBar.tsx` | Bottom bar with connection status and clock |

### 9.5 Pages

Every page follows a consistent pattern:

```tsx
export default function SomePage() {
    // 1. State declarations
    const [data, setData] = useState<SomeType[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // 2. Data loading
    const loadData = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const result = await someApi.list();
            setData(result.items);
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : "Failed to load");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { loadData(); }, [loadData]);

    // 3. Render
    return (
        <>
            <PageHeader title="Some Page" subtitle="Description" actions={...} />
            <SearchInput value={search} onChange={setSearch} />
            {error && <div className="error-banner">{error}</div>}
            {loading ? (
                <div className="loading-bar" />
            ) : data.length === 0 ? (
                <EmptyState icon="📦" title="No items" description="..." />
            ) : (
                <DataTable columns={columns} data={filteredData} />
            )}
            {showModal && <SomeModal onSave={handleSave} onCancel={...} />}
        </>
    );
}
```

### 9.6 Components

**Common components (reusable across all pages):**

| Component | Location | Purpose |
|-----------|----------|---------|
| `PageHeader` | `components/common/PageHeader.tsx` | Title, subtitle, action buttons |
| `DataTable<T>` | `components/common/DataTable.tsx` | Generic typed table with column config |
| `StatusBadge` | `components/common/StatusBadge.tsx` | Colored status dot + label |
| `EmptyState` | `components/common/EmptyState.tsx` | Zero-data placeholder |
| `SearchInput` | `components/common/SearchInput.tsx` | Search input with clear button |
| `LoadingButton` | `components/common/LoadingButton.tsx` | Button with loading spinner |

**Dashboard components:**

| Component | Purpose |
|-----------|---------|
| `StatCard` | Metric stat card with optional link |
| `SystemGauges` | CPU/Memory/Disk gauge bars |
| `HealthBadges` | Health status badge row |
| `QuickActions` | Quick action shortcut buttons |
| `IntegrationsCard` | Integration status card |
| `HyperVCard` | Hyper-V dashboard summary |
| `ProxmoxCard` | Proxmox dashboard summary |
| `AICard` | AI operations summary |
| `AgentCard` | Agent summary |
| `AutomationCard` | Automation summary |
| `RecentCommands` | Recent command history |

### 9.7 Navigation

**File:** `frontend/src/config/navigation.ts`

Navigation is a static array of `NavGroup` objects:

```typescript
import { NavGroup } from "../types/navigation";

export const navigation: NavGroup[] = [
    {
        label: "Dashboard",
        icon: "📊",
        items: [{ label: "Overview", path: "/", icon: "🏠" }],
        defaultOpen: true,
    },
    {
        label: "Remote Operations",
        icon: "🔗",
        items: [
            { label: "Hosts", path: "/remote/hosts", icon: "🖥️" },
            { label: "Credentials", path: "/remote/credentials", icon: "🔑" },
            { label: "Console", path: "/remote/console", icon: "💻" },
            // ...
        ],
    },
    // ... 10 more groups
];
```

**Navigation types:**

```typescript
interface NavItem {
    label: string;
    path: string;
    icon: string;
    disabled?: boolean;
    badge?: string;
}

interface NavGroup {
    label: string;
    icon: string;
    items: NavItem[];
    defaultOpen?: boolean;
}
```

**12 navigation groups:**
1. Dashboard
2. Tenants (Companies)
3. Infrastructure
4. Remote Operations
5. Identity
6. Monitoring (Zabbix)
7. Hyper-V
8. Proxmox VE
9. AI Operations
10. Agents
11. Automation
12. Settings

### 9.8 Dashboard

The dashboard fetches all data in a **single API call** to `GET /api/v1/dashboard`:

```tsx
export default function DashboardPage() {
    const [data, setData] = useState<DashboardResponse | null>(null);

    useEffect(() => {
        dashboardApi.getDashboard().then(setData);
    }, []);

    return (
        <>
            <PageHeader title="Dashboard" subtitle="Infrastructure at a glance" />
            <div className="dashboard-grid">
                {/* Stat cards */}
                <StatCard label="Projects" value={data.projects.count} link="/projects" />
                <StatCard label="Tasks" value={data.tasks.count} link="/tasks" />
                <StatCard label="Containers" value={data.docker.container_count} link="/infrastructure/docker" />

                {/* Detail cards */}
                <SystemGauges system={data.system} />
                <HealthBadges health={data.health} />
                <IntegrationsCard integrations={data.integrations} />
                <HyperVCard />
                <ProxmoxCard />
                <AgentCard agents={data.agents} />
                <AutomationCard automation={data.automation} />
                <AICard ai={data.ai} />
            </div>
        </>
    );
}
```

### 9.9 Modals

Modals follow a consistent overlay pattern:

```tsx
interface ModalProps {
    onSave: () => void;
    onCancel: () => void;
    onError?: (message: string) => void;
    entity?: EntityType;  // Present = edit mode, absent = create mode
}

export default function SomeModal({ entity, onSave, onCancel, onError }: ModalProps) {
    const [loading, setLoading] = useState(false);
    const isEditing = entity !== undefined;

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        try {
            setLoading(true);
            if (isEditing) {
                await someApi.update(entity.id, formData);
            } else {
                await someApi.create(formData);
            }
            onSave();
        } catch (err) {
            onError?.(err instanceof Error ? err.message : "Operation failed");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="modal-overlay" onClick={onCancel}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <h3 className="modal-title">{isEditing ? "Edit" : "New"} Entity</h3>
                <form onSubmit={handleSubmit}>
                    {/* form fields */}
                    <div className="modal-actions">
                        <button className="btn btn-secondary" onClick={onCancel}>Cancel</button>
                        <LoadingButton type="submit" loading={loading}>Save</LoadingButton>
                    </div>
                </form>
            </div>
        </div>
    );
}
```

**Modal conventions:**
- Overlay click dismisses (`onClick={onCancel}`)
- Content click stopped (`e.stopPropagation()`)
- Edit/Create dual mode via optional `entity` prop
- Local loading state per modal
- Error callback to parent for toast display

### 9.10 API Client Pattern

All 14 API service files follow the same pattern:

```typescript
// frontend/src/services/remote.ts
const API = "/api/v1/remote";

async function handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
        const body = await response.json().catch(() => null);
        const detail = body?.detail;
        throw new Error(detail ?? `Request failed (${response.status})`);
    }
    if (response.status === 204) {
        return undefined as T;
    }
    return response.json();
}

export const remoteApi = {
    async listHosts(): Promise<HostListData> {
        const response = await fetch(`${API}/hosts`);
        return handleResponse<HostListData>(response);
    },

    async getHost(id: number): Promise<HostData> {
        const response = await fetch(`${API}/hosts/${id}`);
        return handleResponse<HostData>(response);
    },

    async createHost(data: HostCreateInput): Promise<HostData> {
        const response = await fetch(`${API}/hosts`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        return handleResponse<HostData>(response);
    },

    async updateHost(id: number, data: HostUpdateInput): Promise<HostData> {
        const response = await fetch(`${API}/hosts/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        return handleResponse<HostData>(response);
    },

    async deleteHost(id: number): Promise<void> {
        const response = await fetch(`${API}/hosts/${id}`, { method: "DELETE" });
        return handleResponse<void>(response);
    },
};
```

**Key characteristics:**
- Native `fetch` API — no axios or other HTTP client
- Base path `/api/v1/<domain>` — assumes nginx reverse proxy
- Types co-located with service file
- `handleResponse<T>` generic for type-safe responses
- Error extraction from FastAPI-style `{ detail: string }` responses

### 9.11 CSS and Styling

**File:** `frontend/src/styles.css` (4200+ lines)

The application uses a **single monolithic CSS file** with a dark theme:

```css
:root {
    --background: #0f172a;    /* slate-900 */
    --surface: #1e293b;       /* slate-800 */
    --border: #334155;        /* slate-700 */
    --primary: #3b82f6;       /* blue-500 */
    --success: #22c55e;       /* green-500 */
    --warning: #f59e0b;       /* amber-500 */
    --danger: #ef4444;        /* red-500 */
    --radius: 12px;
    --shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
}
```

**Styling conventions:**
- CSS custom properties for theming (dark theme only)
- BEM-like naming (not strict BEM)
- Responsive breakpoints at 1200px, 900px, 600px
- No CSS modules, styled-components, or CSS-in-JS
- No Tailwind utility classes (despite Tailwind being installed)
- Emoji used as icons throughout (no icon library)

---

## 10. Configuration

### 10.1 Environment Management

**File:** `.env.example` (template) and `.env` (actual, gitignored)

```bash
# Required
MISSIONCONTROL_SECRET_KEY=CHANGE_ME

# PostgreSQL
POSTGRES_DB=mission_control
POSTGRES_USER=mission_control
POSTGRES_PASSWORD=mission_control
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Backend
BACKEND_CORS_ORIGINS=http://localhost,http://localhost:3000,http://localhost:5173

# Optional: Remote Operations, AD, M365, Zabbix
```

**Generate a secret key:**

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 10.2 Settings Class

**File:** `backend/app/core/config.py`

```python
from functools import lru_cache
from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = Field(default="Mission Control", alias="PROJECT_NAME")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    missioncontrol_secret_key: str = Field(alias="MISSIONCONTROL_SECRET_KEY")

    postgres_db: str = Field(default="mission_control", alias="POSTGRES_DB")
    postgres_user: str = Field(default="mission_control", alias="POSTGRES_USER")
    postgres_password: str = Field(default="mission_control", alias="POSTGRES_PASSWORD")
    postgres_host: str = Field(default="postgres", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")

    redis_host: str = Field(default="redis", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")

    cors_origins: list[str] = Field(
        default=["http://localhost", "http://localhost:5173"],
        alias="BACKEND_CORS_ORIGINS",
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @computed_field
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @field_validator("missioncontrol_secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        from cryptography.fernet import Fernet
        try:
            Fernet(v.encode() if isinstance(v, str) else v)
        except Exception:
            raise ValueError(
                "MISSIONCONTROL_SECRET_KEY must be a valid Fernet key. "
                'Generate one with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
            )
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

**Key characteristics:**
- Uses `pydantic-settings` with `.env` file support
- `@lru_cache` for singleton pattern
- `@computed_field` for derived `database_url`
- `@field_validator` to ensure valid Fernet key at startup
- All env vars use uppercase `ALIAS` convention

### 10.3 Startup Sequence

The backend entrypoint (`entrypoint.sh`) executes in this order:

```
1. Wait for PostgreSQL (TCP + psycopg protocol check)
2. Wait for Redis (TCP + PING)
3. Validate configuration (Fernet key check)
4. Apply Alembic migrations (alembic upgrade head)
5. Run database seed (python -m app.seed.runner)
6. Start uvicorn (port 8000)
```

**Seed modules (idempotent):**

| Module | Data |
|--------|------|
| `sites.py` | Default site |
| `projects.py` | 4 sample projects |
| `tasks.py` | 8 sample tasks |
| `notes.py` | Sample notes |
| `automation.py` | 48 built-in playbooks (7 categories) |

---

## 11. Authentication and Authorization

### 11.1 Token-Based Auth

Mission Control uses a **custom lightweight JWT-like token** (HMAC-SHA256 signed):

```python
# backend/app/services/auth_service.py

def create_access_token(user_id, company_id, site_id, role, expires_minutes=480) -> str:
    header = _b64url_encode(b'{"alg":"HS256","typ":"MC"}')
    payload_data = {
        "sub": str(user_id),
        "cid": company_id,
        "sid": site_id,
        "role": role,
        "iat": now,
        "exp": expires_at,
    }
    payload = _b64url_encode(json.dumps(payload_data).encode())
    sig = _sign(f"{header}.{payload}", settings.missioncontrol_secret_key)
    return f"{header}.{payload}.{sig}"
```

**FastAPI dependency:**

```python
# backend/app/core/auth_dependency.py

async def get_current_user(
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
) -> User:
    # Extract "Bearer <token>" from Authorization header
    # Validate token signature and expiration
    # Look up user in database
    # Check user is enabled
    return user
```

**Usage in routes:**

```python
@router.get("/protected-endpoint")
async def protected(user: User = Depends(get_current_user)):
    return {"message": f"Hello {user.email}"}
```

### 11.2 Password Hashing

Passwords are hashed using **PBKDF2-SHA256** with 260,000 iterations and per-user random salt:

```python
def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        (salt + "mc_").encode(),
        iterations=260_000,
    )
    return f"{salt}${dk.hex()}"
```

### 11.3 Role-Based Access Control

Five role levels with hierarchical ordering:

```python
ROLE_HIERARCHY = {
    "global_admin": 5,
    "company_admin": 4,
    "site_admin": 3,
    "operator": 2,
    "readonly": 1,
}
```

### 11.4 Multi-Tenant Context

Tenant context is injected via HTTP headers:

```python
# Headers: X-Company-Id, X-Site-Id
@dataclass
class CompanyContext:
    company_id: int | None = None
    site_id: int | None = None
    is_global: bool = False

async def get_company_ctx(
    request: Request,
    x_company_id: str | None = Header(None, alias="X-Company-Id"),
    x_site_id: str | None = Header(None, alias="X-Site-Id"),
) -> CompanyContext:
    # Extract tenant context from headers
    return CompanyContext(...)
```

---

## 12. Security

### 12.1 Credential Encryption

All credential data is encrypted at rest using **Fernet symmetric encryption** (AES-128-CBC with HMAC-SHA256):

```python
# backend/app/core/security.py

class CredentialCipher:
    def __init__(self, secret_key: str) -> None:
        key_bytes = secret_key.encode() if isinstance(secret_key, str) else secret_key
        self._fernet = Fernet(key_bytes)

    def encrypt(self, plaintext: str) -> str:
        token = self._fernet.encrypt(plaintext.encode("utf-8"))
        return token.decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        plaintext = self._fernet.decrypt(ciphertext.encode("utf-8"))
        return plaintext.decode("utf-8")
```

**Encrypted fields:**

| Model | Fields |
|-------|--------|
| `CredentialProfile` | `password_encrypted`, `private_key_encrypted`, `passphrase_encrypted` |
| `IntegrationProfile` | `encrypted_secret`, `client_secret_encrypted` |

### 12.2 Secrets Management

| Practice | Detail |
|----------|--------|
| `.env` file | Gitignored, never committed |
| API responses | Sensitive fields excluded from Pydantic Response schemas |
| Docker Compose | `MISSIONCONTROL_SECRET_KEY` with `${:?...}` validation |
| Key rotation | Generate new key, update `.env`, re-encrypt credentials |

### 12.3 Security Best Practices

- Never commit secrets, API keys, or passwords to version control
- Use `CredentialCipher` for all credential storage
- Exclude sensitive fields from Pydantic Response schemas
- Validate Fernet key at application startup
- Use `Depends(get_current_user)` on protected endpoints
- Sanitize user input in service layer

---

## 13. REST APIs

### 13.1 API Standards

| Standard | Convention |
|----------|-----------|
| Base path | `/api/v1` |
| Content type | `application/json` |
| Authentication | `Authorization: Bearer <token>` header |
| Tenant isolation | `X-Company-Id`, `X-Site-Id` headers |
| Error format | `{ "detail": "Error message" }` |
| List format | `{ "count": int, "items": [...] }` |
| IDs | Integer primary keys |
| Timestamps | ISO 8601 format (`2026-07-16T12:00:00`) |

### 13.2 Endpoint Conventions

| Method | Path | Purpose | Status |
|--------|------|---------|--------|
| `GET` | `/entity` | List all | 200 |
| `GET` | `/entity/{id}` | Get by ID | 200 / 404 |
| `POST` | `/entity` | Create | 201 / 409 / 422 |
| `PUT` | `/entity/{id}` | Update | 200 / 404 / 422 |
| `DELETE` | `/entity/{id}` | Delete | 204 / 404 |

### 13.3 Response Formats

**Single entity:**

```json
{
    "id": 1,
    "project_id": 1,
    "title": "Wire dashboard to PostgreSQL",
    "description": null,
    "status": "pending",
    "priority": "medium",
    "created_at": "2026-07-08T13:00:00",
    "updated_at": "2026-07-08T13:00:00"
}
```

**List response:**

```json
{
    "count": 8,
    "items": [...]
}
```

**Error response:**

```json
{
    "detail": "Task not found"
}
```

### 13.4 API Reference

All 26 API routers:

| Router | Prefix | Tags |
|--------|--------|------|
| `health` | `/health` | Health |
| `version` | `/version` | Version |
| `status` | `/status` | Status |
| `doctor` | `/doctor` | Doctor |
| `docker` | `/docker` | Docker |
| `git` | `/git` | Git |
| `dashboard` | `/dashboard` | Dashboard |
| `projects` | `/projects` | Projects |
| `tasks` | `/tasks` | Tasks |
| `notes` | `/notes` | Notes |
| `resume` | `/resume` | Resume |
| `parking_lot` | `/parking-lot` | Parking Lot |
| `remote` | `/remote` | Remote Operations |
| `identity` | `/identity` | Identity |
| `integration` | `/integration` | Integration |
| `zabbix` | `/zabbix` | Zabbix |
| `hyperv` | `/hyperv` | Hyper-V |
| `proxmox` | `/proxmox` | Proxmox |
| `site` | `/site` | Sites |
| `ai` | `/ai` | AI |
| `agent` | `/agents` | Agents |
| `automation` | `/automation` | Automation |
| `company` | `/companies` | Companies |
| `auth` | `/auth` | Authentication |
| `agent_token` | `/agent-tokens` | Agent Tokens |

---

## 14. Logging

```python
import logging

logger = logging.getLogger(__name__)


class TaskService:
    async def get_all(self, db: Session) -> TaskListResponse:
        logger.info("Fetching all tasks")
        tasks = self._repository.get_all(db)
        items = [TaskResponse.model_validate(task) for task in tasks]
        return TaskListResponse(count=len(items), items=items)

    async def create(self, db: Session, data: TaskCreate) -> TaskResponse:
        logger.info("Creating task: %s", data.title)
        # ...
```

**Logging conventions:**
- Use `logging.getLogger(__name__)` at module level
- Log at INFO level for normal operations
- Log at ERROR level for failures
- Use `%s` formatting (lazy evaluation) for performance
- Never log sensitive data (passwords, keys, tokens)

---

## 15. Caching

### 15.1 Redis

Redis is used for health checks and caching:

```python
# backend/app/db/redis.py
import redis.asyncio as redis

async def check_redis_health(host: str, port: int) -> dict:
    try:
        r = redis.Redis(host=host, port=port, socket_timeout=3)
        await r.ping()
        return {"status": "healthy", "message": "Connected"}
    except Exception as e:
        return {"status": "unhealthy", "message": str(e)}
```

**Redis configuration:**

| Variable | Default | Purpose |
|----------|---------|---------|
| `REDIS_HOST` | `redis` | Redis server hostname |
| `REDIS_PORT` | `6379` | Redis server port |

---

## 16. Testing Strategy

### 16.1 Backend Testing (pytest)

**Configuration:** `backend/pytest.ini`

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
```

**Test inventory (32 files):**

| Category | Files | Coverage |
|----------|-------|----------|
| API Integration | `api/test_*.py` (7 files) | CRUD endpoints, auth, remote ops |
| Core Tests | `test_repositories.py`, `test_services.py` | Repository and service layers |
| Provider Tests | `test_proxmox.py`, `test_zabbix_provider.py`, `test_hyperv.py` | Provider abstraction |
| Security | `test_security.py`, `test_remote_service_encryption.py` | Fernet encryption |
| Automation | `test_automation.py`, `test_automation_extended.py` | Playbook system |
| AI | `test_ai.py` (~1400 lines) | AI subsystem engines |
| Remote | `test_bulk_execution.py`, `test_command_templates.py`, `test_scheduled_commands.py` | Remote operations |
| Agent | `test_agent_management.py` | Agent system |
| Auth | `test_auth_api.py`, `test_identity_providers.py` | Authentication |

### 16.2 Test Fixtures

**File:** `backend/tests/conftest.py`

```python
import os
from cryptography.fernet import Fernet
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.main import app


@pytest.fixture(autouse=True)
def mock_secret_key(monkeypatch):
    """Automatically set MISSIONCONTROL_SECRET_KEY for all tests."""
    test_key = Fernet.generate_key().decode()
    monkeypatch.setenv("MISSIONCONTROL_SECRET_KEY", test_key)
    get_settings.cache_clear()
    return test_key


@pytest.fixture
def db_session():
    """Provide an isolated in-memory database session."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    """Provide a FastAPI test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
```

**Database isolation strategy:** Each test gets a fresh in-memory SQLite database via `StaticPool` + `create_all`. This provides:
- Fast test execution
- No cross-test contamination
- No PostgreSQL dependency for tests

### 16.3 Writing Backend Tests

**Example test — API integration:**

```python
import pytest


class TestTaskAPI:
    def test_list_tasks(self, client, sample_project):
        response = client.get("/api/v1/tasks")
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "items" in data

    def test_create_task(self, client, sample_project):
        response = client.post(
            "/api/v1/tasks",
            json={
                "project_id": sample_project.id,
                "title": "New Task",
                "status": "pending",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Task"

    def test_create_task_missing_project(self, client):
        response = client.post(
            "/api/v1/tasks",
            json={"project_id": 999, "title": "Orphan Task"},
        )
        assert response.status_code == 404

    def test_get_task_not_found(self, client):
        response = client.get("/api/v1/tasks/999")
        assert response.status_code == 404
```

**Example test — Service layer:**

```python
import pytest
from app.services.task_service import TaskService


class TestTaskService:
    @pytest.mark.asyncio
    async def test_get_by_id_found(self, db_session, sample_project):
        from app.schemas.task import TaskCreate
        service = TaskService()
        created = await service.create(
            db_session,
            TaskCreate(project_id=sample_project.id, title="Test"),
        )
        result = await service.get_by_id(db_session, created.id)
        assert result.title == "Test"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, db_session):
        from fastapi import HTTPException
        service = TaskService()
        with pytest.raises(HTTPException) as exc_info:
            await service.get_by_id(db_session, 999)
        assert exc_info.value.status_code == 404
```

**Example test — Provider with mocking:**

```python
import pytest
from unittest.mock import AsyncMock, patch


class TestDockerProvider:
    @pytest.mark.asyncio
    async def test_get_docker_data_unavailable(self, monkeypatch):
        from app.providers.docker_provider import DockerProvider

        async def mock_raise():
            raise ConnectionError("Docker not running")

        monkeypatch.setattr(
            "app.providers.docker_provider.get_docker_provider",
            lambda: mock_raise,
        )

        provider = DockerProvider()
        result = await provider.get_docker_data()
        assert result["available"] is False
```

### 16.4 Frontend Testing

**Current status:** No frontend test suite exists. This is a known gap.

**Recommended approach for future implementation:**

| Tool | Purpose |
|------|---------|
| Vitest | Unit testing (fast, Vite-native) |
| React Testing Library | Component testing |
| MSW (Mock Service Worker) | API mocking |

### 16.5 Quality Gates

**Local quality gate:**

```powershell
# Run all pytest tests
cd backend
python -m pytest tests/ -v

# Run frontend lint
cd frontend
npm run lint

# Run frontend type check
cd frontend
npx tsc --noEmit

# Run full quality gate
./scripts/Invoke-Quality.ps1
```

---

## 17. CI/CD

### 17.1 GitHub Actions

**File:** `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  quality-gate:
    runs-on: windows-latest

    steps:
    - name: Checkout
      uses: actions/checkout@v4

    - name: Install PowerShell 7
      uses: actions/setup-powershell@v2
      with:
        powershell-version: 'latest'

    - name: Run Quality Gate
      shell: pwsh
      run: ./scripts/Invoke-Quality.ps1
```

### 17.2 Quality Gate Script

**File:** `scripts/Invoke-Quality.ps1`

Three-step process:
1. **Pester Tests** — Runs 5 test files (Bootstrap, Registry, Logger, Helpers, Validation)
2. **CLI Smoke Tests** — Runs `mc.ps1 help`, `version`, `status`, `doctor --output json`
3. **Formatting/Lint Check** — Placeholder (currently skipped)

### 17.3 Future CI/CD Improvements

| Improvement | Priority |
|-------------|----------|
| Add backend pytest to CI | High |
| Add frontend lint/typecheck to CI | High |
| Add Ruff linting to CI | Medium |
| Multi-platform CI (Linux + Windows) | Medium |
| Docker build verification | Medium |
| Code coverage reporting | Low |
| Deployment pipeline | Low |

---

## 18. Docker

### 18.1 Docker Compose Architecture

```mermaid
graph TB
    subgraph External["External"]
        Browser["Browser :80"]
    end

    subgraph Docker["Docker Compose (mc-net)"]
        Nginx["nginx:1.27-alpine :80"]
        Frontend["frontend (Node→Nginx) :3000"]
        Backend["backend (Python 3.12) :8000"]
        PostgreSQL["postgres:16-alpine :5432"]
        Redis["redis:7.2-alpine :6379"]
    end

    Browser --> Nginx
    Nginx --> Frontend
    Nginx --> Backend
    Backend --> PostgreSQL
    Backend --> Redis
```

### 18.2 Service Descriptions

| Service | Image | Ports | Health Check | Depends On |
|---------|-------|-------|-------------|-----------|
| `backend` | Python 3.12-slim | 8000 (internal) | HTTP `/api/v1/health/live` | postgres, redis |
| `frontend` | Multi-stage Node→Nginx | 3000 (internal) | None | backend |
| `nginx` | nginx:1.27-alpine | **80:80** (exposed) | wget spider | backend, frontend |
| `postgres` | postgres:16-alpine | 5432 (internal) | `pg_isready` | — |
| `redis` | redis:7.2-alpine | 6379 (internal) | `redis-cli ping` | — |

### 18.3 Backend Dockerfile

```dockerfile
FROM python:3.12-slim

# Create non-root user
RUN groupadd -r app && useradd -r -g app app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    openssh-client sshpass git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Entrypoint handles migration, seeding, and server start
ENTRYPOINT ["./entrypoint.sh"]
```

### 18.4 Frontend Dockerfile

```dockerfile
# Build stage
FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json .
RUN npm ci --ignore-scripts
COPY . .
RUN npm run build

# Production stage
FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 3000
```

### 18.5 Nginx Configuration

Nginx serves as the reverse proxy, routing:
- `/` → Frontend static files (port 3000)
- `/api/*` → Backend API (port 8000)

---

## 19. Debugging

### Backend Debugging

```bash
# View backend logs
docker compose logs -f backend

# Access API documentation
open http://localhost:8000/api/docs

# Run database queries
docker compose exec postgres psql -U mission_control -d mission_control

# Check Redis
docker compose exec redis redis-cli ping
```

### Frontend Debugging

```bash
# Start dev server with hot reload
cd frontend
npm run dev

# TypeScript type checking
npx tsc --noEmit

# ESLint
npm run lint
```

### Common Issues

| Issue | Solution |
|-------|----------|
| `MISSIONCONTROL_SECRET_KEY` error | Generate key: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| PostgreSQL connection refused | Ensure postgres container is healthy: `docker compose ps` |
| Redis connection refused | Ensure redis container is healthy: `docker compose ps` |
| Migration errors | Run `alembic stamp head` then `alembic upgrade head` |
| Frontend build fails | Run `npm ci` then `npm run build` |

---

## 20. Performance

### Backend Performance Considerations

- **Connection pooling:** SQLAlchemy engine uses `pool_size=10` and `max_overflow=20`
- **Async operations:** All I/O-bound operations (providers, services) use `async/await`
- **Database indexing:** Primary keys, foreign keys, and frequently queried columns are indexed
- **Lazy loading:** ORM relationships use `selectinload` for batch loading

### Frontend Performance Considerations

- **No code splitting:** All 65+ pages are eagerly imported (known technical debt)
- **No data caching:** API calls are fire-and-forget with no client-side cache
- **Monolithic CSS:** Single 4200+ line CSS file loaded upfront

### Future Performance Improvements

| Improvement | Priority |
|-------------|----------|
| React lazy loading / code splitting | High |
| API response caching (React Query/SWR) | High |
| CSS modularization | Medium |
| Connection pooling with idle cleanup | Medium |
| Database query optimization | Low |

---

## 21. Provider Development

### 21.1 How to Build a Provider

**Step 1: Define the abstract base class** (if creating a new domain)

```python
# backend/app/providers/mydomain/base_provider.py

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class MyResult:
    success: bool
    data: dict | None = None
    error: str | None = None


class MyDomainProvider(ABC):
    """Abstract base class for MyDomain providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    async def get_summary(self) -> dict: ...

    @abstractmethod
    async def test_connection(self) -> dict: ...
```

**Step 2: Implement the production provider**

```python
# backend/app/providers/mydomain/mydomain_provider.py

from app.providers.mydomain.base_provider import MyDomainProvider, MyResult


class ProductionMyDomainProvider(MyDomainProvider):
    @property
    def provider_name(self) -> str:
        return "mydomain"

    async def get_summary(self) -> dict:
        # Connect to external system, gather data
        return {"status": "connected", "items": 42}

    async def test_connection(self) -> dict:
        try:
            # Test connectivity
            return {"success": True, "message": "Connected"}
        except Exception as e:
            return {"success": False, "message": str(e)}
```

**Step 3: Implement a mock provider**

```python
# backend/app/providers/mydomain/mock_provider.py

from app.providers.mydomain.base_provider import MyDomainProvider


class MockMyDomainProvider(MyDomainProvider):
    @property
    def provider_name(self) -> str:
        return "mydomain_mock"

    async def get_summary(self) -> dict:
        return {"status": "mock", "items": 0}

    async def test_connection(self) -> dict:
        return {"success": False, "message": "Mock provider — not configured"}
```

**Step 4: Create the factory**

```python
# backend/app/providers/mydomain/provider_factory.py

from app.providers.mydomain.base_provider import MyDomainProvider
from app.providers.mydomain.mydomain_provider import ProductionMyDomainProvider
from app.providers.mydomain.mock_provider import MockMyDomainProvider

_provider: MyDomainProvider | None = None


def get_mydomain_provider() -> MyDomainProvider:
    global _provider
    if _provider is None:
        # Check if external system is configured
        if _is_mydomain_configured():
            _provider = ProductionMyDomainProvider()
        else:
            _provider = MockMyDomainProvider()
    return _provider
```

### 21.2 How to Build a Service

**Step 1: Create the service class**

```python
# backend/app/services/mydomain_service.py

import logging
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.mydomain_repository import MyDomainRepository
from app.schemas.mydomain import MyDomainCreate, MyDomainListResponse, MyDomainResponse, MyDomainUpdate

logger = logging.getLogger(__name__)


class MyDomainService:
    def __init__(self, repository: MyDomainRepository | None = None) -> None:
        self._repository = repository or MyDomainRepository()

    async def get_all(self, db: Session) -> MyDomainListResponse:
        items = self._repository.get_all(db)
        responses = [MyDomainResponse.model_validate(item) for item in items]
        return MyDomainListResponse(count=len(responses), items=responses)

    async def get_by_id(self, db: Session, item_id: int) -> MyDomainResponse:
        item = self._repository.get_by_id(db, item_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        return MyDomainResponse.model_validate(item)

    async def create(self, db: Session, data: MyDomainCreate) -> MyDomainResponse:
        item = self._repository.create(db, data)
        return MyDomainResponse.model_validate(item)

    async def update(self, db: Session, item_id: int, data: MyDomainUpdate) -> MyDomainResponse:
        item = self._repository.update(db, item_id, data)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        return MyDomainResponse.model_validate(item)

    async def delete(self, db: Session, item_id: int) -> None:
        deleted = self._repository.delete(db, item_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")


mydomain_service = MyDomainService()
```

**Step 2: Register the service in `__init__.py`** (if needed)

### 21.3 How to Build a Repository

```python
# backend/app/repositories/mydomain_repository.py

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db.mydomain import MyDomain
from app.schemas.mydomain import MyDomainCreate, MyDomainUpdate


class MyDomainRepository:
    @staticmethod
    def get_all(db: Session) -> list[MyDomain]:
        stmt = select(MyDomain).order_by(MyDomain.created_at.desc())
        return list(db.scalars(stmt).all())

    @staticmethod
    def get_by_id(db: Session, item_id: int) -> MyDomain | None:
        stmt = select(MyDomain).where(MyDomain.id == item_id)
        return db.scalar(stmt)

    @staticmethod
    def create(db: Session, data: MyDomainCreate) -> MyDomain:
        entity = MyDomain(**data.model_dump())
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def update(db: Session, item_id: int, data: MyDomainUpdate) -> MyDomain | None:
        entity = MyDomainRepository.get_by_id(db, item_id)
        if entity is None:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(entity, field, value)
        db.commit()
        db.refresh(entity)
        return entity

    @staticmethod
    def delete(db: Session, item_id: int) -> bool:
        entity = MyDomainRepository.get_by_id(db, item_id)
        if entity is None:
            return False
        db.delete(entity)
        db.commit()
        return True
```

### 21.4 How to Build a Router

```python
# backend/app/routers/mydomain.py

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.mydomain import MyDomainCreate, MyDomainListResponse, MyDomainResponse, MyDomainUpdate
from app.services.mydomain_service import MyDomainService, mydomain_service

router = APIRouter(prefix="/mydomain", tags=["MyDomain"])


def get_mydomain_service() -> MyDomainService:
    return mydomain_service


@router.get("", response_model=MyDomainListResponse)
async def list_items(
    db: Session = Depends(get_db),
    service: MyDomainService = Depends(get_mydomain_service),
) -> MyDomainListResponse:
    return await service.get_all(db)


@router.get("/{item_id}", response_model=MyDomainResponse)
async def get_item(
    item_id: int,
    db: Session = Depends(get_db),
    service: MyDomainService = Depends(get_mydomain_service),
) -> MyDomainResponse:
    return await service.get_by_id(db, item_id)


@router.post("", response_model=MyDomainResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    payload: MyDomainCreate,
    db: Session = Depends(get_db),
    service: MyDomainService = Depends(get_mydomain_service),
) -> MyDomainResponse:
    return await service.create(db, payload)


@router.put("/{item_id}", response_model=MyDomainResponse)
async def update_item(
    item_id: int,
    payload: MyDomainUpdate,
    db: Session = Depends(get_db),
    service: MyDomainService = Depends(get_mydomain_service),
) -> MyDomainResponse:
    return await service.update(db, item_id, payload)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    service: MyDomainService = Depends(get_mydomain_service),
) -> None:
    await service.delete(db, item_id)
```

**Then register in `main.py`:**

```python
from app.routers import mydomain
app.include_router(mydomain.router, prefix="/api/v1")
```

---

## 22. Frontend Development

### 22.1 How to Build Dashboard Widgets

**Step 1: Create the card component**

```tsx
// frontend/src/components/dashboard/MyDomainCard.tsx

import { Link } from "react-router-dom";

interface MyDomainCardProps {
    count: number;
    recent: Array<{ id: number; title: string }>;
}

export default function MyDomainCard({ count, recent }: MyDomainCardProps) {
    return (
        <div className="dashboard-card">
            <div className="card-header">
                <h3 className="card-title">📦 My Domain</h3>
                <Link to="/mydomain" className="card-link">View All</Link>
            </div>
            <div className="card-stat">
                <span className="stat-card-value">{count}</span>
                <span className="stat-card-label">Total Items</span>
            </div>
            <div className="card-list">
                {recent.map((item) => (
                    <div key={item.id} className="card-list-item">
                        {item.title}
                    </div>
                ))}
            </div>
        </div>
    );
}
```

**Step 2: Add to DashboardPage**

```tsx
// In DashboardPage.tsx
<MyDomainCard count={data.mydomain.count} recent={data.mydomain.recent} />
```

### 22.2 How to Add Navigation

**Step 1: Add items to the navigation config**

```typescript
// frontend/src/config/navigation.ts
{
    label: "My Domain",
    icon: "📦",
    items: [
        { label: "Overview", path: "/mydomain", icon: "📊" },
        { label: "Items", path: "/mydomain/items", icon: "📋" },
        { label: "Settings", path: "/mydomain/settings", icon: "⚙️" },
    ],
},
```

**Step 2: Add routes in App.tsx**

```tsx
<Route path="/mydomain" element={<MyDomainOverviewPage />} />
<Route path="/mydomain/items" element={<MyDomainItemsPage />} />
<Route path="/mydomain/settings" element={<MyDomainSettingsPage />} />
```

**Step 3: Add breadcrumb labels in Breadcrumb.tsx**

```typescript
const routeLabels: Record<string, string> = {
    mydomain: "My Domain",
    items: "Items",
    settings: "Settings",
};
```

### 22.3 How to Add Pages

**Step 1: Create the page component**

```tsx
// frontend/src/pages/mydomain/OverviewPage.tsx

import { useState, useEffect, useCallback } from "react";
import PageHeader from "../../components/common/PageHeader";
import DataTable from "../../components/common/DataTable";
import EmptyState from "../../components/common/EmptyState";
import { mydomainApi, MyDomainData } from "../../services/mydomain";

export default function MyDomainOverviewPage() {
    const [items, setItems] = useState<MyDomainData[]>([]);
    const [loading, setLoading] = useState(true);

    const loadData = useCallback(async () => {
        try {
            setLoading(true);
            const result = await mydomainApi.list();
            setItems(result.items);
        } catch (e: unknown) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { loadData(); }, [loadData]);

    const columns = [
        { key: "id", label: "ID" },
        { key: "title", label: "Title" },
        { key: "status", label: "Status" },
    ];

    return (
        <>
            <PageHeader
                title="My Domain"
                subtitle="Manage domain items"
                actions={<button className="btn btn-primary">New Item</button>}
            />
            {loading ? (
                <div className="loading-bar" />
            ) : items.length === 0 ? (
                <EmptyState icon="📦" title="No items" description="Create your first item." />
            ) : (
                <DataTable columns={columns} data={items} />
            )}
        </>
    );
}
```

### 22.4 How to Add Tests

**Backend tests (pytest):**

```python
# backend/tests/test_mydomain.py

import pytest


class TestMyDomainAPI:
    def test_list_items(self, client):
        response = client.get("/api/v1/mydomain")
        assert response.status_code == 200

    def test_create_item(self, client):
        response = client.post(
            "/api/v1/mydomain",
            json={"title": "Test Item", "status": "active"},
        )
        assert response.status_code == 201
        assert response.json()["title"] == "Test Item"

    def test_get_item_not_found(self, client):
        response = client.get("/api/v1/mydomain/999")
        assert response.status_code == 404
```

---

## 23. Mission Control Agent Development

> **Status:** Infrastructure defined, implementation in progress

The Agent system enables remote machines to register with Mission Control and receive commands.

**Architecture:**

```
Agent (remote machine) → Registers via token → Sends heartbeat → Receives commands
                                                                    ↓
                                                            Mission Control
                                                            (dispatches commands)
```

**Key models:**
- `Agent` — Registered agent instance with heartbeat, health, and inventory
- `AgentCommand` — Command dispatched to an agent with status tracking
- `AgentRegistrationToken` — One-time token for agent enrollment

**Agent registration flow:**

1. Admin creates registration token (`POST /api/v1/agent-tokens`)
2. Agent installs and calls registration endpoint with token
3. Agent begins sending heartbeats
4. Admin dispatches commands via Mission Control

---

## 24. Automation Engine Development

> **Status:** Fully implemented (Sprint 2.8)

The Automation Engine executes multi-step playbooks across different providers.

**Key concepts:**

| Concept | Description |
|---------|-------------|
| **Playbook** | Named automation definition with steps, variables, and configuration |
| **PlaybookStep** | Individual step with command, provider, and target host |
| **PlaybookVariable** | Named variables that can be referenced in steps |
| **PlaybookExecution** | Execution attempt with status, mode (live/dry-run), and results |
| **ExecutionLog** | Step-level log entries with stdout/stderr |
| **ApprovalWorkflow** | Approval configuration for sensitive playbooks |
| **EventTrigger** | Event-based playbook triggers |
| **PlaybookSchedule** | Cron-based scheduling |

**Execution flow:**

```mermaid
graph TD
    A[Playbook Triggered] --> B{Requires Approval?}
    B -->|Yes| C[Create ApprovalRequest]
    C --> D[Wait for Approval]
    D --> E{Approved?}
    E -->|No| F[Cancel Execution]
    E -->|Yes| G[Start Execution]
    B -->|No| G
    G --> H[Execute Step 1]
    H --> I{Step Success?}
    I -->|Yes| J[Execute Next Step]
    I -->|No| K{Continue on Failure?}
    K -->|Yes| J
    K -->|No| L{Auto Rollback?}
    L -->|Yes| M[Execute Rollback]
    L -->|No| N[Mark Execution Failed]
    M --> N
    J --> O{More Steps?}
    O -->|Yes| H
    O -->|No| P[Mark Execution Complete]
```

**Built-in providers (8):**

| Provider | Purpose |
|----------|---------|
| `bash` | Local bash execution |
| `powershell` | Local PowerShell execution |
| `http` | HTTP/REST API calls |
| `ssh` | Remote SSH command execution |
| `winrm` | Remote WinRM command execution |
| `agent` | Command dispatch to registered agents |
| `hyperv` | Hyper-V VM management commands |
| `proxmox` | Proxmox VE management commands |

**Built-in playbooks:** 48 playbooks across 7 categories (Windows, Linux, Docker, Zabbix, Remote, Hyper-V, M365, AD).

---

## 25. AI Operations Development

> **Status:** Engine implemented, integration in progress

The AI Operations subsystem provides intelligent analysis of infrastructure data.

**Engine components:**

| Component | Purpose |
|-----------|---------|
| `ConfidenceEngine` | Scores confidence of AI recommendations |
| `IncidentClassifier` | Classifies incidents by severity and type |
| `CorrelationEngine` | Identifies related events and alerts |
| `RecommendationEngine` | Generates actionable recommendations |
| `AIEngine` | Orchestrates all components |

**Supported AI providers (6):**

| Provider | Type |
|----------|------|
| `OllamaProvider` | Local LLM (Ollama) |
| `OpenAIProvider` | OpenAI API |
| `AzureOpenAIProvider` | Azure OpenAI |
| `AnthropicProvider` | Anthropic Claude |
| `LocalLLMProvider` | Local HTTP endpoint |
| `RuleBasedProvider` | Rule-based fallback (no LLM) |

**Provider selection:** The factory checks the `IntegrationProfile` for an `ai_provider` type, decrypts the API key, and returns the appropriate provider.

---

## 26. Plugin Development

> **Status:** Future roadmap (Sprint 3.0+)

### 26.1 Plugin SDK

The Plugin SDK will provide a Python-based framework for extending Mission Control:

```python
# Future plugin SDK interface
from mission_control_plugin import Plugin, PluginContext


class MyPlugin(Plugin):
    name = "my-plugin"
    version = "1.0.0"
    description = "My custom plugin"

    async def on_load(self, ctx: PluginContext) -> None:
        """Called when the plugin is loaded."""
        pass

    async def on_unload(self) -> None:
        """Called when the plugin is unloaded."""
        pass

    async def execute(self, params: dict) -> dict:
        """Execute a plugin command."""
        return {"result": "success"}
```

### 26.2 Plugin Manifest

```yaml
# plugin.yaml
name: my-plugin
version: 1.0.0
description: My custom plugin
author: Developer Name
entrypoint: my_plugin.main:MyPlugin
permissions:
  - read:database
  - execute:commands
  - access:credentials
```

### 26.3 Plugin Registration

Plugins will be registered via the Settings UI or API:

```bash
POST /api/v1/plugins/register
{
    "name": "my-plugin",
    "path": "/plugins/my-plugin"
}
```

### 26.4 Plugin Lifecycle

```
Install → Register → Load → Enable → Execute → Disable → Unload → Remove
```

### 26.5 Plugin Security

- Plugins run in a sandboxed environment
- Permission-based access control
- No direct database access (API only)
- Credential access requires explicit permission
- Plugin code is validated before loading

### 26.6 Plugin Examples

**Example: Custom Monitoring Plugin**

```python
class MonitoringPlugin(Plugin):
    name = "custom-monitoring"

    async def on_load(self, ctx: PluginContext):
        # Register custom health checks
        ctx.health_registry.register("my-service", self.check_health)

    async def check_health(self) -> dict:
        return {"status": "healthy", "message": "Service is running"}
```

---

## 27. Migration Guide

### Adding a New Entity

1. **Create ORM model** → `backend/app/models/db/{entity}.py`
2. **Register in models __init__** → `backend/app/models/db/__init__.py`
3. **Create Pydantic schemas** → `backend/app/schemas/{entity}.py`
4. **Create repository** → `backend/app/repositories/{entity}_repository.py`
5. **Create service** → `backend/app/services/{entity}_service.py`
6. **Create router** → `backend/app/routers/{entity}.py`
7. **Register router** → `backend/app/main.py`
8. **Create Alembic migration** → `alembic revision --autogenerate -m "add {entity}"`
9. **Create frontend service** → `frontend/src/services/{domain}.ts`
10. **Create frontend page** → `frontend/src/pages/{domain}/{Entity}Page.tsx`
11. **Add routes** → `frontend/src/App.tsx`
12. **Add navigation** → `frontend/src/config/navigation.ts`
13. **Write tests** → `backend/tests/test_{entity}.py`

---

## 28. Release Process

### 28.1 Versioning

Mission Control uses **semantic versioning** with a sprint-based release cycle:

```
MAJOR.MINOR.PATCH
│       │     │
│       │     └── Bug fixes, patches
│       └──────── Feature additions (sprint-based)
└──────────────── Breaking changes
```

**Current version:** `0.1.0` (VERSION file) / `0.1.1` (API)

### 28.2 Git Workflow

```bash
# Start new feature
git checkout develop
git pull origin develop
git checkout -b feature/my-feature

# Make changes, commit with conventional commits
git commit -m "feat: add mydomain CRUD endpoints"
git commit -m "fix: resolve dashboard loading issue"
git commit -m "docs: update developer guide"

# Push and create PR
git push origin feature/my-feature
# Open PR targeting develop
```

### 28.3 Branch Strategy

| Branch | Purpose | Merges Into |
|--------|---------|-------------|
| `main` | Production-ready code | — |
| `develop` | Integration branch | `main` |
| `feature/*` | Feature branches | `develop` |

### 28.4 Pull Requests

- Target `develop` branch
- Run quality gate before opening
- Update documentation if needed
- Keep PRs small and focused
- Address review feedback promptly

### 28.5 Code Reviews

**Review checklist:**
- [ ] Tests pass locally
- [ ] Quality gate passes
- [ ] No breaking changes to public APIs
- [ ] Documentation updated
- [ ] No duplicate code
- [ ] Follows existing patterns
- [ ] No secrets or sensitive data committed

---

## 29. Future Development Standards

### 29.1 Architecture Principles

| Principle | Description |
|-----------|-------------|
| **Modular Monolith** | Keep the monolith but maintain clean module boundaries |
| **Convention over Configuration** | Follow established patterns rather than creating new ones |
| **Layered Separation** | Routers → Services → Repositories → Models |
| **Strategy Pattern** | Use ABC + Factory for external system integrations |
| **Fail Gracefully** | Providers return `{"available": False}` instead of raising |
| **Encrypt at Rest** | All credentials and secrets encrypted via Fernet |
| **Multi-Tenant First** | Every entity should support `company_id` and `site_id` |
| **Idempotent Seeds** | Database seeders must be idempotent (check before insert) |

### 29.2 Future Kubernetes Deployment

> **Status:** Roadmap (Sprint 4.0+)

```mermaid
graph TB
    subgraph Kubernetes["Kubernetes Cluster"]
        Ingress["Ingress Controller"]
        FrontendSvc["Frontend Service"]
        BackendSvc["Backend Service"]
        PostgreSQL["PostgreSQL (StatefulSet)"]
        Redis["Redis (Deployment)"]
    end

    Ingress --> FrontendSvc
    Ingress --> BackendSvc
    BackendSvc --> PostgreSQL
    BackendSvc --> Redis
```

**Planned Kubernetes resources:**
- `Deployment` for frontend and backend
- `StatefulSet` for PostgreSQL
- `Deployment` for Redis
- `Service` for internal communication
- `Ingress` for external access
- `ConfigMap` and `Secret` for configuration
- `PersistentVolumeClaim` for database storage

---

## 30. Appendices

### 30.1 Directory Structure

```text
MissionControl/
├── .github/workflows/ci.yml
├── backend/
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   ├── app/
│   │   ├── main.py
│   │   ├── ai/
│   │   ├── core/
│   │   ├── db/
│   │   ├── infrastructure/
│   │   ├── models/db/
│   │   ├── platform/
│   │   ├── providers/
│   │   │   ├── automation/
│   │   │   ├── hyperv/
│   │   │   ├── identity/
│   │   │   ├── proxmox/
│   │   │   ├── remote/
│   │   │   ├── virtualization/
│   │   │   └── zabbix/
│   │   ├── repositories/
│   │   ├── routers/
│   │   ├── schemas/
│   │   ├── seed/
│   │   ├── services/
│   │   ├── storage/
│   │   └── utils/
│   ├── tests/
│   │   ├── api/
│   │   └── conftest.py
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── pyproject.toml
│   ├── pytest.ini
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── styles.css
│   │   ├── components/
│   │   ├── config/
│   │   ├── contexts/
│   │   ├── hooks/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── services/
│   │   └── types/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
├── nginx/
│   └── default.conf
├── scripts/
│   ├── mc.ps1
│   ├── Invoke-Quality.ps1
│   ├── lib/
│   └── commands/
├── tests/
│   ├── TestHelpers.ps1
│   └── *.Tests.ps1
├── docker-compose.yml
├── .env.example
├── CONTRIBUTING.md
├── CHANGELOG.md
├── README.md
└── VERSION
```

### 30.2 Glossary

| Term | Definition |
|------|-----------|
| **Provider** | A class that encapsulates interaction with an external system |
| **Repository** | A class with static methods for data access |
| **Service** | A class containing business logic between router and repository |
| **Router** | A FastAPI APIRouter that defines HTTP endpoints |
| **Schema** | A Pydantic model for request/response validation |
| **Model** | A SQLAlchemy ORM class mapping to a database table |
| **Factory** | A function that returns cached singleton instances of providers |
| **Playbook** | An automation definition with ordered steps |
| **Step** | A single unit of work within a playbook |
| **Agent** | A remote machine registered with Mission Control |
| **Credential** | An encrypted authentication credential (password, SSH key) |
| **Tenant** | A company and its associated sites |
| **Dashboard** | The main overview page aggregating all system data |
| **Quality Gate** | Automated checks run before merging (tests, lint, build) |

### 30.3 Useful Commands

**Docker:**

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f backend

# Rebuild from scratch
docker compose down -v
docker compose build --no-cache
docker compose up -d

# Access PostgreSQL
docker compose exec postgres psql -U mission_control -d mission_control

# Access Redis CLI
docker compose exec redis redis-cli
```

**Backend:**

```bash
# Start dev server
cd backend
uvicorn app.main:app --reload --port 8000

# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_task_api.py -v

# Run with coverage
python -m pytest tests/ --cov=app

# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Seed database
python -m app.seed.runner
```

**Frontend:**

```bash
# Start dev server
cd frontend
npm run dev

# Build for production
npm run build

# Run lint
npm run lint

# Type check
npx tsc --noEmit
```

**Quality Gate:**

```powershell
# Run full quality gate
./scripts/Invoke-Quality.ps1

# Run Pester tests
Invoke-Pester -Path tests/

# Verify environment
./scripts/verify.ps1
```

---

> **Document Version:** 1.0
> **Last Updated:** July 16, 2026
> **Maintainer:** Mission Control Development Team
