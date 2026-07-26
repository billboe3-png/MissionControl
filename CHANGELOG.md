# Changelog

All notable changes to Mission Control will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

---

## [3.0.0] - 2026-07-01

### Added

- **AI Operations module** — Natural-language task generation, anomaly detection across agent telemetry, automated remediation suggestions, and LLM-powered log analysis.
- **Plugin System** — Python-based plugin SDK with community marketplace, custom UI panels, dashboard widgets, and full lifecycle event hooks.
- **Multi-tenancy** — Organization and workspace isolation with role-based access control (RBAC) across tenants.
- **Playbook editor improvements** — Drag-and-drop workflow designer with new step types: conditions, loops, and parallel execution.
- **Web-based terminal** — SSH-style remote terminal sessions directly from the browser with session recording and audit trail.
- **Live log streaming** — Real-time log streaming from any connected agent.
- **Inventory change tracking** — Diff views for software, hardware, and network inventory changes.
- **Bulk operations** — Execute commands, playbooks, and updates across agent groups.
- **SSO / SAML integration** (Enterprise) — Single sign-on with SAML 2.0 identity providers.
- **Advanced audit logging** (Enterprise) — Tamper-evident, append-only audit logs with custom retention policies.
- **Compliance reports** (Enterprise) — SOC 2, GDPR, and HIPAA-ready compliance tooling.
- **Custom branding** (Enterprise) — White-label UI with custom logos, colors, and themes.
- **One-click GCE deployment** — Deployment script for Google Compute Engine.
- **Terraform modules** — Infrastructure-as-code modules for AWS and Azure.
- 78 frontend pages covering dashboards, editors, terminals, and admin panels.
- 286 API endpoints across 25 routers.
- 29 database tables with Alembic migration support.

### Changed

- **Backend rewritten** — Migrated from Flask to FastAPI with async support.
- **Frontend rewritten** — Migrated from Vue to React/TypeScript with Vite.
- **Database upgraded** — Migrated from PostgreSQL 14 to PostgreSQL 16 as the primary version.
- **Redis upgraded** — Minimum Redis version bumped to 7.0.
- **Agent rewritten** — Zero external dependencies; ships with Python 3.12 standard library only.
- **Agent configuration** — Moved from `/etc/mission-control-agent/` to `~/.config/mission-control-agent/config.yaml`.
- **Authentication** — Switched from session-based to JWT-based authentication.
- **API versioning** — All endpoints now under `/api/v1/` prefix.
- Upgraded SQLAlchemy to 2.0 with modern query patterns.

### Deprecated

- Flask-based API server (removed in 3.0.0).
- Vue.js frontend (removed in 3.0.0).
- PostgreSQL 13 support (end of life).

### Removed

- Legacy XML-RPC agent protocol.
- Monolithic frontend architecture.
- Python 3.11 support.

### Fixed

- Agent heartbeat thundering herd — added jitter to stagger reconnect attempts.
- Playbook execution race condition when steps run in parallel.
- Memory leak in long-running WebSocket connections.
- SQL injection vulnerability in legacy search endpoint (CVE-2026-XXXXX).

### Security

- All agent communication now requires TLS.
- Secrets encrypted at rest using AES-256.
- Audit logging for all administrative actions.
- Plugin sandboxing with restricted filesystem access.

---

## [2.0.0] - 2025-06-15

### Added

- **Playbook engine** — Visual playbook editor with step types: commands, scripts, and sequential execution.
- **Scheduled tasks** — Cron-based scheduling for playbook runs.
- **Agent groups** — Organize agents into groups for bulk management.
- **Software inventory** — Automatic discovery of installed software across agents.
- **Hardware inventory** — CPU, memory, disk, and network hardware details.
- **Dashboard widgets** — Customizable dashboard with drag-and-drop widget layout.
- **API documentation** — Interactive Swagger/OpenAPI docs at `/docs`.
- **Webhook integrations** — Trigger external services on playbook completion or agent events.
- **CSV/JSON export** — Export inventory and playbook run data.
- Role-based access control with admin, operator, and viewer roles.
- API key authentication for programmatic access.

### Changed

- Upgraded PostgreSQL from 12 to 14.
- Upgraded Redis from 6 to 7.
- Agent heartbeat protocol now supports bidirectional commands.
- Improved agent reconnection logic with exponential backoff.

### Deprecated

- API v1 endpoints (replaced by v1 with new naming conventions in 3.0.0).
- Session-based authentication (replaced by JWT in 3.0.0).

### Fixed

- Agent disconnection not propagating to UI in real time.
- Playbook step timeout not cancelling subprocess correctly.
- Race condition in concurrent playbook runs on the same agent.

---

## [1.0.0] - 2024-12-01

### Added

- **Initial public release** of Mission Control Community Edition.
- **Agent management** — Register, monitor, and manage remote agents.
- **Heartbeat monitoring** — Agents report health status at configurable intervals.
- **Remote command execution** — Run commands on agents from the web UI.
- **Basic inventory** — System information, OS details, and uptime.
- **User management** — Admin-created accounts with password authentication.
- **REST API** — Core API for agent registration, status, and command execution.
- **Web dashboard** — Single-page application for infrastructure overview.
- PostgreSQL 12 as the primary database.
- Redis 6 for caching and task queuing.
- Docker Compose setup for local development.
- Basic logging with configurable levels.

---

[3.0.0]: https://github.com/billboe3-png/MissionControl/compare/v2.0.0...v3.0.0
[2.0.0]: https://github.com/billboe3-png/MissionControl/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/billboe3-png/MissionControl/releases/tag/v1.0.0
