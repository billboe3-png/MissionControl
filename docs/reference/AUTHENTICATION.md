# Mission Control Authentication Guide

Complete reference for JWT token and API key authentication flows.

---

## Overview

Mission Control supports two authentication methods:

| Method | Token Type | Audience | Lifetime |
|--------|-----------|----------|----------|
| JWT Bearer Token | `access_token` | User sessions | 1 hour |
| JWT Refresh Token | `refresh_token` | Token renewal | 30 days |
| API Key | `X-API-Key` header | Agent-to-server | No expiry |

---

## JWT Token Flow

### 1. Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "securepassword"
  }'
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c3JfYTFiMmMzZDQiLCJlbWFpbCI6ImFkbWluQGV4YW1wbGUuY29tIiwicm9sZSI6ImFkbWluIiwidG9rZW5fdHlwZSI6ImFjY2VzcyIsImlhdCI6MTcxOTM5ODQwMCwiZXhwIjoxNzE5Mzk4NDAwfQ...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c3JfYTFiMmMzZDQiLCJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImlhdCI6MTcxOTM5ODQwMCwiZXhwIjoxNzIxOTkwNDAwfQ...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": "usr_a1b2c3d4",
      "email": "admin@example.com",
      "name": "Admin User",
      "role": "admin"
    }
  }
}
```

### 2. Use the Token

Include the access token in the `Authorization` header for all subsequent requests:

```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  http://localhost:8000/api/v1/dashboard/stats
```

### 3. Token Refresh

When the access token expires (after 1 hour), use the refresh token to obtain a new pair:

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
  }'
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...(new)",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...(new)",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

Refresh tokens are single-use. The previous refresh token is invalidated when a new one is issued.

### 4. Logout

```bash
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

This invalidates the current access token and refresh token pair.

---

## API Key Flow

API keys are used by agents for automated server communication. They bypass JWT entirely.

### Generating an API Key

API keys are generated per-agent during registration:

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  http://localhost:8000/api/v1/agents \
  -d '{
    "name": "Server Agent 01",
    "site_id": "site_x1y2z3",
    "type": "server"
  }'
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "id": "agt_x1y2z3",
    "name": "Server Agent 01",
    "api_key": "mc_agent_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
    "status": "registered",
    "created_at": "2026-07-26T10:00:00Z"
  }
}
```

Store the `api_key` securely. It is only shown once at creation time.

### Using an API Key

```bash
curl -H "X-API-Key: mc_agent_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6" \
  http://localhost:8000/api/v1/agents/agt_x1y2z3/heartbeat
```

### Agent Configuration

Configure the agent to use the API key in `~/.config/mission-control-agent/config.yaml`:

```yaml
server:
  url: "https://your-domain.com"
  api_key: "mc_agent_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
  verify_ssl: true

heartbeat:
  interval: 30
  timeout: 10
```

---

## JWT Token Structure

### Access Token Payload

```json
{
  "sub": "usr_a1b2c3d4",
  "email": "admin@example.com",
  "role": "admin",
  "token_type": "access",
  "company_id": "comp_x1y2z3",
  "iat": 1719398400,
  "exp": 1719402000
}
```

### Refresh Token Payload

```json
{
  "sub": "usr_a1b2c3d4",
  "token_type": "refresh",
  "iat": 1719398400,
  "exp": 1721990400
}
```

### Token Claims

| Claim | Description |
|-------|-------------|
| `sub` | Subject — user ID |
| `email` | User email address |
| `role` | User role (`admin`, `manager`, `operator`, `viewer`) |
| `token_type` | `access` or `refresh` |
| `company_id` | Company scope (multi-tenant) |
| `iat` | Issued at (Unix timestamp) |
| `exp` | Expiration (Unix timestamp) |

---

## Role-Based Access Control

### Roles

| Role | Description |
|------|-------------|
| `admin` | Full system access. Manage users, settings, billing. |
| `manager` | Manage agents, sites, commands. Cannot manage users or billing. |
| `operator` | Execute commands, view dashboards, acknowledge alerts. |
| `viewer` | Read-only access to dashboards and reports. |

### Permission Matrix

| Resource | Admin | Manager | Operator | Viewer |
|----------|-------|---------|----------|--------|
| Users | CRUD | Read | — | — |
| Companies | CRUD | Read | — | — |
| Sites | CRUD | CRUD | Read | Read |
| Agents | CRUD | CRUD | Read | Read |
| Commands | CRUD | CRUD | Create/Read | Read |
| Settings | CRUD | Read | — | — |
| Plugins | CRUD | CRUD | — | — |
| Webhooks | CRUD | CRUD | Read | Read |
| Reports | CRUD | CRUD | Create/Read | Read |
| Logs | CRUD | Read | Read | Read |
| Audit | Read | Read | — | — |

---

## Session Management

### List Active Sessions

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/auth/sessions
```

