# Mission Control — Security

**Version:** 3.0.0

---

## Overview

Mission Control implements defense-in-depth security across authentication, authorization, encryption, and transport.

---

## 1. Authentication

### JWT Tokens

The primary authentication mechanism for web users.

| Property | Value |
|----------|-------|
| Algorithm | HS256 |
| Access token lifetime | Configurable (default: 60 minutes) |
| Refresh token lifetime | Configurable (default: 7 days) |
| Secret | `MISSIONCONTROL_SECRET_KEY` (Fernet key) |
| Claims | `user_id`, `company_id`, `role`, `exp` |

**Flow:**

```
POST /api/v1/auth/login
  → Validate credentials (bcrypt)
  → Generate access + refresh tokens
  → Return tokens

GET /api/v1/agents (with token)
  → Validate JWT signature
  → Check expiry
  → Extract user_id, company_id
  → Inject into request state
```

### API Keys

Used for agent-to-server authentication.

| Property | Value |
|----------|-------|
| Format | `mc_agent_<64_hex_chars>` |
| Storage | SHA-256 hash in database |
| Authentication | `X-Agent-API-Key` header |
| Rotation | Supported via re-registration |

**Flow:**

```
Agent registers → Server generates API key → Agent stores key
Agent heartbeat → Server validates API key hash → Process heartbeat
```

### First-Run Setup

The setup wizard (`/api/v1/setup`) creates the initial admin user and company. It is only available when no users exist.

---

## 2. Authorization

### Role-Based Access Control (RBAC)

| Role | Description |
|------|-------------|
| `admin` | Full access to all features |
| `operator` | Access to infrastructure, automation, agents |
| `viewer` | Read-only access to dashboard and reports |

### Tenant Isolation

Every database query is scoped to the authenticated user's `company_id`.

```
Company A → Sites A1, A2 → Users A-admin, A-operator
Company B → Sites B1, B2 → Users B-admin, B-operator

User A-admin can only see:
  - Company A data
  - Site A1, A2 data
  - Users in Company A
```

### Agent Scoping

Agents are scoped to sites. An agent belonging to Site A cannot access data from Site B.

---

## 3. Transport Security

### TLS

| Environment | TLS | Notes |
|-------------|-----|-------|
| Development | Optional | `http://localhost` |
| Production | Required | HTTPS with valid certificate |
| Agent → Server | Required | TLS for all agent communication |

### CORS

Configured via `BACKEND_CORS_ORIGINS`:

```
allow_origins = ["http://localhost", "http://localhost:3000"]
allow_credentials = True
allow_methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
allow_headers = ["Authorization", "Content-Type", "X-Agent-API-Key"]
```

---

## 4. Encryption

### At Rest

Fernet symmetric encryption (AES-128-CBC) for sensitive data.

| Data | Storage |
|------|---------|
| Passwords | bcrypt hash |
| API keys | SHA-256 hash |
| Credential profiles | Fernet encrypted |
| SSH private keys | Fernet encrypted |
| Integration secrets | Fernet encrypted |
| AD/M365 passwords | Fernet encrypted |

**Key:** `MISSIONCONTROL_SECRET_KEY` (Fernet key, 32 bytes base64)

### Credential Cipher

```python
from app.core.security import CredentialCipher

cipher = CredentialCipher(settings.missioncontrol_secret_key)

# Encrypt
encrypted = cipher.encrypt("my-secret-password")

# Decrypt
decrypted = cipher.decrypt(encrypted)
```

---

## 5. Secrets Management

### Environment Variables

Secrets are stored in environment variables, not in code:

```bash
MISSIONCONTROL_SECRET_KEY=<fernet-key>
POSTGRES_PASSWORD=<password>
ZABBIX_PASSWORD=<password>
AD_PASSWORD=<password>
M365_CLIENT_SECRET=<secret>
```

### .env File

The `.env` file should never be committed to version control. `.env.example` provides a template.

### Docker Secrets (Enterprise)

For production deployments, use Docker secrets or a vault:

```yaml
secrets:
  missioncontrol_secret_key:
    external: true
  postgres_password:
    external: true
```

---

## 6. Rate Limiting

In-memory sliding window rate limiting per IP address.

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/api/v1/auth/login` | 5 requests/min | 60s |
| All other endpoints | 60 requests/min | 60s |
| Agent heartbeat | Exempt | — |
| Health check | Exempt | — |

**Response headers:**

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
Retry-After: 60  (when exceeded)
```

---

## 7. Agent Trust Model

### Registration

1. Admin creates a registration token
2. Agent uses token to register
3. Server generates API key
4. Agent stores API key for future authentication

### Authentication

Every agent request includes the API key:

```
X-Agent-API-Key: mc_agent_...
```

The server validates the key hash against the stored value.

### Trust Boundaries

| Trust Level | Entity | Access |
|-------------|--------|--------|
| High | Server | Full database access |
| Medium | Agent | Own data, remote targets |
| Low | API consumer | Scoped by role and tenant |

---

## 8. Audit Trail

All significant actions are recorded in the `audit_trail` table.

| Action | Recorded |
|--------|----------|
| Playbook execution | User, start/end time, result |
| Approval request | Requester, approver, decision |
| Agent registration | Agent name, hostname, timestamp |
| User login | User, IP, timestamp |
| Configuration change | User, field, old/new value |

---

## 9. Security Best Practices

### For Deployment

1. Use TLS in production (never expose HTTP)
2. Generate a strong `MISSIONCONTROL_SECRET_KEY`
3. Use unique database passwords
4. Restrict database access to internal network
5. Enable firewall rules (only expose必要 ports)
6. Regular database backups

### For Development

1. Never commit `.env` files
2. Use `http://localhost` for CORS
3. Use strong secret keys even in development
4. Run security scans before deployment

### For Agents

1. Store API keys securely (file permissions, not environment variables)
2. Use TLS for server communication
3. Run agents with minimal privileges
4. Monitor agent registration events
