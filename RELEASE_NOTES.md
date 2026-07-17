# Release Notes

## v3.0.0 — Production Release (Sprint 3.0)

### Highlights

- **Security**: JWT authentication on all 226+ API endpoints, rate limiting (60 req/min, 5 for login), production-hardened CORS
- **Performance**: N+1 query fixes, Redis singleton, batch database queries, 6 new database indexes
- **Production Ready**: Resource limits, structured logging, backup/restore scripts, production docker-compose
- **CI/CD**: GitHub Actions pipeline (ruff lint + pytest + TypeScript check + build)
- **Code Quality**: 178 import fixes, dead code removal, standardized logging across all routers

### Security (OWASP Audit)

- All 21 routers protected by JWT authentication via `get_current_user`
- Agent endpoints use API key authentication for inter-service communication
- Rate limiting: 60 requests/minute per IP (5 for login endpoint)
- Agent and health/version endpoints exempt from rate limiting
- Security headers: Referrer-Policy, Permissions-Policy
- CORS locked to specific methods (GET/POST/PUT/DELETE/PATCH) and headers
- Default database passwords removed from code (must come from `.env`)

### Performance

- `CompanyService.get_all()`: 3N → 4 queries (batch company stats)
- `SiteService.list_sites()`: Batch site stats + company names
- `DashboardService._get_agent_data()`: 4 queries → 1 aggregated query
- Redis singleton pattern replaces per-call client creation
- New indexes: Task.status, Task.priority, ParkingLot.status/priority/owner/category, RemoteHost.enabled, IntegrationProfile.enabled, Company.enabled

### Docker

- Resource limits on all 5 services
- `docker-compose.prod.yml` for production (no bind mounts, no docker.sock)
- JSON-file logging with rotation (10MB, 3 files)
- `restart: always` policy on all services

### DevOps

- Structured logging with request IDs and timing
- Backup script: `scripts/backup-db.ps1` (PostgreSQL gzip dumps)
- Restore script: `scripts/restore-db.ps1` (with confirmation prompt)
- GitHub Actions CI: ruff, pytest, TypeScript check, frontend build

### Code Cleanup

- Removed dead code: `db/session.py`, `git.py` stub
- Fixed 178 import sorting issues
- Standardized `logging.getLogger(__name__)` across all routers and services
- Version unified to 3.0.0 across backend, frontend, and API responses

### Breaking Changes

- `POSTGRES_USER` and `POSTGRES_PASSWORD` defaults changed from `mission_control` to empty string (must come from `.env`)
- `GET /api/v1` no longer returns `environment` field
- `git` router removed (was a stub returning 501)

---

## Previous Releases

### v2.8.0 — Automation & Playbooks
- Cron-based automation rules with 30+ trigger types
- Variable system (built-in + custom) with template rendering
- Playbook CRUD with JSON editor
- Task logging with retry logic
- 1062+ tests

### v2.7.0 — Standalone Agent
- `.agents/agent/` directory with `agent.py`
- 8 CLI commands: version, register, heartbeat, command-result, inventory
- SQLite registry for API keys
- JWT token management

### v2.5.0 — Infrastructure Dashboard
- Zabbix, Hyper-V, Proxmox monitoring cards
- Windows Admin Center-inspired UI
- 8-page infrastructure overview

### v2.3.0 — Identity & Access
- Active Directory / LDAP integration
- Active sessions tracking
- Identity provider support

### v2.2.0 — AI Assistant & Projects
- AI chat with OpenAI/Anthropic integration
- GitHub Issues integration
- Project management with tasks and notes
