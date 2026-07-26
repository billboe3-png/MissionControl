# Configuration Reference

**Version:** 3.0.0

All 42 configuration fields are defined in `backend/app/core/config.py` and loaded from environment variables or the `.env` file.

---

## Application Settings

| Variable | Type | Default | Description |
|---|---|---|---|
| `PROJECT_NAME` | string | `Mission Control` | Application display name. |
| `ENVIRONMENT` | string | `development` | Runtime environment: `development`, `staging`, or `production`. |
| `EDITION` | string | `community` | Edition: `community` or `enterprise`. Enterprise enables advanced RBAC, audit logging, and marketplace features. See [User Management](USER_MANAGEMENT.md). |
| `COMPOSE_PROJECT_NAME` | string | `missioncontrol` | Docker Compose project namespace. Change to run multiple instances on the same host. |

---

## Security

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `MISSIONCONTROL_SECRET_KEY` | string | — | **Yes** | Fernet symmetric key used for JWT signing and data encryption. Generate with: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. Never commit this value to source control. |

---

## PostgreSQL

| Variable | Type | Default | Description |
|---|---|---|---|
| `POSTGRES_DB` | string | `missioncontrol` | Database name. |
| `POSTGRES_USER` | string | `missioncontrol` | Database user. |
| `POSTGRES_PASSWORD` | string | — | Database password. Use a strong, unique value in production. |
| `POSTGRES_HOST` | string | `postgres` | Database hostname. Use `localhost` for manual installs, `postgres` for Docker Compose. |
| `POSTGRES_PORT` | int | `5432` | Database port. |

The full SQLAlchemy connection string is constructed as:

```
postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}
```

---

## Redis

| Variable | Type | Default | Description |
|---|---|---|---|
| `REDIS_HOST` | string | `redis` | Redis hostname. Use `localhost` for manual installs, `redis` for Docker Compose. |
| `REDIS_PORT` | int | `6379` | Redis port. |

Redis is used for caching, session storage, the event bus, and rate limiting. See [Performance](PERFORMANCE.md) for tuning guidance.

---

## SQLAlchemy

| Variable | Type | Default | Description |
|---|---|---|---|
| `DATABASE_ECHO` | bool | `false` | Enable SQL query logging. Set to `true` during development only. Verbose in production. |
| `DATABASE_POOL_SIZE` | int | `5` | Number of persistent connections in the SQLAlchemy pool. Increase for production workloads. See [Performance](PERFORMANCE.md). |
| `DATABASE_MAX_OVERFLOW` | int | `10` | Maximum number of connections beyond `DATABASE_POOL_SIZE` that can be created on demand. |

---

## Remote Access

These variables configure SSH and WinRM connections for remote host management.

| Variable | Type | Default | Description |
|---|---|---|---|
| `TERMINAL_MAX_SESSIONS` | int | `10` | Maximum concurrent terminal sessions per user. |
| `SSH_CONNECT_TIMEOUT` | int | `10` | SSH connection timeout in seconds. |
| `SSH_COMMAND_TIMEOUT` | int | `30` | Default SSH command execution timeout in seconds. |
| `SSH_IDLE_TIMEOUT` | int | `300` | SSH idle session timeout in seconds. Connections are closed after this period of inactivity. |
| `WINRM_CONNECT_TIMEOUT` | int | `10` | WinRM connection timeout in seconds. |
| `WINRM_OPERATION_TIMEOUT` | int | `30` | WinRM operation timeout in seconds. |
| `REMOTE_MAX_COMMAND_TIMEOUT` | int | `300` | Maximum allowed timeout for any remote command in seconds. Prevents runaway commands. |
| `REMOTE_RETRY_COUNT` | int | `3` | Number of retry attempts for failed remote connections. |
| `REMOTE_CONNECTION_POOL_SIZE` | int | `5` | Number of persistent remote connections maintained in the pool. |

---

## Active Directory

Configure LDAP/AD integration for user authentication.

