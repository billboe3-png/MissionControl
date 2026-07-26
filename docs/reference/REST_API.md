# Mission Control REST API Reference

Complete reference for the Mission Control API — 286 endpoints across 25 routers.

---

## Base URL

```
http://localhost:8000/api/v1
```

Production deployments use HTTPS with the configured domain. All examples below use the base path `/api/v1`.

---

## Authentication

All endpoints require authentication unless marked otherwise. Two authentication methods are supported — see [AUTHENTICATION.md](./AUTHENTICATION.md) for full details.

| Method | Header | Use Case |
|--------|--------|----------|
| JWT Bearer Token | `Authorization: Bearer <token>` | User sessions, browser clients |
| API Key | `X-API-Key: <key>` | Agent-to-server communication |

### Health & Version (No Auth)

```
GET /health
GET /version
```

These endpoints are unauthenticated and return service status.

---

## Response Format

All responses return JSON with a consistent envelope:

```json
{
  "status": "success",
  "data": { ... },
  "meta": {
    "page": 1,
    "per_page": 25,
    "total": 142,
    "total_pages": 6
  }
}
```

### Error Response

```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Email address is invalid",
    "details": [
      {
        "field": "email",
        "message": "Must be a valid email address"
      }
    ]
  }
}
```

---

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (successful delete) |
| 400 | Bad Request — invalid input |
| 401 | Unauthorized — missing or invalid credentials |
| 403 | Forbidden — insufficient permissions |
| 404 | Not Found — resource does not exist |
| 409 | Conflict — resource already exists |
| 422 | Unprocessable Entity — validation failed |
| 429 | Rate Limited — too many requests |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

---

## Rate Limiting

| Endpoint Category | Limit | Window |
|-------------------|-------|--------|
| Authentication (`/auth/*`) | 10 requests | 1 minute |
| All other endpoints | 60 requests | 1 minute |

Rate limit headers are included in every response:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 57
X-RateLimit-Reset: 1719398400
```

When rate limited, the response includes:

```json
{
  "status": "error",
  "error": {
    "code": "RATE_LIMITED",
    "message": "Rate limit exceeded. Retry after 12 seconds."
  }
}
```

Status code: `429 Too Many Requests`.

---

## Pagination

All list endpoints support pagination via query parameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `page` | 1 | Page number (1-indexed) |
| `per_page` | 25 | Items per page (max: 100) |

**Example:**

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/sites?page=2&per_page=50"
```

Response `meta` object:

```json
{
  "page": 2,
  "per_page": 50,
  "total": 142,
  "total_pages": 3
}
```

---

## Filtering & Sorting

List endpoints support filtering and sorting via query parameters:

| Parameter | Description |
|-----------|-------------|
| `search` | Full-text search across name, description fields |
| `sort` | Sort field (e.g., `created_at`, `name`) |
| `order` | Sort direction: `asc` (default) or `desc` |
| `status` | Filter by status: `active`, `inactive`, `pending` |

**Example:**

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/agents?status=active&sort=last_heartbeat&order=desc"
```

---

## API Reference by Router

### 1. Health Router

Unauthenticated endpoints for service health checks.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Basic health check |
| GET | `/health/detailed` | Detailed health with dependency checks |

```bash
curl http://localhost:8000/api/v1/health
```

```json
{
  "status": "success",
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "uptime": 86400,
    "database": "connected",
    "redis": "connected"
  }
}
```

---

### 2. Version Router

Unauthenticated version information.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/version` | Current version and build info |

```bash
curl http://localhost:8000/api/v1/version
```

```json
{
  "status": "success",
  "data": {
    "version": "1.0.0",
    "build": "20260726.1",
    "python": "3.12",
    "fastapi": "0.115.0"
  }
}
```

---

### 3. Auth Router

