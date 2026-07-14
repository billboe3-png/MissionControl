# Mission Control

Mission Control is a personal productivity platform for senior IT professionals.

## Vision

One dashboard.

One workflow.

One place to manage everything.

## What is Mission Control?

Mission Control is a developer productivity CLI and dashboard platform designed for senior IT professionals. It provides a unified interface for managing development environments, Docker containers, Git workflows, and project health checks through a single PowerShell-based command-line interface.

## Current Project Status

**Sprint 3** - Developer Experience Foundation

- ✅ CLI framework with command registry
- ✅ Docker Compose integration
- ✅ Git workflow helpers
- ✅ Health check system (doctor)
- ✅ Pester test framework
- ✅ CI quality gate with GitHub Actions
- ✅ VS Code workspace configuration

# Mission Control Backend v1.0

## Release Highlights

### Core Platform
- FastAPI backend
- PostgreSQL persistence
- SQLAlchemy ORM
- Alembic migrations

### APIs
- Project CRUD
- Task CRUD
- Note CRUD
- Dashboard API
- Resume API foundation

### Architecture
- Repository pattern
- Service layer
- Pydantic schemas
- Dependency injection
- Structured logging

### Database
- Idempotent seed framework
- Production-ready migrations
- PostgreSQL support

### Dashboard
- Live statistics
- Project statistics
- Task statistics
- Docker integration foundation

### Testing
- 65 automated tests
- CRUD integration tests
- Dashboard integration tests
- Repository tests
- Service tests
- Seeder tests

Status: Stable

## High-Level Architecture

Mission Control follows a modular PowerShell-based architecture:

- **CLI Entry Point** (`mc.ps1`) - Main script that bootstraps the framework
- **Bootstrap** - Parses arguments and creates execution context
- **Registry** - Command registration and dispatch system
- **Commands** - Individual command modules (doctor, docker, git, etc.)
- **Libraries** - Shared utilities (validation, logging, output, config)
- **Output Engine** - Unified rendering for console, JSON, and pretty JSON

For detailed architecture documentation, see [docs/architecture.md](docs/architecture.md).

## Prerequisites

- **PowerShell 7+** - Required for CLI execution
- **Docker Desktop** - Required for Docker Compose stack
- **Git** - Required for version control operations
- **Python** - Required for backend development
- **Node.js** - Required for frontend development

## Quick Start

Clone the repository and run the doctor check to verify your environment:

```bash
git clone <repository>
cd MissionControl
./scripts/mc.ps1 doctor
```

Start the Docker stack:

```bash
./scripts/mc.ps1 docker up
```

Check your environment status:

```bash
./scripts/mc.ps1 status
```

## Security Setup

Mission Control requires a Fernet secret key to encrypt credential profiles (SSH keys, passwords, WinRM credentials). The backend will not start without a valid key.

### Generating a Secret Key

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Or via Docker:

```bash
docker compose run --rm backend python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Adding to .env

Copy the generated key into your `.env` file:

```env
MISSIONCONTROL_SECRET_KEY=your-generated-key-here
```

Never commit a real key to version control.

## Docker Setup

### Prerequisites

- Docker Desktop or Docker Engine with Compose V2
- A valid `MISSIONCONTROL_SECRET_KEY` in your `.env` file

### Starting the Stack

```bash
docker compose up -d
```

On first start, the backend entrypoint will:
1. Validate `MISSIONCONTROL_SECRET_KEY` is present and valid
2. Run Alembic migrations
3. Seed the database
4. Start the API server

If the key is missing, the container exits with a clear error message before attempting migrations.

### Stopping the Stack

```bash
docker compose down
```

### Rebuilding

```bash
docker compose build --no-cache backend
docker compose up -d
```

## Environment Variables

All configuration is managed through the `.env` file at the project root.

| Variable | Required | Default | Description |
|---|---|---|---|
| `MISSIONCONTROL_SECRET_KEY` | **Yes** | — | Fernet key for credential encryption |
| `PROJECT_NAME` | No | `Mission Control` | Application display name |
| `ENVIRONMENT` | No | `development` | Runtime environment |
| `POSTGRES_DB` | No | `mission_control` | PostgreSQL database name |
| `POSTGRES_USER` | No | `mission_control` | PostgreSQL user |
| `POSTGRES_PASSWORD` | No | `mission_control` | PostgreSQL password |
| `POSTGRES_HOST` | No | `postgres` | PostgreSQL host (use `localhost` outside Docker) |
| `POSTGRES_PORT` | No | `5432` | PostgreSQL port |
| `REDIS_HOST` | No | `redis` | Redis host |
| `REDIS_PORT` | No | `6379` | Redis port |
| `BACKEND_CORS_ORIGINS` | No | `http://localhost,http://localhost:3000,http://localhost:5173` | Comma-separated allowed origins |
| `COMPOSE_PROJECT_NAME` | No | `missioncontrol` | Docker Compose project name |
| `SSH_CONNECT_TIMEOUT` | No | `10` | SSH connection timeout (seconds) |
| `SSH_COMMAND_TIMEOUT` | No | `60` | SSH command timeout (seconds) |
| `WINRM_CONNECT_TIMEOUT` | No | `10` | WinRM connection timeout (seconds) |
| `WINRM_OPERATION_TIMEOUT` | No | `60` | WinRM operation timeout (seconds) |
| `REMOTE_RETRY_COUNT` | No | `1` | Retries for transient remote failures |

