# Mission Control — Database

**Version:** 3.0.0

---

## Overview

Mission Control uses PostgreSQL 16 as its primary data store. The schema contains 29 tables organized by domain.

---

## 1. Technology

| Property | Value |
|----------|-------|
| Engine | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Connection | psycopg3 (async) |
| Pool size | 10 (configurable) |
| Max overflow | 20 (configurable) |

---

## 2. Tables

### Agent Management

| Table | Purpose | Key Relationships |
|-------|---------|-------------------|
| `agents` | Registered agents | → sites |
| `agent_commands` | Command queue | → agents |
| `agent_registration_tokens` | Registration tokens | → agents |
| `agent_remote_targets` | Remote targets per agent | → agents |

### Multi-Tenancy

| Table | Purpose | Key Relationships |
|-------|---------|-------------------|
| `companies` | Tenant organizations | → sites, users |
| `sites` | Physical/logical locations | → agents |
| `users` | Authenticated users | → companies |

### Remote Operations

| Table | Purpose | Key Relationships |
|-------|---------|-------------------|
| `remote_hosts` | SSH/WinRM targets | → credential_profiles |
| `credential_profiles` | Encrypted credentials | — |
| `command_history` | Execution audit log | → remote_hosts |
| `command_templates` | Reusable commands | — |
| `scheduled_commands` | Cron-scheduled commands | → remote_hosts |

### Automation

| Table | Purpose | Key Relationships |
|-------|---------|-------------------|
| `playbooks` | Automation definitions | → playbook_steps |
| `playbook_steps` | Individual steps | → playbooks |
| `playbook_executions` | Execution records | → playbooks |
| `playbook_schedules` | Cron schedules | → playbooks |
| `playbook_variables` | Template variables | → playbooks |
| `event_triggers` | Event-driven triggers | — |
| `approval_requests` | Approval workflow | — |
| `approval_workflows` | Approval definitions | — |
| `execution_logs` | Step-level logs | → playbook_executions |
| `audit_trail` | Audit trail | — |

### Plugins & Integrations

| Table | Purpose | Key Relationships |
|-------|---------|-------------------|
| `plugins` | Installed plugins | — |
| `integration_profiles` | Integration configuration | — |

### Workspace

| Table | Purpose | Key Relationships |
|-------|---------|-------------------|
| `projects` | Project management | → tasks |
| `tasks` | Task tracking | → projects |
| `notes` | Notepad entries | — |
| `parking_lot` | Backlog items | — |
| `resumes` | Resume context | — |

---

## 3. Entity Relationships

```
companies ─────┬──── sites ──────── agents
               │         │              │
               │         │              ├── agent_commands
               │         │              ├── agent_remote_targets
               │         │              └── agent_registration_tokens
               │         │
               └──── users

remote_hosts ───── credential_profiles
       │
       └──── command_history

playbooks ─────┬──── playbook_steps
               ├──── playbook_executions ───── execution_logs
               ├──── playbook_schedules
               ├──── playbook_variables
               └──── (via event_triggers)

projects ───── tasks
```

---

## 4. Migration Strategy

### Alembic

Migrations are managed by Alembic in `backend/alembic/`.

```bash
# Generate migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Migration Rules

1. **Never delete columns** — deprecate first, remove in next major version
2. **Never rename columns** — add new, migrate data, remove old
3. **Always provide defaults** — for new non-nullable columns
4. **Test rollback** — every migration must be reversible
5. **Version stamp** — mark migrations with version number

---

## 5. Connection Configuration

```python
# backend/app/core/config.py
DATABASE_URL = (
    f"postgresql+psycopg://"
    f"{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}"
    f"/{POSTGRES_DB}"
)
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_DB` | `mission_control` | Database name |
| `POSTGRES_USER` | `mission_control` | Database user |
| `POSTGRES_PASSWORD` | `mission_control` | Database password |
| `POSTGRES_HOST` | `postgres` | Database host |
| `POSTGRES_PORT` | `5432` | Database port |
| `DATABASE_ECHO` | `False` | SQL logging |
| `DATABASE_POOL_SIZE` | `10` | Connection pool size |
| `DATABASE_MAX_OVERFLOW` | `20` | Max overflow connections |

---

## 6. Redis

Redis is used for caching and ephemeral data, not primary storage.

### Usage

| Key Pattern | Purpose | TTL |
|-------------|---------|-----|
| `session:{token}` | Session cache | 1 hour |
| `ratelimit:{ip}` | Rate limiting | 60 seconds |
| `agent:{id}:state` | Agent state cache | 5 minutes |

### Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_HOST` | `redis` | Redis host |
| `REDIS_PORT` | `6379` | Redis port |

---

## 7. Data Access Pattern

### Repository Pattern

All database access goes through repositories.

```
Router → Service → Repository → SQLAlchemy → PostgreSQL
```

### Example

```python
# Repository
class AgentRepository:
    @staticmethod
    def get_by_id(db: Session, agent_id: int) -> Agent | None:
        return db.query(Agent).filter(Agent.id == agent_id).first()

# Service
class AgentService:
    async def get_agent(self, db: Session, agent_id: int) -> AgentResponse:
        agent = AgentRepository.get_by_id(db, agent_id)
        if agent is None:
            raise HTTPException(status_code=404, detail="Agent not found")
        return self._to_response(agent)
```

---

## 8. Seed Data

Demo data is seeded via `backend/app/seed/`.

```bash
# Run seeder
python -m app.seed.runner
```

### Seed Modules

| Module | Purpose |
|--------|---------|
| `companies` | Demo companies |
| `sites` | Demo sites |
| `users` | Demo users (admin, operator, viewer) |
| `agents` | Demo agents |
| `projects` | Demo projects |
| `tasks` | Demo tasks |
| `notes` | Demo notes |
| `playbooks` | Demo playbooks |

---

## 9. Backup

### Manual Backup

```bash
docker exec postgres pg_dump -U mission_control mission_control > backup.sql
```

### Automated Backup

```bash
# Cron job (daily at 2 AM)
0 2 * * * docker exec postgres pg_dump -U mission_control mission_control | gzip > /backups/mc_$(date +\%Y\%m\%d).sql.gz
```

### Restore

```bash
cat backup.sql | docker exec -i postgres psql -U mission_control mission_control
```
