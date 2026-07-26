# Mission Control Community Edition v1.0.0

**Release Date:** December 1, 2024

---

## Overview

Mission Control Community Edition v1.0.0 is the first public release of the Mission Control platform. This release provides the core infrastructure for managing remote agents, executing commands, and monitoring system health from a unified web dashboard.

This release establishes the foundation on which all subsequent versions are built. It is a Community Edition release under the AGPL-3.0 license, free for individuals and organizations.

---

## Key Features

### Agent Management

- Register and manage remote agents from the web UI
- Heartbeat-driven health monitoring with configurable intervals
- Real-time agent status (online, offline, degraded)
- Agent metadata: hostname, OS, IP address, uptime, resource usage
- Agent groups for organization

### Remote Command Execution

- Execute shell commands on any connected agent from the browser
- Real-time command output streaming
- Command history with search and filtering
- Operator identity and timestamp on every command

### Basic Inventory

- Automatic system information collection on agent registration
- Operating system details, CPU, memory, and disk usage
- Agent version and configuration summary

### Web Dashboard

- Single-page application for infrastructure overview
- Agent status overview with summary counts
- Command history view
- Basic filtering and search

### User Management

- Admin-created user accounts
- Password authentication
- Basic role differentiation (admin vs. standard user)

### REST API

- RESTful API for all core operations
- Agent registration, status reporting, and command execution endpoints
- API key authentication for programmatic access
- Interactive Swagger documentation at `/docs`

### Infrastructure

- Docker Compose setup for local development and deployment
- PostgreSQL 12 for data storage
- Redis 6 for caching and task queuing
- Configurable logging levels

---

## Installation

### Docker Compose (Recommended)

```bash
git clone https://github.com/billboe3-png/MissionControl.git
cd MissionControl
git checkout v1.0.0
docker compose up -d
```

Open **http://localhost:8000** in your browser. Default admin credentials are printed to the server logs on first startup.

### Manual Installation

Requirements: Python 3.12, PostgreSQL 12+, Redis 6+, Node.js 18+.

```bash
git clone https://github.com/billboe3-png/MissionControl.git
cd MissionControl
git checkout v1.0.0
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your database and Redis credentials
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Agent Installation

```bash
# On the remote machine
pip install mission-control-agent
mission-control-agent register --server https://your-server:8000 --token YOUR_API_KEY
```

---

## Known Issues

The following issues are known and will be addressed in future releases:

- **Agent reconnection delay** — When a network interruption occurs, agents may take up to 60 seconds to reconnect. A configurable reconnection interval is planned for v1.1.0.
- **Command output truncation** — Very long command outputs (over 1 MB) may be truncated in the web UI. Full output is available via the API.
- **No playbook support** — The visual playbook editor and automation engine are not yet available. These are the primary focus for v2.0.0.
- **Single-server only** — No clustering or high-availability support in this release.
- **Browser compatibility** — Tested on Chrome 120+ and Firefox 120+. Safari and Edge may have minor UI inconsistencies.
- **No RBAC** — Only two roles (admin, standard user) are available. Fine-grained permissions are planned for v2.0.0.

See [CHANGELOG.md](CHANGELOG.md) for the full list of known issues and fixes in subsequent releases.

---

## Upgrade Guide

This is the initial release, so no upgrade path from a previous version exists. If you are migrating from an earlier pre-release or development build:

1. Back up your existing database.
2. Pull the v1.0.0 release tag.
3. Run database migrations: `alembic upgrade head`.
4. Update your `.env` file if configuration keys have changed (see commit history).
5. Restart the server.

---

## Breaking Changes

As this is the initial public release, there are no prior versions with compatibility guarantees. However, the following pre-release conventions have been formalized in v1.0.0:

- API endpoints are now versioned under `/api/v1/`.
- Agent registration requires a server-generated API key (previously accepted any token string).
- Configuration file location moved to `.env` (previously inline in `config.py`).
- Default database port changed from 5432 to the standard 5432 (no change for most deployments).

---

## Acknowledgments

Mission Control v1.0.0 would not be possible without the contributions and support of:

- **Bill Boe** — Project creator and lead developer
- **Community contributors** — Everyone who reported issues, submitted PRs, and provided feedback during the pre-release development cycle
- **Open source dependencies** — FastAPI, SQLAlchemy, Pydantic, React, Vite, and the entire Python and JavaScript ecosystems that Mission Control builds upon
- **Early adopters** — Organizations and individuals who tested pre-release versions in their environments and provided invaluable real-world feedback

---

## What's Next

See the [Roadmap](ROADMAP.md) for details on upcoming releases. The v2.0.0 release will introduce the playbook engine, advanced RBAC, and the rewritten agent protocol.

See the [Changelog](CHANGELOG.md) for detailed changes in each release.

---

## Links

| Resource | URL |
|----------|-----|
| Repository | https://github.com/billboe3-png/MissionControl |
| Documentation | https://github.com/billboe3-png/MissionControl/tree/main/docs |
| Issues | https://github.com/billboe3-png/MissionControl/issues |
| Discussions | https://github.com/billboe3-png/MissionControl/discussions |
| Security Policy | [SECURITY.md](SECURITY.md) |
| Contributing | [CONTRIBUTING.md](CONTRIBUTING.md) |