### Copying .env.example

```bash
cp .env.example .env
```

Then generate and set your secret key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Secret Rotation

To rotate the encryption key:

1. Generate a new key:
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

2. Update `MISSIONCONTROL_SECRET_KEY` in `.env` with the new key.

3. Re-encrypt existing credentials. The system supports key versioning (`key_version` column on credential profiles). Existing encrypted values encrypted with the old key will need to be re-encrypted. For development, recreate credential profiles. For production, run a migration script.

4. Restart the stack:
   ```bash
   docker compose restart backend
   ```

> **Note:** The old key cannot decrypt credentials encrypted with the new key. Rotate during a maintenance window.

## CLI Commands

### help

**Description:** Shows help for CLI commands

**Example:**
```bash
./scripts/mc.ps1 help
./scripts/mc.ps1 help doctor
```

**Purpose:** Displays available commands, usage information, and examples for all CLI commands.

### doctor

**Description:** Checks local tools, repository state, Docker services, and backend endpoints

**Example:**
```bash
./scripts/mc.ps1 doctor
./scripts/mc.ps1 doctor --output json
./scripts/mc.ps1 doctor --output json-pretty
```

**Purpose:** Performs comprehensive health checks on your development environment including tool availability, Docker status, and backend connectivity.

### docker

**Description:** Manages the Mission Control Docker Compose stack

**Example:**
```bash
./scripts/mc.ps1 docker up
./scripts/mc.ps1 docker down
./scripts/mc.ps1 docker logs
```

**Purpose:** Controls the Docker Compose stack for backend, frontend, PostgreSQL, Redis, and Nginx services.

### git

**Description:** Provides safe wrappers around common Git commands

**Example:**
```bash
./scripts/mc.ps1 git status
./scripts/mc.ps1 git commit "fix: resolve doctor null message issue"
```

**Purpose:** Simplifies common Git operations with validation and safety checks.

### status

**Description:** Shows local developer environment status

**Example:**
```bash
./scripts/mc.ps1 status
```

**Purpose:** Displays current environment configuration including PowerShell version, .env status, Docker Compose availability, and Git status.

### version

**Description:** Shows CLI version

**Example:**
```bash
./scripts/mc.ps1 version
```

**Purpose:** Displays the current Mission Control CLI version.

### init

**Description:** Performs idempotent project initialization

**Example:**
```bash
./scripts/mc.ps1 init
```

**Purpose:** Creates required project files and directories including .env from .env.example and developer folders.

### Reserved Commands

The following commands are reserved for future sprints:

- **build** - Builds the project
- **clean** - Cleans build artifacts
- **dev** - Starts development environment
- **lint** - Runs linting
- **sprint** - Manages sprints
- **test** - Runs tests

## Repository Layout

