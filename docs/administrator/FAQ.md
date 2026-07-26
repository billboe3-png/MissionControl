# Frequently Asked Questions

**Version:** 3.0.0

---

## Installation

### What are the minimum system requirements?

2 vCPU, 4 GB RAM, 20 GB disk, Docker 24+, Docker Compose v2.20+. See [Installation](INSTALLATION.md) for full requirements.

### Can I run Mission Control on Windows?

Yes. The API server and dashboard run on any platform with Docker. The agent supports both Windows (PowerShell) and Linux. See [Installation](INSTALLATION.md) for Windows-specific instructions.

### Can I run multiple instances on the same host?

Yes. Set a unique `COMPOSE_PROJECT_NAME` in `.env` for each instance and use different ports. See [Configuration](CONFIGURATION.md).

### How do I generate a secure `MISSIONCONTROL_SECRET_KEY`?

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

This generates a valid Fernet key. See [Configuration](CONFIGURATION.md).

---

## Configuration

### What is the difference between Community and Enterprise editions?

Community (`EDITION=community`) provides core functionality. Enterprise (`EDITION=enterprise`) adds custom roles, audit logging, advanced RBAC, and full marketplace access. See [Configuration](CONFIGURATION.md).

### Can I change the database after installation?

Yes. Update `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` in `.env`, then run `alembic upgrade head`. See [Configuration](CONFIGURATION.md).

### How do I enable HTTPS?

Use a reverse proxy (nginx, Caddy, or Traefik) to terminate TLS. Mission Control does not handle TLS directly. See [Security Hardening](SECURITY_HARDENING.md).

### Can I integrate with Active Directory?

Yes. Configure `AD_SERVER`, `AD_PORT`, `AD_USE_SSL`, `AD_USERNAME`, `AD_PASSWORD`, and `AD_BASE_DN` in `.env`. See [Configuration](CONFIGURATION.md).

---

## Agents

### How many agents can I connect?

There is no hard limit. Agent capacity depends on your server resources and database connection pool. See [Performance](PERFORMANCE.md) for sizing recommendations.

### What happens when an agent goes offline?

The agent enters offline mode (if configured) and queues commands locally. When connectivity is restored, queued commands execute and results sync to the server. See [Agent Deployment](AGENT_DEPLOYMENT.md).

### How do I update agents?

Agents can auto-update if configured, or update manually by downloading the new version. See [Agent Deployment](AGENT_DEPLOYMENT.md).

### Can agents run on different networks?

Yes. Agents only need outbound access to the API server. No inbound firewall rules are required on agent hosts. See [Agent Deployment](AGENT_DEPLOYMENT.md).

### What Python version does the agent require?

Python 3.12 or newer. The agent has no external dependencies beyond the standard library. See [Agent Deployment](AGENT_DEPLOYMENT.md).

---

## Plugins

### What plugin types are available?

Server, Agent, and Hybrid. Server plugins run in the API process. Agent plugins run on remote hosts. Hybrid plugins span both. See [Plugin Management](PLUGIN_MANAGEMENT.md).

### Can I develop custom plugins?

Yes. Plugins follow a standard Python interface based on `PluginBase`. See [Plugin Management](PLUGIN_MANAGEMENT.md) for the interface definition.

### What happens to plugins during an upgrade?

Plugins are validated for compatibility after server upgrades. Incompatible plugins are flagged and must be updated or removed. See [Upgrades](UPGRADES.md).

### How do I check plugin health?

```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/plugins/health
```

See [Monitoring](MONITORING.md).

---

## Upgrades

### Can I upgrade directly from version 1.x to 3.0.0?

No. Upgrade to 2.x first, then to 3.0.0. See [Upgrades](UPGRADES.md) for the version compatibility matrix.

### Do I need to stop the API server for upgrades?

No. Alembic migrations run as part of the upgrade process. In Docker Compose, the old container is replaced with the new one. See [Upgrades](UPGRADES.md).

