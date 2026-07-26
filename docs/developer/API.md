# API Development

Mission Control's API is built with FastAPI and follows consistent patterns across all 25 routers.

## Base URL

All endpoints are prefixed with `/api/v1`:

```
http://localhost:8000/api/v1/
```

## Creating a New Router

### 1. Create the router module

Create a new file in `backend/app/routers/`:

```python
# backend/app/routers/webhook.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth_dependency import get_current_user
from app.db.database import get_db
from app.models.db.user import User
from app.schemas.webhook import WebhookCreate, WebhookResponse, WebhookUpdate
from app.services.webhook_service import WebhookService

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.get("", response_model=list[WebhookResponse])
def list_webhooks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[WebhookResponse]:
    webhooks = WebhookService.list_by_company(db, current_user.company_id)
    return webhooks


@router.get("/{webhook_id}", response_model=WebhookResponse)
def get_webhook(
    webhook_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WebhookResponse:
    webhook = WebhookService.get_by_id(db, webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    if webhook.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return webhook


@router.post("", response_model=WebhookResponse, status_code=201)
def create_webhook(
    webhook_in: WebhookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WebhookResponse:
    webhook = WebhookService.create(
        db, webhook_in, company_id=current_user.company_id, created_by=current_user.id
    )
    return webhook


@router.put("/{webhook_id}", response_model=WebhookResponse)
def update_webhook(
    webhook_id: int,
    webhook_in: WebhookUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WebhookResponse:
    webhook = WebhookService.get_by_id(db, webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    if webhook.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    updated = WebhookService.update(db, webhook, webhook_in)
    return updated


@router.delete("/{webhook_id}", status_code=204)
def delete_webhook(
    webhook_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    webhook = WebhookService.get_by_id(db, webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    if webhook.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    WebhookService.delete(db, webhook)
```

### 2. Register the router in `main.py`

```python
from app.routers import webhook

app.include_router(webhook.router, prefix="/api/v1")
```

### 3. Create the service

```python
# backend/app/services/webhook_service.py
from sqlalchemy.orm import Session
from app.models.db.webhook import Webhook
from app.repositories.webhook_repository import WebhookRepository
from app.schemas.webhook import WebhookCreate, WebhookUpdate


class WebhookService:
    @staticmethod
    def list_by_company(db: Session, company_id: int) -> list[Webhook]:
        return WebhookRepository.get_by_company(db, company_id)

    @staticmethod
    def get_by_id(db: Session, webhook_id: int) -> Webhook | None:
        return WebhookRepository.get_by_id(db, webhook_id)

    @staticmethod
    def create(
        db: Session,
        webhook_in: WebhookCreate,
        company_id: int,
        created_by: int,
    ) -> Webhook:
        return WebhookRepository.create(
            db, obj_in=webhook_in, company_id=company_id, created_by=created_by
        )

    @staticmethod
    def update(db: Session, webhook: Webhook, webhook_in: WebhookUpdate) -> Webhook:
        return WebhookRepository.update(db, db_obj=webhook, obj_in=webhook_in)

    @staticmethod
    def delete(db: Session, webhook: Webhook) -> None:
        WebhookRepository.delete(db, id=webhook.id)
```

### 4. Create the repository

```python
# backend/app/repositories/webhook_repository.py
from sqlalchemy.orm import Session
from app.models.db.webhook import Webhook
from app.schemas.webhook import WebhookCreate, WebhookUpdate


class WebhookRepository:
    @staticmethod
    def get_by_company(db: Session, company_id: int) -> list[Webhook]:
        return db.query(Webhook).filter(Webhook.company_id == company_id).all()

    @staticmethod
    def get_by_id(db: Session, webhook_id: int) -> Webhook | None:
        return db.query(Webhook).filter(Webhook.id == webhook_id).first()

    @staticmethod
    def create(
        db: Session,
        *,
        obj_in: WebhookCreate,
        company_id: int,
        created_by: int,
    ) -> Webhook:
        webhook = Webhook(
            **obj_in.model_dump(),
            company_id=company_id,
            created_by=created_by,
        )
        db.add(webhook)
        db.commit()
        db.refresh(webhook)
        return webhook

    @staticmethod
    def update(
        db: Session,
        *,
        db_obj: Webhook,
        obj_in: WebhookUpdate,
    ) -> Webhook:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def delete(db: Session, *, id: int) -> None:
        obj = db.query(Webhook).filter(Webhook.id == id).first()
        if obj:
            db.delete(obj)
            db.commit()
```