Authentication and session management. Rate limited to 10 requests/minute.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Authenticate with email/password |
| POST | `/auth/login/api-key` | Authenticate with API key |
| POST | `/auth/refresh` | Refresh an expiring JWT token |
| POST | `/auth/logout` | Invalidate current session |
| GET | `/auth/me` | Get current authenticated user |
| POST | `/auth/password/change` | Change password |
| POST | `/auth/password/reset` | Request password reset email |
| POST | `/auth/password/reset/confirm` | Confirm password reset with token |
| POST | `/auth/sessions` | List active sessions |
| DELETE | `/auth/sessions/{session_id}` | Revoke a specific session |

**Login:**

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "securepassword"}'
```

```json
{
  "status": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": "usr_a1b2c3d4",
      "email": "admin@example.com",
      "role": "admin"
    }
  }
}
```

**Refresh Token:**

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "eyJhbGciOiJIUzI1NiIs..."}'
```

See [AUTHENTICATION.md](./AUTHENTICATION.md) for the complete auth flow.

---

### 4. Users Router

User management and profile operations.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/users` | List all users |
| POST | `/users` | Create a new user |
| GET | `/users/{user_id}` | Get user by ID |
| PUT | `/users/{user_id}` | Update user |
| DELETE | `/users/{user_id}` | Delete user |
| GET | `/users/{user_id}/activity` | Get user activity log |
| PUT | `/users/{user_id}/role` | Change user role |
| POST | `/users/{user_id}/invite` | Send invitation email |

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/users?status=active
```

```json
{
  "status": "success",
  "data": [
    {
      "id": "usr_a1b2c3d4",
      "email": "admin@example.com",
      "name": "Admin User",
      "role": "admin",
      "status": "active",
      "last_login": "2026-07-26T10:30:00Z",
      "created_at": "2026-01-15T08:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "per_page": 25,
    "total": 12,
    "total_pages": 1
  }
}
```

---

### 5. Companies Router

Multi-tenant company management.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/companies` | List all companies |
| POST | `/companies` | Create a company |
| GET | `/companies/{company_id}` | Get company details |
| PUT | `/companies/{company_id}` | Update company |
| DELETE | `/companies/{company_id}` | Delete company |
| GET | `/companies/{company_id}/sites` | List company sites |
| GET | `/companies/{company_id}/users` | List company users |
| POST | `/companies/{company_id}/users` | Add user to company |

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/companies
```

---

### 6. Sites Router

Site/endpoint management within companies.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/sites` | List all sites |
| POST | `/sites` | Create a site |
| GET | `/sites/{site_id}` | Get site details |
| PUT | `/sites/{site_id}` | Update site |
| DELETE | `/sites/{site_id}` | Delete site |
| GET | `/sites/{site_id}/agents` | List agents at site |
| GET | `/sites/{site_id}/inventory` | List inventory at site |
| POST | `/sites/{site_id}/tags` | Add tags to site |
| DELETE | `/sites/{site_id}/tags/{tag}` | Remove tag from site |

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/sites?search=cape%20town
```

---

### 7. Agents Router

Agent registration, management, and command dispatch.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/agents` | List all agents |
| POST | `/agents` | Register a new agent |
| GET | `/agents/{agent_id}` | Get agent details |
| PUT | `/agents/{agent_id}` | Update agent config |
| DELETE | `/agents/{agent_id}` | Deregister agent |
| POST | `/agents/{agent_id}/heartbeat` | Agent heartbeat endpoint |
| GET | `/agents/{agent_id}/commands` | Get pending commands |
| POST | `/agents/{agent_id}/commands` | Queue a command for agent |
| GET | `/agents/{agent_id}/logs` | Get agent logs |
| POST | `/agents/{agent_id}/config` | Push config update to agent |

See [HEARTBEAT_API.md](./HEARTBEAT_API.md) for the heartbeat protocol.

---

### 8. Automation Router

Automation rules and workflow management.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/automation` | List automation rules |
| POST | `/automation` | Create automation rule |
| GET | `/automation/{rule_id}` | Get rule details |
| PUT | `/automation/{rule_id}` | Update rule |
| DELETE | `/automation/{rule_id}` | Delete rule |
| POST | `/automation/{rule_id}/enable` | Enable rule |
| POST | `/automation/{rule_id}/disable` | Disable rule |
| GET | `/automation/{rule_id}/runs` | Get rule execution history |
| POST | `/automation/{rule_id}/test` | Test rule with sample event |

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/automation
```

---

### 9. Remote Router

Remote access and tunnel management.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/remote` | List remote connections |
| POST | `/remote` | Create remote connection |
| GET | `/remote/{connection_id}` | Get connection details |
| DELETE | `/remote/{connection_id}` | Terminate connection |
| POST | `/remote/{connection_id}/connect` | Initiate connection |
| POST | `/remote/{connection_id}/disconnect` | Disconnect |
| GET | `/remote/{connection_id}/status` | Get connection status |
| PUT | `/remote/{connection_id}/config` | Update connection config |

