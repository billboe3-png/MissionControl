# Backend Architecture

Mission Control's backend is a Python 3.12 application built with FastAPI, SQLAlchemy 2.0, and Pydantic v2.

## Application Factory

The entry point is `backend/app/main.py`. It creates the FastAPI application, configures middleware, and registers all routers:

```python
from fastapi import FastAPI
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.project_name,
    version="3.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)
```

### Middleware Stack

Middleware is applied in reverse order (last added = first executed):

1. **Request Logging** — attaches `X-Request-ID`, logs method, path, status, and timing.
2. **Rate Limiting** — in-memory sliding window (60 req/min general, 5 req/min for `/auth/login`).
3. **CORS** — configurable origins from `BACKEND_CORS_ORIGINS`.

### Router Registration

All routers are mounted under the `/api/v1` prefix:

```python
app.include_router(remote.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(automation.router, prefix="/api/v1")
# ... 25 routers total
```

## Request Lifecycle

```
Client Request
    │
    ▼
Request Logging Middleware (X-Request-ID, timing)
    │
    ▼
Rate Limit Middleware (sliding window check)
    │
    ▼
CORS Middleware
    │
    ▼
FastAPI Router
    │
    ▼
Dependency Injection (DB session, auth, company context)
    │
    ▼
Router Handler
    │
    ▼
Service Layer (business logic)
    │
    ▼
Repository Layer (data access)
    │
    ▼
SQLAlchemy ORM → PostgreSQL
    │
    ▼
Response (Pydantic schema serialization)
```

## Layered Architecture

### Routers (`app/routers/`)

Routers define HTTP endpoints. Each router is a FastAPI `APIRouter` in its own module:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth_dependency import get_current_user
from app.db.database import get_db
from app.models.db.user import User
from app.schemas.remote import HostCreate, HostResponse
from app.services.remote_service import RemoteService

router = APIRouter(prefix="/remote", tags=["Remote Operations"])


@router.get("/hosts", response_model=list[HostResponse])
def list_hosts(
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[HostResponse]:
    hosts = RemoteService.list_hosts(db, search=search)
    return hosts


@router.post("/hosts", response_model=HostResponse, status_code=201)
def create_host(
    host_in: HostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HostResponse:
    host = RemoteService.create_host(db, host_in, created_by=current_user.id)
    return host
```

**Rules for routers:**
- Never put business logic in routers — delegate to services.
- Always use dependency injection for `db` and `current_user`.
- Return Pydantic schemas, not ORM models.
- Raise `HTTPException` for error responses.

### Services (`app/services/`)

Services contain business logic and orchestration. They are plain Python classes with static or instance methods:

```python
from sqlalchemy.orm import Session
from app.models.db.host import RemoteHost
from app.repositories.host_repository import HostRepository
from app.schemas.remote import HostCreate


class RemoteService:
    @staticmethod
    def list_hosts(db: Session, search: str | None = None) -> list[RemoteHost]:
        if search:
            return HostRepository.search(db, search)
        return HostRepository.get_all(db)

    @staticmethod
    def create_host(db: Session, host_in: HostCreate, created_by: int) -> RemoteHost:
        host = HostRepository.create(db, obj_in=host_in, created_by=created_by)
        return host
```

**Rules for services:**
- Services do not import routers or schemas for HTTP-specific types.
- Services can raise domain exceptions for business rule violations.
- Services call repositories for data access, never raw SQL.

### Repositories (`app/repositories/`)

Repositories provide static data-access methods per entity. They encapsulate all SQLAlchemy queries:

```python
from sqlalchemy.orm import Session
from app.models.db.host import RemoteHost
from app.schemas.remote import HostCreate


class HostRepository:
    @staticmethod
    def get_all(db: Session) -> list[RemoteHost]:
        return db.query(RemoteHost).all()

    @staticmethod
    def get_by_id(db: Session, host_id: int) -> RemoteHost | None:
        return db.query(RemoteHost).filter(RemoteHost.id == host_id).first()

    @staticmethod
    def search(db: Session, term: str) -> list[RemoteHost]:
        return (
            db.query(RemoteHost)
            .filter(RemoteHost.name.ilike(f"%{term}%"))
            .all()
        )

    @staticmethod
    def create(db: Session, *, obj_in: HostCreate, created_by: int) -> RemoteHost:
        host = RemoteHost(**obj_in.model_dump(), created_by=created_by)
        db.add(host)
        db.commit()
        db.refresh(host)
        return host
```

### Models (`app/models/db/`)

SQLAlchemy 2.0 ORM models define the database schema. Each model maps to a table:

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class RemoteHost(Base):
    __tablename__ = "remote_hosts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    hostname = Column(String(512), nullable=False)
    protocol = Column(String(10), nullable=False, default="ssh")
    port = Column(Integer, nullable=False, default=22)
    is_active = Column(Boolean, default=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default="now()")
    updated_at = Column(DateTime, server_default="now()", onupdate="now()")

    company = relationship("Company", back_populates="hosts")
    credentials = relationship("CredentialProfile", back_populates="host")
```

See [DATABASE.md](DATABASE.md) for model creation and migration workflows.

### Schemas (`app/schemas/`)

Pydantic v2 models define request/response contracts:

```python
from pydantic import BaseModel, ConfigDict


class HostBase(BaseModel):
    name: str
    hostname: str
    protocol: str = "ssh"
    port: int = 22


class HostCreate(HostBase):
    credential_id: int | None = None


class HostResponse(HostBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    company_id: int | None
    created_at: str
```

### Providers (`app/providers/`)

Providers implement platform-specific logic behind ABC interfaces. This is the Strategy pattern:

```python
from abc import ABC, abstractmethod


class RemoteProvider(ABC):
    @abstractmethod
    def connect(self, host: str, port: int, credentials: dict) -> None: ...

    @abstractmethod
    def execute(self, command: str) -> str: ...

    @abstractmethod
    def disconnect(self) -> None: ...
```

Concrete implementations: `SSHProvider`, `WinRMProvider`. The `ProviderFactory` selects the correct provider based on the host protocol.

Platform providers (Zabbix, Proxmox, Hyper-V, Identity) follow the same pattern with their own ABC interfaces.

## Dependency Injection

FastAPI's `Depends()` is used for:

- **Database sessions**: `db: Session = Depends(get_db)`
- **Authentication**: `current_user: User = Depends(get_current_user)`
- **Company context**: `company_id: int = Depends(get_company_id)`

These are defined in `app/core/`:

| File | Purpose |
|------|---------|
| `auth_dependency.py` | JWT validation, user extraction |
| `company_context.py` | Multi-tenant company/site scoping |
| `config.py` | Pydantic Settings for environment variables |
| `security.py` | Fernet encryption, JWT signing |

## Configuration

Settings are loaded from environment variables via Pydantic Settings:

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    project_name: str = "Mission Control"
    secret_key: str = ""
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "mission_control"
    postgres_user: str = "mission_control"
    postgres_password: str = "mission_control"
    redis_host: str = "redis"
    redis_port: int = 6379
    cors_origins: list[str] = ["http://localhost", "http://localhost:3000"]
    rate_limit_per_minute: int = 60

    class Config:
        env_file = ".env"
```

Access settings via `get_settings()` — it returns a cached singleton.

## Cross-References

- See [API.md](API.md) for endpoint creation patterns.
- See [DATABASE.md](DATABASE.md) for model and migration workflows.
- See [TESTING.md](TESTING.md) for backend test patterns.
- See [CODING_STANDARDS.md](CODING_STANDARDS.md) for Python style rules.
