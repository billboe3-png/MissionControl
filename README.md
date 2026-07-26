<p align="center">
  <img src="docs/assets/mission-control-logo.png" alt="Mission Control Logo" width="200"/>
</p>

<h1 align="center">Mission Control</h1>

<p align="center">
  <strong>Enterprise-grade infrastructure automation and remote operations platform</strong>
</p>

<p align="center">
  <a href="https://github.com/billboe3-png/MissionControl/actions"><img src="https://img.shields.io/github/actions/workflow/status/billboe3-png/MissionControl/ci.yml?branch=main&style=flat-square&label=CI" alt="CI Status"></a>
  <a href="https://github.com/billboe3-png/MissionControl/blob/main/LICENSE"><img src="https://img.shields.io/github/license/billboe3-png/MissionControl?style=flat-square" alt="License"></a>
  <a href="https://github.com/billboe3-png/MissionControl/releases"><img src="https://img.shields.io/github/v/release/billboe3-png/MissionControl?style=flat-square" alt="Release"></a>
  <a href="https://github.com/billboe3-png/MissionControl/issues"><img src="https://img.shields.io/github/issues/billboe3-png/MissionControl?style=flat-square" alt="Issues"></a>
  <img src="https://img.shields.io/badge/version-3.0.0-blue?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/python-3.12-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.12">
  <img src="https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black" alt="React">
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#features">Features</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#deployment">Deployment</a> •
  <a href="#documentation">Documentation</a> •
  <a href="#contributing">Contributing</a>
</p>

---

## Screenshots

<!-- Add screenshots to docs/screenshots/ and reference them here -->

| Dashboard | Agent Management | Playbook Editor |
|-----------|-----------------|-----------------|
| ![Dashboard](docs/screenshots/dashboard.png) | ![Agents](docs/screenshots/agents.png) | ![Playbooks](docs/screenshots/playbooks.png) |

| Inventory | AI Operations | Remote Terminal |
|-----------|--------------|-----------------|
| ![Inventory](docs/screenshots/inventory.png) | ![AI Ops](docs/screenshots/ai-ops.png) | ![Terminal](docs/screenshots/terminal.png) |

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/billboe3-png/MissionControl.git
cd MissionControl
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
```

### 2. Configure and migrate

```bash
cp .env.example .env
# Edit .env with your PostgreSQL and Redis connection strings
alembic upgrade head
```

### 3. Run

```bash
# Terminal 1 — API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — Frontend
cd frontend && npm install && npm run dev
```

Open **http://localhost:5173** in your browser. The default admin credentials are printed on first startup.

> **Prefer Docker?** See the [deployment guide](#deployment) for a one-command `docker compose up` setup.

---

## Features

### Agent Management
- Heartbeat-driven agent monitoring with automatic reconnection
- Real-time status, system metrics, and health dashboards
- Remote command execution and file transfer
- Group-based agent organization

### Automation & Playbooks
- Visual playbook editor with drag-and-drop workflow design
- Step types: commands, scripts, conditions, loops, parallel execution
- Scheduled and event-triggered playbook runs
- Rollback and error-handling primitives

### AI Operations
- Natural-language task generation from prompts
- Anomaly detection across agent telemetry
- Automated remediation suggestions
- LLM-powered log analysis and summarization

### Remote Operations
- Web-based terminal sessions (SSH-style)
- Live log streaming from agents
- Bulk operations across agent groups
- Session recording and audit trail

### Inventory
- Automatic system discovery and classification
- Software, hardware, and network inventory
- Custom attribute tagging and filtering
- Change tracking with diff views

### Plugin System
- Python-based plugin SDK
- Community plugin marketplace
- Custom UI panels and dashboard widgets
- Event hooks for full lifecycle integration

### Multi-Tenancy
- Organization and workspace isolation
- Role-based access control (RBAC)
- SSO / SAML integration (Enterprise)
- Audit logging across all tenants

---

## Architecture

Mission Control follows a **Server + Agent** architecture:

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (React)                  │
│              Vite · TypeScript · Tailwind            │
└───────────────────────┬─────────────────────────────┘
                        │ REST + WebSocket
┌───────────────────────▼─────────────────────────────┐
│               API Server (FastAPI)                   │
│   286 endpoints · 25 routers · SQLAlchemy 2.0        │
│   PostgreSQL 16  ·  Redis 7  ·  Alembic migrations  │
└───────────────────────┬─────────────────────────────┘
                        │ Agent Protocol (heartbeat)
┌───────────────────────▼─────────────────────────────┐
│                    Agent (Python)                    │
│       Python 3.12 · zero external dependencies      │
│  Config: ~/.config/mission-control-agent/config.yaml│
└─────────────────────────────────────────────────────┘
```