---

### 10. Integrations Router

Third-party integration management.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/integrations` | List available integrations |
| POST | `/integrations` | Create integration |
| GET | `/integrations/{integration_id}` | Get integration details |
| PUT | `/integrations/{integration_id}` | Update integration |
| DELETE | `/integrations/{integration_id}` | Remove integration |
| POST | `/integrations/{integration_id}/test` | Test integration connection |
| GET | `/integrations/{integration_id}/logs` | Get integration logs |
| POST | `/integrations/{integration_id}/sync` | Trigger manual sync |

---

### 11. Settings Router

System and user settings.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/settings` | Get all settings |
| PUT | `/settings` | Update settings |
| GET | `/settings/public` | Get public settings (no auth) |
| PUT | `/settings/notifications` | Update notification preferences |
| PUT | `/settings/branding` | Update branding (admin only) |
| GET | `/settings/feature-flags` | Get feature flags |

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/settings
```

---

### 12. Inventory Router

Asset and inventory management.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/inventory` | List inventory items |
| POST | `/inventory` | Add inventory item |
| GET | `/inventory/{item_id}` | Get item details |
| PUT | `/inventory/{item_id}` | Update item |
| DELETE | `/inventory/{item_id}` | Remove item |
| GET | `/inventory/categories` | List categories |
| POST | `/inventory/categories` | Create category |
| GET | `/inventory/low-stock` | Get low-stock alerts |
| POST | `/inventory/bulk-import` | Bulk import items (CSV) |

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/inventory?category=networking&sort=name"
```

---

### 13. Dashboard Router

Dashboard data and widgets.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard` | Get dashboard summary |
| GET | `/dashboard/stats` | Get aggregate statistics |
| GET | `/dashboard/agent-status` | Get agent status overview |
| GET | `/dashboard/activity` | Get recent activity feed |
| GET | `/dashboard/alerts` | Get active alerts |
| GET | `/dashboard/charts/{chart_type}` | Get chart data |

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/dashboard/stats
```

```json
{
  "status": "success",
  "data": {
    "total_agents": 45,
    "agents_online": 42,
    "agents_offline": 3,
    "total_sites": 12,
    "active_alerts": 2,
    "commands_today": 156,
    "uptime_percentage": 99.7
  }
}
```

---

### 14. Plugins Router

Plugin management and marketplace.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/plugins` | List installed plugins |
| POST | `/plugins/install` | Install plugin |
| GET | `/plugins/{plugin_id}` | Get plugin details |
| DELETE | `/plugins/{plugin_id}` | Uninstall plugin |
| POST | `/plugins/{plugin_id}/enable` | Enable plugin |
| POST | `/plugins/{plugin_id}/disable` | Disable plugin |
| PUT | `/plugins/{plugin_id}/config` | Update plugin config |
| GET | `/plugins/marketplace` | Browse marketplace |
| POST | `/plugins/{plugin_id}/update` | Update plugin |

---

### 15. AI Router

