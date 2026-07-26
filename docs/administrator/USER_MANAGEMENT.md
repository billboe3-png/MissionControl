# User Management

**Version:** 3.0.0

---

## First-Run Setup Wizard

When Mission Control is started for the first time with an empty database, the setup wizard is triggered. Navigate to `http://localhost:3000` (or your configured URL) and you will be guided through:

1. Creating the initial **administrator** account.
2. Setting the company name for the default tenant.
3. Configuring the primary site.

The first user created via the wizard is automatically assigned the `admin` role. See [Company and Site Management](COMPANY_AND_SITE_MANAGEMENT.md) for tenant configuration.

---

## User CRUD

### Creating Users

**Via Dashboard:** Navigate to **Settings → Users → Add User**.

**Via API:**

```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "jdoe",
    "email": "jdoe@example.com",
    "full_name": "Jane Doe",
    "password": "SecureP@ss123",
    "role": "operator",
    "company_id": 1,
    "site_ids": [1, 2]
  }'
```

### Listing Users

```bash
curl http://localhost:8000/api/v1/users \
  -H "Authorization: Bearer <admin-token>"
```

### Updating Users

```bash
curl -X PUT http://localhost:8000/api/v1/users/2 \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{"role": "admin", "is_active": true}'
```

### Deleting Users

```bash
curl -X DELETE http://localhost:8000/api/v1/users/2 \
  -H "Authorization: Bearer <admin-token>"
```

Deleting a user is a soft delete — the account is deactivated and can be reactivated by an administrator.

---

## Roles

Mission Control defines three built-in roles:

| Role | Description |
|---|---|
| `admin` | Full system access. Can manage users, roles, companies, sites, agents, plugins, and system configuration. |
| `operator` | Can manage agents, execute remote commands, manage plugins, and view dashboards. Cannot manage users or system settings. |
| `viewer` | Read-only access. Can view dashboards, agent status, logs, and reports. Cannot execute commands or modify configurations. |

Enterprise edition supports custom roles with granular permissions. See [Security Hardening](SECURITY_HARDENING.md) for RBAC details.

---

## RBAC Permissions Matrix

| Permission | Admin | Operator | Viewer |
|---|---|---|---|
| Manage users | Yes | No | No |
| Manage companies/sites | Yes | No | No |
| Manage agents | Yes | Yes | No |
| Execute remote commands | Yes | Yes | No |
| Manage plugins | Yes | Yes | No |
| Manage API keys | Yes | Yes | No |
| View dashboards | Yes | Yes | Yes |
| View logs | Yes | Yes | Yes |
| View reports | Yes | Yes | Yes |
| System configuration | Yes | No | No |
| Backup/restore | Yes | No | No |

---

## Password Policies

Mission Control enforces the following password requirements:

- **Minimum length:** 8 characters
- **Maximum length:** 128 characters
- **Required character classes:** At least 3 of the following:
  - Uppercase letters (A-Z)
  - Lowercase letters (a-z)
  - Digits (0-9)
  - Special characters (!@#$%^&* etc.)

Password history is not enforced by default. Passwords are stored as bcrypt hashes.

### Password Reset

Administrators can reset any user's password:

```bash
curl -X POST http://localhost:8000/api/v1/users/2/reset-password \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{"new_password": "NewSecureP@ss456"}'
```

Users can change their own password from **Settings → Profile → Change Password**.

---

## Active Directory Integration

When AD is configured (see [Configuration](CONFIGURATION.md)), users can authenticate with their AD credentials. AD users are automatically created on first login.

### AD Group Mapping

| AD Group | Mission Control Role |
|---|---|
| `MC-Admins` | `admin` |
| `MC-Operators` | `operator` |
| `MC-Viewers` | `viewer` |

Group mapping is configured in the application config. Users not in any mapped group are denied access unless a local fallback account exists.

---

## API Keys

API keys are used for agent-to-server authentication. See [Agent Deployment](AGENT_DEPLOYMENT.md) for API key management.

```bash
# Create an API key for an agent
curl -X POST http://localhost:8000/api/v1/api-keys \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "agent-prod-01", "expires_days": 365}'
```

---

## Session Management

- Active sessions are tracked in Redis.
- Sessions expire after 30 minutes of inactivity.
- Administrators can view and terminate active sessions from **Settings → Sessions**.
- Maximum concurrent sessions per user: 5 (default).

See [Monitoring](MONITORING.md) for session health checks and [Logging](LOGGING.md) for audit trail configuration.