- **Server**: Handles authentication, orchestration, scheduling, plugin management, and the REST/WebSocket API.
- **Agent**: Lightweight Python process deployed on managed nodes. Communicates with the server via heartbeat polling and command execution channels. Zero external dependencies — ships with Python 3.12 standard library only.
- **Frontend**: React SPA with TypeScript and Vite. 78 pages covering dashboards, editors, terminals, and admin panels.

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for a deep dive.

---

## Deployment

### Docker (Recommended)

```bash
docker compose up -d
```

This starts the API server, PostgreSQL, Redis, and the frontend reverse proxy. See [`docker-compose.yml`](docker-compose.yml) and the [Deployment Guide](docs/DEPLOYMENT.md).

### Manual

Requires Python 3.12, Node.js 20+, PostgreSQL 16, and Redis 7. Follow the [manual deployment guide](docs/DEPLOYMENT.md#manual-installation).

### Cloud

- **Google Cloud**: One-click deployment script for GCE. See [`deploy/gce/`](deploy/gce/).
- **AWS / Azure**: Terraform modules available in [`deploy/terraform/`](deploy/terraform/).

---

## Documentation

| Document | Description |
|----------|-------------|
| [Documentation Hub](docs/) | Full documentation index |
| [Architecture Guide](docs/ARCHITECTURE.md) | System design and component details |
| [API Reference](docs/api/) | OpenAPI / Swagger documentation |
| [Agent Guide](docs/AGENT.md) | Agent installation and configuration |
| [Plugin Development](docs/PLUGINS.md) | Building and distributing plugins |
| [Playbook Authoring](docs/PLAYBOOKS.md) | Creating and running automation playbooks |
| [Deployment Guide](docs/DEPLOYMENT.md) | Production deployment instructions |
| [Changelog](CHANGELOG.md) | Version history and release notes |
| [Roadmap](ROADMAP.md) | Project roadmap and planned features |

---

## Community vs Enterprise

Mission Control is available in two editions:

| | Community | Enterprise |
|---|:---------:|:----------:|
| Core agent management | ✅ | ✅ |
| Playbook editor & runner | ✅ | ✅ |
| Basic RBAC | ✅ | ✅ |
| Plugin SDK | ✅ | ✅ |
| AI operations (basic) | ✅ | ✅ |
| SSO / SAML | ❌ | ✅ |
| Advanced audit logging | ❌ | ✅ |
| Premium support SLA | ❌ | ✅ |
| Custom branding | ❌ | ✅ |
| Compliance reports | ❌ | ✅ |

See [SUPPORTED_PLATFORMS.md](SUPPORTED_PLATFORMS.md) for platform-specific support details.

---

## Contributing

We welcome contributions of all kinds. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes following [conventional commits](CONTRIBUTING.md#commit-messages)
4. Push and open a Pull Request

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for community standards.

---

## Security

To report a vulnerability, see [SECURITY.md](SECURITY.md). **Do not open public issues for security vulnerabilities.**

---

## License

Mission Control Community Edition is released under the [GNU Affero General Public License v3.0](LICENSE).

Enterprise Edition is commercially licensed. Contact [enterprise@missioncontrol.dev](mailto:enterprise@missioncontrol.dev) for details.

---

<p align="center">
  Built with care by the Mission Control team and <a href="https://github.com/billboe3-png/MissionControl/graphs/contributors">community contributors</a>.
</p>