```json
{
  "status": "success",
  "data": [
    {
      "session_id": "sess_a1b2c3d4",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0 ...",
      "created_at": "2026-07-26T10:00:00Z",
      "last_active": "2026-07-26T10:30:00Z",
      "current": true
    },
    {
      "session_id": "sess_e5f6g7h8",
      "ip_address": "10.0.0.50",
      "user_agent": "curl/7.88",
      "created_at": "2026-07-25T14:00:00Z",
      "last_active": "2026-07-25T16:00:00Z",
      "current": false
    }
  ]
}
```

### Revoke a Session

```bash
curl -X DELETE -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/auth/sessions/sess_e5f6g7h8
```

---

## Password Management

### Change Password (Authenticated)

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  http://localhost:8000/api/v1/auth/password/change \
  -d '{
    "current_password": "oldpassword",
    "new_password": "newsecurepassword"
  }'
```

### Request Password Reset

```bash
curl -X POST http://localhost:8000/api/v1/auth/password/reset \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com"}'
```

Returns 200 regardless of whether the email exists (prevents user enumeration).

### Confirm Password Reset

```bash
curl -X POST http://localhost:8000/api/v1/auth/password/reset/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "token": "reset_token_from_email",
    "new_password": "newsecurepassword"
  }'
```

---

## Error Handling

### 401 Unauthorized

```json
{
  "status": "error",
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid or expired token"
  }
}
```

Causes:
- Missing `Authorization` header
- Expired access token
- Invalid token signature
- Revoked token

### 403 Forbidden

```json
{
  "status": "error",
  "error": {
    "code": "FORBIDDEN",
    "message": "Insufficient permissions for this action"
  }
}
```

### 429 Rate Limited (Auth Endpoints)

```json
{
  "status": "error",
  "error": {
    "code": "RATE_LIMITED",
    "message": "Too many authentication attempts. Try again in 45 seconds."
  }
}
```

Auth endpoints are rate limited to 10 requests per minute.

---

## Frontend Integration

### Vite (Port 3000) Auth Flow

```javascript
// Store token after login
const response = await fetch('/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
});
const { data } = await response.json();
localStorage.setItem('access_token', data.access_token);
localStorage.setItem('refresh_token', data.refresh_token);

// Use token in requests
fetch('/api/v1/dashboard/stats', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
  }
});

// Auto-refresh on 401
async function fetchWithAuth(url, options = {}) {
  let token = localStorage.getItem('access_token');
  let response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`
    }
  });

  if (response.status === 401) {
    const refreshResponse = await fetch('/api/v1/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        refresh_token: localStorage.getItem('refresh_token')
      })
    });

    if (refreshResponse.ok) {
      const { data } = await refreshResponse.json();
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);

      response = await fetch(url, {
        ...options,
        headers: {
          ...options.headers,
          'Authorization': `Bearer ${data.access_token}`
        }
      });
    } else {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
    }
  }

  return response;
}
```

---

## Python Agent Auth Example

```python
import requests

class MissionControlAuth:
    def __init__(self, server_url: str, api_key: str):
        self.server_url = server_url
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers["X-API-Key"] = api_key

    def heartbeat(self, payload: dict) -> dict:
        response = self.session.post(
            f"{self.server_url}/api/v1/agents/heartbeat",
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        return response.json()

    def get_commands(self, agent_id: str) -> list:
        response = self.session.get(
            f"{self.server_url}/api/v1/agents/{agent_id}/commands",
            timeout=10
        )
        response.raise_for_status()
        return response.json()["data"]
```

---

## Security Best Practices

1. **Never expose tokens in logs or error messages.**
2. **Store tokens in memory or httpOnly cookies**, not localStorage in production.
3. **Rotate API keys** periodically. Delete and recreate agent keys on a schedule.
4. **Use HTTPS** in all production deployments to prevent token interception.
5. **Set short access token lifetimes** (default: 1 hour) and rely on refresh tokens.
6. **Revoke sessions** when users change devices or leave the organization.
7. **Monitor audit logs** for unusual authentication patterns.

---

## Related Documentation

- [REST_API.md](./REST_API.md) — Complete API endpoint reference
- [WEBHOOKS.md](./WEBHOOKS.md) — Webhook HMAC signing
- [HEARTBEAT_API.md](./HEARTBEAT_API.md) — Agent heartbeat with API keys
- [DEPLOYMENT_DOCKER.md](./DEPLOYMENT_DOCKER.md) — Environment variables for JWT secrets
