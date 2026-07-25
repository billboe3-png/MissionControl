# Changelog

All notable changes to Mission Control will be documented in this file.

## [3.0.0] - Production Release

### Security (OWASP Audit)
- JWT authentication on all 226+ API endpoints
- Rate limiting (60 req/min, 5 for login)
- Production-hardened CORS
- Agent endpoints use API key authentication for inter-service communication
- Security headers: Referrer-Policy, Permissions-Policy
- Default database passwords removed from code (must come from `.env`)

### Performance
- N+1 query fixes across Company, Site, and Dashboard services
- Redis singleton pattern replaces per-call client creation
- 6 new database indexes (Task, ParkingLot, RemoteHost, IntegrationProfile, Company)

### Docker
- Resource limits on all 5 services
- `docker-compose.prod.yml` for production (no bind mounts, no docker.sock)
- JSON-file logging with rotation (10MB, 3 files)
- `restart: always` policy on all services

### DevOps
- GitHub Actions CI pipeline (ruff lint + pytest + TypeScript check + frontend build)
- Backup script: `scripts/backup-db.ps1` (PostgreSQL gzip dumps)
- Restore script: `scripts/restore-db.ps1` (with confirmation prompt)
- Structured logging with request IDs and timing

### Agent Relay System
- AgentHyperVProvider write operations (start/stop/restart/pause/resume VM, checkpoints) dispatch commands to agent via server command queue
- AgentProxmoxProvider: full Proxmox read/write provider backed by agent inventory
- AgentVeeamProvider: full Veeam provider (19 methods) backed by agent inventory
- AgentZabbixProvider: full Zabbix provider (16 methods) backed by agent plugin
- AgentActiveDirectoryProvider: AD provider backed by agent plugin (LDAP)
- AgentMicrosoft365Provider: M365 provider backed by agent plugin (Microsoft Graph)
- Provider factories rewritten with `host_id` support and agent dispatch/fallback

### Agent Plugins (`.agents/agent/plugins/`)
- Zabbix plugin: JSON-RPC API collector for hosts, groups, triggers, problems
- Active Directory plugin: LDAP collector for users, groups, devices
- Microsoft 365 plugin: Microsoft Graph API collector for users, groups, devices, service health

### Agent Remote Collectors
- `collect_proxmox_inventory()` via SSH (pvesh CLI)
- `collect_veeam_inventory()` via PSRemoting/WinRM (Veeam PowerShell module)
- `RemoteManager.collect_inventory()` updated to call new collectors

### Code Cleanup
- Removed dead code: `db/session.py`, `git.py` stub
- Fixed 178 import sorting issues
- Standardized `logging.getLogger(__name__)` across all routers and services
- Version unified to 3.0.0 across backend, frontend, and API responses

### Breaking Changes
- `POSTGRES_USER` and `POSTGRES_PASSWORD` defaults changed from `mission_control` to empty string (must come from `.env`)
- `GET /api/v1` no longer returns `environment` field
- `git` router removed (was a stub returning 501)

## [0.1.0] - Development Preview

### Added

- CLI framework with command registry system
- Bootstrap module for argument parsing and context creation
- Registry module for command registration and dispatch
- Config module for configuration loading and merging
- Validation module with reusable validation helpers
- Logger module for timestamped log entries
- Output engine for console, JSON, and JSON-pretty rendering
- Help command with registry-based documentation
- Doctor command for environment, Docker, and HTTP health checks
- Docker command for Docker Compose stack management (up, down, logs)
- Git command for safe Git operations (status, commit)
- Status command for developer environment status
- Version command for CLI version display
- Init command for idempotent project initialization
- Pester test framework with tests for Bootstrap, Registry, Logger, Helpers, and Validation
- CI quality gate script (Invoke-Quality.ps1)
- GitHub Actions workflow for continuous integration
- VS Code workspace configuration (extensions, settings, tasks, launch)
- Developer documentation (README.md, CONTRIBUTING.md, docs/architecture.md)

### Changed

- Fixed Doctor command null message handling for Git and Python version checks
- Enhanced Help command to display command descriptions from registry metadata
- Added subcommand validation helpers (Assert-McValidSubcommand) to Validation module
- Updated Docker and Git commands to use shared validation helpers

### Fixed

- Doctor command empty Message parameter binding error
- Registry.Tests.ps1 PowerShell version check issue
- Validation.Tests.ps1 Pester 3 syntax compatibility
- Logger.Tests.ps1 directory existence test
- Helpers.Tests.ps1 exit code test for Windows compatibility
