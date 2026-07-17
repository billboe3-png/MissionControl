# Security Standards

## Authentication

### JWT Tokens
- Token-based authentication for all API users
- Tokens signed with HMAC-SHA256
- Configurable expiry (default: 24 hours)
- Refresh token support for long sessions

### API Keys
- Service-to-service authentication via `X-Agent-API-Key` header
- Agent registration tokens for initial setup
- Keys stored hashed, never in plaintext

### Agent Tokens
- Each agent has a unique `mc_agent_*` API key
- Keys generated on registration
- Used for heartbeat and command authentication

## Authorization

### Role-Based Access Control (RBAC)
- Roles: `global_admin`, `admin`, `operator`, `viewer`
- Permissions: `read`, `manage`, `execute` per resource
- Plugin permissions declared in manifest

### Plugin Permissions
- Plugins declare required permissions
- Permissions checked before plugin activation
- Granular permissions: `read:dashboard`, `manage:integrations`, etc.

## Secret Storage

### Encryption
- Fernet symmetric encryption (AES-128-CBC)
- Key derived from `MISSIONCONTROL_SECRET_KEY`
- All credential data encrypted at rest

### Sensitive Fields
- Never expose secrets in API responses
- Response schemas omit encrypted fields
- Logging never includes secrets or keys

## Tenant Isolation

### Company Isolation
- Resources scoped to `company_id`
- Queries filtered by tenant
- Cross-tenant access blocked

### Site Isolation
- Resources scoped to `site_id` within a company
- Site-level access control

## Audit Logging

All operations are logged:
- User actions (login, CRUD, execute)
- Plugin operations (register, enable, disable)
- Agent operations (register, heartbeat, command)
- Security events (auth failure, permission denied)

## API Security

### CORS
- Configurable allowed origins
- Restricted methods: GET, POST, PUT, DELETE, PATCH
- Restricted headers: Authorization, Content-Type, X-Agent-API-Key

### Security Headers
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`
- `X-Content-Type-Options: nosniff`

### Rate Limiting
- 60 requests/minute per IP (default)
- 5 requests/minute for login endpoint
- 429 Too Many Requests response with Retry-After

### Request Size Limits
- `client_max_body_size: 10m` (nginx)

## Certificate Validation
- HTTPS required in production
- SSL certificate verification enabled by default
- Configurable per integration (verify_ssl flag)
