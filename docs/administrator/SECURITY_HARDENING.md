# Security Hardening

**Version:** 3.0.0

---

## TLS Setup

Mission Control does not terminate TLS directly. Use a reverse proxy.

### nginx with Let's Encrypt

```nginx
server {
    listen 80;
    server_name control.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name control.example.com;

    ssl_certificate /etc/letsencrypt/live/control.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/control.example.com/privkey.pem;

    # TLS hardening
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;

    # HSTS
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains" always;

    # Security headers
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Rate limiting
        limit_req zone=api burst=20 nodelay;
    }
}
```

### Rate Limiting Zones

Add to the nginx `http` block:

```nginx
http {
    limit_req_zone $binary_remote_addr zone=api:10m rate=60r/m;
    limit_req_zone $binary_remote_addr zone=auth:10m rate=10r/m;
}
```

---

## Firewall Rules

### UFW (Ubuntu)

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTPS (dashboard and API via reverse proxy)
sudo ufw allow 443/tcp

# Block direct API access from outside
# (only accessible through reverse proxy)

# Enable firewall
sudo ufw enable
sudo ufw status verbose
```

### iptables

```bash
# Allow established connections
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow SSH
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow HTTPS
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Drop direct API access from external IPs
iptables -A INPUT -p tcp --dport 8000 -s 127.0.0.1 -j ACCEPT
iptables -A INPUT -p tcp --dport 8000 -j DROP

# Drop direct dashboard access from external IPs
iptables -A INPUT -p tcp --dport 3000 -s 127.0.0.1 -j ACCEPT
iptables -A INPUT -p tcp --dport 3000 -j DROP

# Save rules
iptables-save > /etc/iptables/rules.v4
```

---

## RBAC

Role-Based Access Control is enforced at the API layer. Every endpoint requires authentication and checks the user's role against the required permission.

### Built-in Roles

| Role | Access Level |
|---|---|
| `admin` | Full system access. |
| `operator` | Agent management, remote execution, plugin management. |
| `viewer` | Read-only dashboard and reports. |

See [User Management](USER_MANAGEMENT.md) for the complete permissions matrix.

### Enforcing Least Privilege

1. Create operator accounts for day-to-day operations.
2. Reserve admin accounts for configuration changes only.
3. Use viewer accounts for read-only monitoring.
4. Audit role assignments quarterly.

---

## Secret Rotation

Rotate secrets regularly to limit exposure from compromised credentials.

### Mission Control Secret Key

```bash
# Generate new key
NEW_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Update .env
sed -i "s|MISSIONCONTROL_SECRET_KEY=.*|MISSIONCONTROL_SECRET_KEY=$NEW_KEY|" .env

# Restart API (existing sessions will be invalidated)
docker compose -f docker-compose.prod.yml restart api
```

### Database Password

```bash
# Change PostgreSQL password
docker exec missioncontrol-postgres-1 psql -U missioncontrol -c \
  "ALTER USER missioncontrol WITH PASSWORD 'new_secure_password';"

# Update .env
sed -i "s|POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=new_secure_password|" .env

# Restart API
docker compose -f docker-compose.prod.yml restart api
```

### API Keys

Rotate agent API keys before expiration:

```bash
# Create new key
NEW_KEY=$(curl -s -X POST http://localhost:8000/api/v1/api-keys \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "agent-prod-01", "expires_days": 365}')

# Update agent config.yaml with new key
# Restart agent
# Revoke old key
curl -X DELETE http://localhost:8000/api/v1/api-keys/<old_key_id> \
  -H "Authorization: Bearer <admin-token>"
```

### Microsoft 365 Client Secret

Rotate in the Azure AD portal and update the `M365_CLIENT_SECRET` environment variable.

### Zabbix Password

Update `ZABBIX_PASSWORD` in `.env` and restart the API.

---

## Token Expiration

JWT tokens expire after 30 minutes (access) and 7 days (refresh). For tighter security:

- Reduce session timeout to 15 minutes for admin accounts.
- Enable single-session enforcement (one active session per user).
- Configure automatic logout on the dashboard.

These settings are in `backend/app/core/auth.py`. Modify and rebuild for custom values.

---

## API Security

### Input Validation

All API endpoints validate input using Pydantic models. Malformed requests are rejected with 422 responses.

### SQL Injection Protection

SQLAlchemy 2.0 with parameterized queries prevents SQL injection. Never construct raw SQL from user input.

### CORS

Restrict CORS to your dashboard origin:

```bash
# In .env
BACKEND_CORS_ORIGINS=["https://control.example.com"]
```

Never use `["*"]` in production.

### API Key Security

- API keys are stored as bcrypt hashes.
- Keys are shown only once at creation time.
- Keys can be scoped to specific agents.
- Keys can be revoked immediately.

---

## Reverse Proxy Best Practices

1. **Terminrate TLS** at the proxy, not the application.
2. **Set security headers** (HSTS, X-Content-Type-Options, X-Frame-Options).
3. **Rate limit** at the proxy layer for DDoS protection.
4. **Proxy headers** — Forward `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto`.
5. **WebSocket support** — If using real-time features, configure WebSocket proxying.
6. **Access logs** — Enable nginx access logs for audit trails.

### WebSocket Proxying

```nginx
location /ws/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_read_timeout 86400;
}
```

---

## Audit Trail

Enterprise edition provides a complete audit trail of:

- User authentication events (login, logout, failed attempts)
- User management operations (create, update, delete)
- Agent management operations
- Plugin installations and removals
- Configuration changes
- Remote command execution
- API key management

Audit logs are stored in the database and are immutable. Retention is configurable per company.

```bash
# Query audit logs
curl -H "Authorization: Bearer <admin-token>" \
  "http://localhost:8000/api/v1/audit-logs?limit=100&action=login"
```

### Audit Log Retention

Default retention: 90 days. Configure per company:

```bash
curl -X PUT http://localhost:8000/api/v1/companies/1 \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{"settings": {"audit_retention_days": 365}}'
```

---

## Security Checklist

- [ ] TLS configured and HTTP redirects to HTTPS
- [ ] Firewall blocks direct access to ports 3000 and 8000
- [ ] `MISSIONCONTROL_SECRET_KEY` is a strong, unique Fernet key
- [ ] Database password is strong and not reused elsewhere
- [ ] CORS restricted to dashboard origin
- [ ] Rate limiting enabled (auth and API)
- [ ] Admin accounts use strong passwords
- [ ] API keys rotated before expiration
- [ ] Audit logging enabled (Enterprise)
- [ ] Security headers configured in reverse proxy
- [ ] Secrets not committed to source control

See [Backup and Restore](BACKUP_AND_RESTORE.md) for encrypting backups and [Configuration](CONFIGURATION.md) for all security-related environment variables.