```
MissionControl/
├── backend/           # Backend API (FastAPI/Python)
├── frontend/          # Frontend dashboard (React)
├── docker/            # Docker Compose configuration
├── scripts/           # CLI framework and commands
│   ├── mc.ps1        # Main CLI entry point
│   ├── lib/          # Shared libraries
│   │   ├── Bootstrap.ps1
│   │   ├── Registry.ps1
│   │   ├── Config.ps1
│   │   ├── Validation.ps1
│   │   ├── Logger.ps1
│   │   ├── Output.ps1
│   │   ├── Doctor.ps1
│   │   ├── Docker.ps1
│   │   ├── Git.ps1
│   │   └── Helpers.ps1
│   ├── commands/     # Command modules
│   │   ├── Help.ps1
│   │   ├── Doctor.ps1
│   │   ├── Docker.ps1
│   │   ├── Git.ps1
│   │   ├── Status.ps1
│   │   ├── Version.ps1
│   │   └── Project.ps1
│   └── Invoke-Quality.ps1  # CI quality gate script
├── tests/             # Pester test suite
│   ├── Bootstrap.Tests.ps1
│   ├── Registry.Tests.ps1
│   ├── Logger.Tests.ps1
│   ├── Helpers.Tests.ps1
│   ├── Validation.Tests.ps1
│   └── TestHelpers.ps1
├── docs/              # Documentation
│   └── architecture.md
├── .github/           # GitHub Actions workflows
│   └── workflows/
│       └── ci.yml
├── .vscode/           # VS Code workspace configuration
│   ├── extensions.json
│   ├── settings.json
│   ├── tasks.json
│   └── launch.json
├── README.md
├── CONTRIBUTING.md
└── LICENSE
```

## Development Workflow

### Seeding the Database

Database seeding runs automatically when the backend container starts via `entrypoint.sh`.

To run the seed manually:

```bash
cd backend
python -m app.seed.runner
```

From inside the backend container:

```bash
docker compose exec backend python -m app.seed.runner
```

The seed runner is idempotent — each entity module seeds only when its table is empty. Running it multiple times will not create duplicates.

Production baseline after a fresh `docker compose up`:

- Projects: 4
- Tasks: 8
- Notes: 0
- Resume: 0

Verify seeded data on the dashboard:

```bash
curl http://localhost/api/v1/dashboard
```

### Running Tests Locally

Use Pester to run the test suite:

```powershell
Invoke-Pester
```

Tests are located in the `tests/` directory and cover Bootstrap, Registry, Logger, Helpers, and Validation modules.

### Running the Quality Gate Locally

Run the quality gate script before pushing:

```powershell
./scripts/Invoke-Quality.ps1
```

This script:
1. Runs all Pester tests
2. Executes CLI smoke tests (help, version, status, doctor)
3. Checks formatting/lint (placeholder for future implementation)

**Run this before pushing** - it's the same check that CI runs on every push and pull request.

## Continuous Integration

Mission Control uses GitHub Actions for continuous integration:

### Push Validation

Every push to `main` or `master` branches triggers the CI workflow which:
- Checks out the code
- Installs PowerShell 7
- Runs the quality gate script

### Pull Request Validation

Every pull request to `main` or `master` branches triggers the same CI workflow to ensure code quality before merging.

The CI workflow is defined in `.github/workflows/ci.yml`.

## Roadmap

### Sprint 1 - Foundation
- CLI framework architecture
- Command registry system
- Basic output rendering
- Docker Compose integration
- Git workflow helpers

### Sprint 2 - Health & Monitoring
- Doctor command with environment checks
- Docker service health monitoring
- Backend HTTP endpoint checks
- Logging infrastructure

### Sprint 3 - Developer Experience
- Pester test framework
- CI quality gate with GitHub Actions
- VS Code workspace configuration
- Developer documentation

### Sprint 4 - Dashboard & Frontend
- Dashboard API endpoints
- React frontend application
- Authentication system
- Widget infrastructure

## Planned Modules

- Dashboard
- Tasks
- Projects
- Notes
- Focus Mode
- Resume Me
- Parking Lot
- Microsoft 365
- Google Workspace
- Ticket System
- Zabbix
- AI Assistant

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on contributing to Mission Control.

## License

See [LICENSE](LICENSE) for license information.

