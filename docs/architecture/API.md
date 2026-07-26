# Mission Control — API

**Version:** 3.0.0

---

## Overview

Mission Control exposes a RESTful API with 286 endpoints across 25 routers. The API is the single interface for all clients: web dashboard, agents, and integrations.

---

## 1. API Principles

| Principle | Description |
|-----------|-------------|
| **RESTful** | Standard HTTP methods (GET, POST, PUT, DELETE, PATCH) |
| **Versioned** | All endpoints prefixed with `/api/v1/` |
| **Authenticated** | JWT for web users, API keys for agents |
| **Documented** | OpenAPI/Swagger at `/api/docs` |
| **Rate-limited** | Per-IP sliding window (60 req/min default) |

---

## 2. Base URL

```
https://<host>:8000/api/v1
```

### Documentation

```
Swagger UI:  https://<host>:8000/api/docs
ReDoc:       https://<host>:8000/api/redoc
OpenAPI JSON: https://<host>:8000/api/openapi.json
```

---

## 3. Authentication

### JWT Token (Web Users)

```
Authorization: Bearer <access_token>
```

**Login:**

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password"
}

Response:
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### API Key (Agents)

```
X-Agent-API-Key: mc_agent_<64_hex_chars>
```

---

## 4. Routers

| Router | Prefix | Endpoints | Description |
|--------|--------|-----------|-------------|
| `auth` | `/auth` | 5 | Login, refresh, register |
| `agent` | `/agents` | 12 | Agent CRUD, heartbeat, inventory |
| `agent_token` | `/agents/tokens` | 4 | Registration tokens |
| `agent_remote_target` | `/agents/{id}/remote-targets` | 5 | Remote target CRUD |
| `automation` | `/automation` | 42 | Playbooks, executions, approvals |
| `dashboard` | `/dashboard` | 1 | Dashboard aggregation |
| `health` | `/health` | 3 | Liveness, readiness, subsystems |
| `version` | `/version` | 1 | Version information |
| `remote` | `/remote` | 25 | Hosts, credentials, commands |
| `plugin` | `/plugins` | 10 | Plugin management |
| `identity` | `/identity` | 8 | AD, M365 integration |
| `hyperv` | `/hyperv` | 12 | Hyper-V VM management |
| `proxmox` | `/proxmox` | 15 | Proxmox VE management |
| `veeam` | `/veeam` | 10 | Veeam backup management |
| `zabbix` | `/zabbix` | 12 | Zabbix monitoring |
| `ai` | `/ai` | 8 | AI operations |
| `integration` | `/integrations` | 6 | Integration profiles |
| `company` | `/companies` | 4 | Tenant management |
| `site` | `/sites` | 5 | Site management |
| `projects` | `/projects` | 5 | Project CRUD |
| `tasks` | `/tasks` | 5 | Task CRUD |
| `notes` | `/notes` | 4 | Note CRUD |
| `parking_lot` | `/parking-lot` | 4 | Backlog items |
| `resume` | `/resume` | 3 | Resume context |
| `setup` | `/setup` | 2 | First-run wizard |

**Total: 286 endpoints**

---

## 5. REST Conventions

### Resource Naming

```
GET    /api/v1/agents           # List agents
GET    /api/v1/agents/{id}      # Get agent
POST   /api/v1/agents           # Create agent
PUT    /api/v1/agents/{id}      # Update agent
DELETE /api/v1/agents/{id}      # Delete agent
```

### Nested Resources

```
GET    /api/v1/agents/{id}/commands           # Agent commands
POST   /api/v1/agents/{id}/commands           # Queue command
GET    /api/v1/agents/{id}/remote-targets     # Agent remote targets
```

### Query Parameters

```
GET /api/v1/agents?status=online&search=web
GET /api/v1/automation/executions?status=running&page=1&limit=20
```

---

## 6. Response Format

### Success

```json
{
  "id": 1,
  "name": "Web Server 01",
  "status": "online",
  "health": "healthy",
  "created_at": "2026-01-15T10:30:00Z"
}
```

### List

```json
{
  "count": 25,
  "items": [...]
}
```

### Error

```json
{
  "detail": "Agent not found"
}
```

### Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "Field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## 7. HTTP Status Codes

| Code | Meaning |
|------|---------|
| `200` | Success |
| `201` | Created |
| `204` | No Content (deleted) |
| `400` | Bad Request (validation) |
| `401` | Unauthorized (auth failed) |
| `403` | Forbidden (insufficient permissions) |
| `404` | Not Found |
| `409` | Conflict (duplicate) |
| `422` | Unprocessable Entity |
| `429` | Too Many Requests (rate limit) |
| `500` | Internal Server Error |

---

## 8. Rate Limiting

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/api/v1/auth/login` | 5 requests | 60 seconds |
| All other endpoints | 60 requests | 60 seconds |
| Agent heartbeat | Exempt | — |
| Health check | Exempt | — |

**Response Headers:**

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
```

**When exceeded (429):**

```
Retry-After: 60
```

---

## 9. Versioning

All endpoints are prefixed with `/api/v1/`. Future versions will use `/api/v2/`.

### Version Endpoint

```bash
GET /api/v1/version

Response:
{
  "version": "3.0.0",
  "edition": "community",
  "build": "3.0.0",
  "db_schema_version": "3.0.0",
  "min_agent_version": "3.0.0",
  "plugin_sdk_version": "3.0.0",
  "uptime_seconds": 12345.6
}
```

---

## 10. CORS

```python
allow_origins = ["http://localhost", "http://localhost:3000"]
allow_credentials = True
allow_methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
allow_headers = ["Authorization", "Content-Type", "X-Agent-API-Key"]
```

---

## 11. OpenAPI Schema

The full API schema is available at:

```
GET /api/v1/openapi.json
```

This provides machine-readable API documentation for code generation, testing, and client libraries.