| Variable | Type | Default | Description |
|---|---|---|---|
| `AD_SERVER` | string | `""` | AD server hostname or IP. Leave empty to disable AD authentication. |
| `AD_PORT` | int | `389` | LDAP port. Use `636` for LDAPS. |
| `AD_USE_SSL` | bool | `false` | Enable SSL/TLS for the LDAP connection. |
| `AD_USERNAME` | string | `""` | Bind DN or username for AD authentication. |
| `AD_PASSWORD` | string | `""` | Bind password. |
| `AD_BASE_DN` | string | `""` | Base DN for user lookups, e.g. `DC=example,DC=com`. |

When configured, users can authenticate with their AD credentials. See [User Management](USER_MANAGEMENT.md) for mapping AD groups to Mission Control roles.

---

## Microsoft 365

Integration with Microsoft Graph API for M365 monitoring.

| Variable | Type | Default | Description |
|---|---|---|---|
| `M365_TENANT_ID` | string | `""` | Azure AD tenant ID. |
| `M365_CLIENT_ID` | string | `""` | Application (client) ID registered in Azure AD. |
| `M365_CLIENT_SECRET` | string | `""` | Client secret. Store securely and rotate regularly. |

---

## Zabbix Integration

Connect to a Zabbix server for infrastructure monitoring data.

| Variable | Type | Default | Description |
|---|---|---|---|
| `ZABBIX_URL` | string | `""` | Zabbix API URL, e.g. `https://zabbix.example.com/api_jsonrpc.php`. |
| `ZABBIX_USERNAME` | string | `""` | Zabbix API username. |
| `ZABBIX_PASSWORD` | string | `""` | Zabbix API password. |
| `ZABBIX_VERIFY_SSL` | bool | `true` | Verify SSL certificates when connecting to Zabbix. Set to `false` for self-signed certificates. |
| `ZABBIX_TIMEOUT` | int | `30` | Zabbix API request timeout in seconds. |
| `ZABBIX_RETRIES` | int | `3` | Number of retry attempts for failed Zabbix API calls. |

---

## Rate Limiting

| Variable | Type | Default | Description |
|---|---|---|---|
| `rate_limit_per_minute` | int | `60` | Maximum API requests per minute per client IP. |
| `rate_limit_auth_per_minute` | int | `10` | Maximum authentication attempts per minute per client IP. Lower value protects against brute-force attacks. |

Rate limiting is enforced via Redis. See [Performance](PERFORMANCE.md) for high-traffic tuning and [Security Hardening](SECURITY_HARDENING.md) for protection settings.

---

## CORS

| Variable | Type | Default | Description |
|---|---|---|---|
| `BACKEND_CORS_ORIGINS` | JSON array | `["http://localhost:3000"]` | Allowed origins for cross-origin requests. Format: JSON array of strings. In production, set to your dashboard URL, e.g. `["https://control.example.com"]`. |

---

## HTTPS and Reverse Proxy

Mission Control does not terminate TLS directly. Use a reverse proxy (nginx, Caddy, Traefik) in front of the API and Dashboard.

```nginx
# Example nginx TLS configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
ssl_prefer_server_ciphers off;
ssl_session_cache shared:SSL:10m;
```

Set `BACKEND_CORS_ORIGINS` to include the HTTPS origin of your dashboard. See [Security Hardening](SECURITY_HARDENING.md) for complete TLS guidance.

---

## Secrets Management

**Never** store secrets in source control. Recommended approaches:

1. **Environment variables** — Set in `.env` file (excluded via `.gitignore`) or injected by your orchestration platform.
2. **Docker secrets** — Use Docker Compose secrets for production deployments.
3. **Vault solutions** — HashiCorp Vault, AWS Secrets Manager, or Azure Key Vault for enterprise environments.

Key secrets requiring protection:

- `MISSIONCONTROL_SECRET_KEY`
- `POSTGRES_PASSWORD`
- `AD_PASSWORD`
- `M365_CLIENT_SECRET`
- `ZABBIX_PASSWORD`

---

## JWT Configuration

JWT tokens are signed using `MISSIONCONTROL_SECRET_KEY`. Default token lifetimes:

- **Access token:** 30 minutes
- **Refresh token:** 7 days

These are hardcoded in the authentication module and are not currently configurable via environment variables. To change them, modify the authentication source in `backend/app/core/auth.py`.

See [Security Hardening](SECURITY_HARDENING.md) for token rotation and expiration guidance.