AI features and model management.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/ai/models` | List available models |
| POST | `/ai/predict` | Run prediction |
| POST | `/ai/analyze` | Analyze data/logs |
| GET | `/ai/history` | Get AI interaction history |
| POST | `/ai/recommend` | Get recommendations |
| PUT | `/ai/settings` | Update AI settings |
| POST | `/ai/train` | Trigger model training |
| GET | `/ai/models/{model_id}` | Get model details |

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  http://localhost:8000/api/v1/ai/analyze \
  -d '{
    "type": "log_analysis",
    "data": {
      "agent_id": "agt_x1y2z3",
      "time_range": "24h"
    }
  }'
```

---

### 16. Commands Router

Command execution and management.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/commands` | List all commands |
| POST | `/commands` | Create/queue command |
| GET | `/commands/{command_id}` | Get command details |
| DELETE | `/commands/{command_id}` | Cancel command |
| POST | `/commands/{command_id}/retry` | Retry failed command |
| GET | `/commands/{command_id}/result` | Get command result |
| GET | `/commands/history` | Command history |

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  http://localhost:8000/api/v1/commands \
  -d '{
    "agent_id": "agt_x1y2z3",
    "type": "script",
    "payload": {
      "script": "uptime",
      "timeout": 30
    }
  }'
```

---

### 17. Logs Router

Log aggregation and search.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/logs` | Search logs |
| GET | `/logs/{log_id}` | Get specific log entry |
| GET | `/logs/stream` | SSE log stream |
| POST | `/logs/export` | Export logs (CSV/JSON) |
| GET | `/logs/sources` | List log sources |
| DELETE | `/logs/cleanup` | Cleanup old logs |

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/logs?level=error&source=agent&limit=100"
```

---

### 18. Audit Router

Audit trail and compliance logging.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/audit` | List audit entries |
| GET | `/audit/{entry_id}` | Get audit entry |
| GET | `/audit/export` | Export audit trail |
| GET | `/audit/user/{user_id}` | User activity audit |
| GET | `/audit/resource/{resource_type}/{resource_id}` | Resource audit |

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/audit?from=2026-07-01&to=2026-07-26&action=delete"
```

---

### 19. Storage Router

File and blob storage management.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/storage` | List stored files |
| POST | `/storage/upload` | Upload file |
| GET | `/storage/{file_id}` | Get file metadata |
| GET | `/storage/{file_id}/download` | Download file |
| DELETE | `/storage/{file_id}` | Delete file |
| POST | `/storage/{file_id}/share` | Create share link |
| GET | `/storage/usage` | Get storage usage stats |

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -F "file=@backup.tar.gz" \
  -F "category=backups" \
  http://localhost:8000/api/v1/storage/upload
```

---

### 20. Tasks Router

Task scheduling and management.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/tasks` | List tasks |
| POST | `/tasks` | Create task |
| GET | `/tasks/{task_id}` | Get task details |
| PUT | `/tasks/{task_id}` | Update task |
| DELETE | `/tasks/{task_id}` | Delete task |
| POST | `/tasks/{task_id}/run` | Trigger task immediately |
| POST | `/tasks/{task_id}/cancel` | Cancel running task |
| GET | `/tasks/{task_id}/runs` | Get task run history |

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  http://localhost:8000/api/v1/tasks \
  -d '{
    "name": "Daily Backup",
    "type": "scheduled",
    "cron": "0 2 * * *",
    "command": {
      "agent_id": "agt_x1y2z3",
      "type": "script",
      "payload": {"script": "backup.sh"}
    }
  }'
```

---

### 21. Notifications Router

