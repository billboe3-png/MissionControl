# Database Development

Mission Control uses PostgreSQL 16 with SQLAlchemy 2.0 ORM and Alembic for migrations.

## Models

### SQLAlchemy 2.0 Style

Models are defined in `backend/app/models/db/`. Each model maps to a database table:

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.base import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="pending")
    priority = Column(String(20), nullable=False, default="medium")
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default="now()")
    updated_at = Column(DateTime, server_default="now()", onupdate="now()")

    project = relationship("Project", back_populates="tasks")
    company = relationship("Company", back_populates="tasks")
```

### Model Conventions

| Convention | Example |
|------------|---------|
| Table name | `snake_case` plural: `remote_hosts`, `credential_profiles` |
| Primary key | `id = Column(Integer, primary_key=True, index=True)` |
| Timestamps | `created_at` and `updated_at` with `server_default="now()"` |
| Foreign keys | `Column(Integer, ForeignKey("table.id"))` |
| Relationships | Defined on both sides with `back_populates` |
| Soft delete | Not used — records are deleted permanently |

### All Models

| Model | Table | File |
|-------|-------|------|
| `User` | `users` | `models/db/user.py` |
| `Company` | `companies` | `models/db/company.py` |
| `Site` | `sites` | `models/db/site.py` |
| `RemoteHost` | `remote_hosts` | `models/db/host.py` |
| `CredentialProfile` | `credential_profiles` | `models/db/credential.py` |
| `CommandHistory` | `command_history` | `models/db/command_history.py` |
| `CommandTemplate` | `command_templates` | `models/db/command_template.py` |
| `ScheduledCommand` | `scheduled_commands` | `models/db/scheduled_command.py` |
| `Agent` | `agents` | `models/db/agent.py` |
| `AgentCommand` | `agent_commands` | `models/db/agent_command.py` |
| `AgentRegistrationToken` | `agent_registration_tokens` | `models/db/agent_token.py` |
| `IntegrationProfile` | `integration_profiles` | `models/db/integration.py` |
| `Playbook` | `playbooks` | `models/db/playbook.py` |
| `PlaybookStep` | `playbook_steps` | `models/db/playbook.py` |
| `PlaybookVariable` | `playbook_variables` | `models/db/playbook.py` |
| `PlaybookSchedule` | `playbook_schedules` | `models/db/playbook.py` |
| `PlaybookExecution` | `playbook_executions` | `models/db/playbook.py` |
| `EventTrigger` | `event_triggers` | `models/db/event_trigger.py` |
| `ExecutionLog` | `execution_logs` | `models/db/execution_log.py` |
| `ApprovalWorkflow` | `approval_workflows` | `models/db/approval.py` |
| `ApprovalRequest` | `approval_requests` | `models/db/approval.py` |
| `Project` | `projects` | `models/db/project.py` |
| `Task` | `tasks` | `models/db/task.py` |
| `Note` | `notes` | `models/db/note.py` |
| `ParkingLot` | `parking_lot` | `models/db/parking_lot.py` |
| `Resume` | `resumes` | `models/db/resume.py` |
| `AuditTrail` | `audit_trail` | `models/db/audit_trail.py` |

## Creating a New Model

### 1. Define the model

Create a new file in `backend/app/models/db/` or add to an existing domain file:

```python
# backend/app/models/db/webhook.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from app.db.base import Base


class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(1024), nullable=False)
    secret = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    created_at = Column(DateTime, server_default="now()")
```

### 2. Generate a migration

```bash
cd backend
alembic revision --autogenerate -m "add webhooks table"
```

This creates a new file in `backend/alembic/versions/`. Review the generated migration — autogenerate does not detect all changes (e.g., indexes, server defaults).

### 3. Edit the migration if needed

```python
"""add webhooks table

Revision ID: abc123
Revises: def456
Create Date: 2026-01-15 10:30:00.000000
"""
from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    op.create_table(
        "webhooks",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("url", sa.String(1024), nullable=False),
        sa.Column("secret", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_webhooks_company_id", "webhooks", ["company_id"])


def downgrade() -> None:
    op.drop_index("ix_webhooks_company_id")
    op.drop_table("webhooks")
```

### 4. Apply the migration

```bash
alembic upgrade head
```

## Adding a Column to an Existing Model

### 1. Add the column to the model

```python
class RemoteHost(Base):
    # ... existing columns ...
    tags = Column(Text, nullable=True)  # new column
```

### 2. Generate and review the migration

```bash
alembic revision --autogenerate -m "add tags column to remote_hosts"
```

### 3. Apply

```bash
alembic upgrade head
```

## Alembic Commands

| Command | Purpose |
|---------|---------|
| `alembic upgrade head` | Apply all pending migrations |
| `alembic downgrade -1` | Roll back one migration |
| `alembic history` | List all migrations |
| `alembic current` | Show current migration revision |
| `alembic revision --autogenerate -m "description"` | Generate a new migration |
| `alembic merge -m "merge heads" <rev1> <rev2>` | Merge diverged migration heads |

### Configuration

Alembic is configured in `backend/alembic.ini`. The database URL is read from the same environment variables used by the application:

```ini
[alembic]
script_location = alembic
sqlalchemy.url = postgresql+psycopg://mission_control:mission_control@postgres:5432/mission_control
```

In practice, the URL is overridden at runtime from `POSTGRES_*` environment variables.

## Pydantic Schemas

Pydantic v2 schemas define the contract between the API and clients. Create schemas in `backend/app/schemas/`:

```python
from pydantic import BaseModel, ConfigDict


class WebhookBase(BaseModel):
    url: str
    secret: str | None = None
    is_active: bool = True


class WebhookCreate(WebhookBase):
    company_id: int


class WebhookUpdate(BaseModel):
    url: str | None = None
    secret: str | None = None
    is_active: bool | None = None


class WebhookResponse(WebhookBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    created_at: str
```

### Schema Conventions

| Schema | Purpose |
|--------|---------|
| `XBase` | Shared fields for create and update |
| `XCreate` | Fields required on creation (extends XBase) |
| `XUpdate` | All fields optional (for PATCH-style updates) |
| `XResponse` | Response serialization (includes `from_attributes=True`) |

## Seed Data

The seed framework is idempotent and runs on every startup (in Docker) or manually:

```bash
cd backend
python -m app.seed.runner
```

Seed data includes:
- Default admin user
- Default company and site
- Sample data (if configured)

The seed runner checks for existing records before inserting, so it is safe to run repeatedly.

## Relationships

Define relationships on both sides of a foreign key:

```python
# In Company model
class Company(Base):
    __tablename__ = "companies"
    # ...
    sites = relationship("Site", back_populates="company")
    hosts = relationship("RemoteHost", back_populates="company")


# In Site model
class Site(Base):
    __tablename__ = "sites"
    # ...
    company_id = Column(Integer, ForeignKey("companies.id"))
    company = relationship("Company", back_populates="sites")
```

Use `lazy="select"` (default) for most relationships. Use `lazy="joined"` for eagerly-loaded associations that are always needed.

## Cross-References

- See [BACKEND.md](BACKEND.md) for the repository pattern that queries these models.
- See [DATABASE.md](../architecture/DATABASE.md) for the architecture-level database design.
- See [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md) for initial database setup.
- See [CI_CD.md](CI_CD.md) for how migrations run in CI.