### How do I roll back a failed upgrade?

Restore the database from backup, checkout the previous version tag, and restart. See [Upgrades](UPGRADES.md) for rollback procedures.

### Are database migrations backward-compatible?

Migrations are forward-only within a major version. Always back up before upgrading. See [Upgrades](UPGRADES.md).

---

## Backup

### What should I back up?

PostgreSQL database (critical), Redis data (high), configuration files (high), plugin data (medium). See [Backup and Restore](BACKUP_AND_RESTORE.md).

### How often should I back up?

Daily at minimum. For production, consider continuous WAL archiving for point-in-time recovery. See [Backup and Restore](BACKUP_AND_RESTORE.md).

### How do I test my backups?

Restore to an isolated environment quarterly and verify data integrity, agent connectivity, and plugin status. See [Backup and Restore](BACKUP_AND_RESTORE.md).

### Can I back up while the system is running?

Yes. `pg_dump` is consistent and does not require downtime. `BGSAVE` for Redis is non-blocking. See [Backup and Restore](BACKUP_AND_RESTORE.md).

---

## Troubleshooting

### My agent shows offline. What do I check?

1. Agent service status on the host.
2. Network connectivity to the API server.
3. API key validity.
4. Agent logs at `/var/log/mission-control-agent/agent.log`.

See [Troubleshooting](TROUBLESHOOTING.md).

### The API server won't start. What do I check?

1. Container logs: `docker compose logs api`.
2. Database connectivity: `pg_isready`.
3. Redis connectivity: `redis-cli ping`.
4. Environment variables in `.env`.

See [Troubleshooting](TROUBLESHOOTING.md).

### How do I check system health?

```bash
curl http://localhost:8000/live
curl http://localhost:8000/ready
curl http://localhost:8000/subsystems
curl http://localhost:8000/version
```

See [Monitoring](MONITORING.md).

### Where are the logs?

Docker Compose: `docker compose logs <service>`. Manual install: `journalctl -u mission-control`. Agent: `/var/log/mission-control-agent/agent.log`. See [Logging](LOGGING.md).

---

## Performance

### How do I scale for more agents?

Increase `DATABASE_POOL_SIZE`, `DATABASE_MAX_OVERFLOW`, and worker count. For 500+ agents, consider dedicated database and Redis instances. See [Performance](PERFORMANCE.md).

### What is the recommended production configuration?

4 vCPU, 8 GB RAM, 4 workers, `DATABASE_POOL_SIZE=10`, `DATABASE_MAX_OVERFLOW=20`, 256 MB Redis. See [Performance](PERFORMANCE.md) for the full sizing guide.

### How do I identify slow queries?

Enable `DATABASE_ECHO=true` temporarily, or configure PostgreSQL `log_min_duration_statement`. See [Performance](PERFORMANCE.md).

---

## Multi-Tenancy

### How is data isolated between companies?

All database queries include a `company_id` filter enforced at the application layer. Users can only access data within their assigned company and sites. See [Company and Site Management](COMPANY_AND_SITE_MANAGEMENT.md).

### Can a user belong to multiple companies?

In community edition, users are assigned to one company. Enterprise edition supports multi-company user assignments. See [Company and Site Management](COMPANY_AND_SITE_MANAGEMENT.md).

---

## API

### How many endpoints does Mission Control expose?

286 endpoints across 25 routers. See the OpenAPI documentation at `http://localhost:8000/docs` (Swagger UI) or `http://localhost:8000/redoc` (ReDoc).

### How do I authenticate API requests?

Use JWT Bearer tokens for user authentication or `X-API-Key` header for agent authentication. See [User Management](USER_MANAGEMENT.md) and [Agent Deployment](AGENT_DEPLOYMENT.md).

### Is there rate limiting?

Yes. Default: 60 requests/minute for API, 10 requests/minute for authentication endpoints. Configurable via environment variables. See [Configuration](CONFIGURATION.md).