Notification management and delivery.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/notifications` | List notifications |
| PUT | `/notifications/{notification_id}/read` | Mark as read |
| PUT | `/notifications/read-all` | Mark all as read |
| DELETE | `/notifications/{notification_id}` | Delete notification |
| GET | `/notifications/preferences` | Get notification prefs |
| PUT | `/notifications/preferences` | Update notification prefs |
| POST | `/notifications/test` | Send test notification |

---

### 22. Reports Router

Report generation and retrieval.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/reports` | List available reports |
| POST | `/reports/generate` | Generate a report |
| GET | `/reports/{report_id}` | Get report details |
| GET | `/reports/{report_id}/download` | Download report |
| DELETE | `/reports/{report_id}` | Delete report |
| GET | `/reports/templates` | List report templates |
| POST | `/reports/templates` | Create report template |

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  http://localhost:8000/api/v1/reports/generate \
  -d '{
    "template": "agent_summary",
    "format": "pdf",
    "date_range": {
      "from": "2026-07-01",
      "to": "2026-07-26"
    }
  }'
```

---

### 23. Webhooks Router

Outbound webhook management. See [WEBHOOKS.md](./WEBHOOKS.md) for the complete webhook guide.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/webhooks` | List webhooks |
| POST | `/webhooks` | Create webhook |
| GET | `/webhooks/{webhook_id}` | Get webhook details |
| PUT | `/webhooks/{webhook_id}` | Update webhook |
| DELETE | `/webhooks/{webhook_id}` | Delete webhook |
| POST | `/webhooks/{webhook_id}/test` | Send test payload |
| GET | `/webhooks/{webhook_id}/logs` | Get delivery logs |
| POST | `/webhooks/{webhook_id}/retry/{delivery_id}` | Retry delivery |

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  http://localhost:8000/api/v1/webhooks \
  -d '{
    "url": "https://hooks.example.com/mission-control",
    "events": ["agent.offline", "alert.created"],
    "secret": "whsec_your_signing_secret"
  }'
```

---

### 24. Git Router

Git integration and repository management.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/git/repositories` | List connected repositories |
| POST | `/git/repositories` | Connect repository |
| GET | `/git/repositories/{repo_id}` | Get repository details |
| DELETE | `/git/repositories/{repo_id}` | Disconnect repository |
| GET | `/git/repositories/{repo_id}/commits` | List commits |
| GET | `/git/repositories/{repo_id}/branches` | List branches |
| POST | `/git/repositories/{repo_id}/sync` | Trigger sync |
| GET | `/git/repositories/{repo_id}/files` | Browse repository files |

---

### 25. Dashboard (Extended)

Additional dashboard endpoints for real-time data.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard/realtime` | WebSocket upgrade for realtime data |
| GET | `/dashboard/kpis` | Get key performance indicators |
| GET | `/dashboard/trends` | Get trend data |
| POST | `/dashboard/widgets` | Add custom widget |
| PUT | `/dashboard/widgets/{widget_id}` | Update widget |
| DELETE | `/dashboard/widgets/{widget_id}` | Remove widget |

---

## Common Request Headers

```
Authorization: Bearer <jwt_token>
Content-Type: application/json
Accept: application/json
X-API-Key: <api_key>          # Alternative auth for agents
X-Request-ID: <uuid>          # Optional, for request tracing
```

---

## Common Request Body Fields

Timestamps use ISO 8601 format: `2026-07-26T10:30:00Z`

All IDs use prefixed format: `usr_`, `agt_`, `site_`, `cmd_`, `wh_`, etc.

Boolean fields use JSON `true`/`false`, never strings.

---

## SDK & Client Libraries

The API is generated from OpenAPI specs. Access the interactive docs at:

```
http://localhost:8000/docs      # Swagger UI
http://localhost:8000/redoc     # ReDoc
```

---

## Related Documentation

- [AUTHENTICATION.md](./AUTHENTICATION.md) — Auth flows and token management
- [WEBHOOKS.md](./WEBHOOKS.md) — Webhook configuration and events
- [HEARTBEAT_API.md](./HEARTBEAT_API.md) — Agent heartbeat protocol
- [DEPLOYMENT_DOCKER.md](./DEPLOYMENT_DOCKER.md) — Docker deployment