## Request/Response Patterns

### GET — List resources

```
GET /api/v1/remote/hosts?search=web
```

Response: `200 OK` with array of objects.

### GET — Single resource

```
GET /api/v1/remote/hosts/42
```

Response: `200 OK` with single object, or `404 Not Found`.

### POST — Create resource

```
POST /api/v1/remote/hosts
Content-Type: application/json

{
  "name": "Web Server",
  "hostname": "192.168.1.100",
  "protocol": "ssh",
  "port": 22
}
```

Response: `201 Created` with the created object.

### PUT — Update resource

```
PUT /api/v1/remote/hosts/42
Content-Type: application/json

{
  "name": "Production Web Server"
}
```

Response: `200 OK` with the updated object.

### DELETE — Remove resource

```
DELETE /api/v1/remote/hosts/42
```

Response: `204 No Content`.

## Authentication

All protected endpoints require a `Bearer` token in the `Authorization` header:

```
Authorization: Bearer <jwt-token>
```

Use the `get_current_user` dependency:

```python
from app.core.auth_dependency import get_current_user

@router.get("/protected-endpoint")
def my_endpoint(
    current_user: User = Depends(get_current_user),
) -> ...:
    ...
```

The dependency validates the JWT, loads the user, and raises `401 Unauthorized` if invalid.

### Agent Authentication

Agent-to-backend communication uses API key authentication via the `X-Agent-API-Key` header. This is handled separately from user JWT auth.

## Error Handling

### HTTP Exceptions

Raise `HTTPException` with appropriate status codes:

```python
from fastapi import HTTPException

# Not found
raise HTTPException(status_code=404, detail="Host not found")

# Forbidden
raise HTTPException(status_code=403, detail="Access denied")

# Validation error
raise HTTPException(status_code=400, detail="Invalid hostname format")

# Conflict
raise HTTPException(status_code=409, detail="Host already exists")
```

### Error Response Format

FastAPI returns errors in a consistent format:

```json
{
  "detail": "Host not found"
}
```

### Rate Limiting

When rate limited, the response includes:

```json
{
  "detail": "Rate limit exceeded. Try again later."
}
```

With headers:
- `X-RateLimit-Limit`: Maximum requests per window
- `X-RateLimit-Remaining`: Requests remaining
- `Retry-After`: Seconds until the window resets

## OpenAPI Documentation

FastAPI generates interactive API documentation automatically:

| URL | Format |
|-----|--------|
| `/api/docs` | Swagger UI |
| `/api/redoc` | ReDoc |
| `/api/openapi.json` | OpenAPI JSON schema |

Use the `tags` parameter on routers to group endpoints in the docs:

```python
router = APIRouter(prefix="/remote", tags=["Remote Operations"])
```

## Health and Version Endpoints

These endpoints are exempt from rate limiting:

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/health/live` | Liveness probe |
| `GET /api/v1/health/ready` | Readiness probe (checks DB + Redis) |
| `GET /api/v1/version` | Version info |
| `GET /api/v1` | API root (name, status, version) |

## Company Scoping

Multi-tenant endpoints must filter by `current_user.company_id`:

```python
@router.get("/hosts")
def list_hosts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[HostResponse]:
    hosts = RemoteService.list_hosts(db, company_id=current_user.company_id)
    return hosts
```

Global admins can access all companies. Other roles are scoped to their company.

## Cross-References

- See [BACKEND.md](BACKEND.md) for the full architecture.
- See [DATABASE.md](DATABASE.md) for model and schema creation.
- See [API.md](../architecture/API.md) for architecture-level API design.
- See [API-Standards.md](../architecture/API-Standards.md) for detailed API conventions.
