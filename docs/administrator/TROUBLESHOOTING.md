# Troubleshooting

**Version:** 3.0.0

---

## Diagnostic Commands

Run these first to gather system state:

```bash
# Container status
docker compose -f docker-compose.prod.yml ps

# API health
curl -s http://localhost:8000/live | python -m json.tool
curl -s http://localhost:8000/ready | python -m json.tool
curl -s http://localhost:8000/subsystems | python -m json.tool
curl -s http://localhost:8000/version | python -m json.tool

# Database connectivity
docker exec missioncontrol-postgres-1 pg_isready -U missioncontrol

# Redis connectivity
docker exec missioncontrol-redis-1 redis-cli ping

# Recent logs
docker compose -f docker-compose.prod.yml logs --tail=100 api
docker compose -f docker-compose.prod.yml logs --tail=100 postgres
docker compose -f docker-compose.prod.yml logs --tail=100 redis

# System resources
docker stats --no-stream
```

---

## Agent Offline

**Symptoms:** Agent shows "Offline" in the dashboard.

**Diagnostic:**

```bash
# On the agent host, check agent status
systemctl status mission-control-agent

# Check agent logs
tail -50 /var/log/mission-control-agent/agent.log

# Test API connectivity from the agent host
curl -H "X-API-Key: your_key_here" http://control.example.com/api/v1/health

# Check DNS resolution
nslookup control.example.com

# Check firewall
telnet control.example.com 8000
```

**Common Causes and Fixes:**

1. **API key expired or revoked** — Generate a new API key and update the agent config. See [Agent Deployment](AGENT_DEPLOYMENT.md).
2. **Network/firewall blocking port 8000** — Open the port or verify the reverse proxy is forwarding correctly.
3. **Server URL wrong in config.yaml** — Correct the `server.url` field.
4. **Agent service crashed** — Restart with `systemctl restart mission-control-agent` and review logs.
5. **TLS certificate issue** — If using a self-signed cert, set the CA bundle path in the agent config.

---

## Plugin Failures

**Symptoms:** Plugin shows "Unhealthy" or "Degraded" status.

**Diagnostic:**

```bash
# Check plugin health
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/plugins/health

# Check API server logs for plugin errors
docker compose logs api 2>&1 | grep -i plugin

# Check plugin-specific logs (if configured)
ls /opt/mission-control/plugins/*/logs/
```

**Common Causes and Fixes:**

1. **Incompatible plugin version** — Update the plugin to a version compatible with Mission Control 3.0.0. See [Plugin Management](PLUGIN_MANAGEMENT.md).
2. **Missing permissions** — Review and grant required plugin permissions.
3. **Dependency failure** — For hybrid plugins, verify the agent-side component is running.
4. **Configuration error** — Check plugin-specific settings under **Plugins → Settings**.

---

## Database Problems

**Symptoms:** API errors mentioning database, slow queries, connection refused.

### Connection Refused

```bash
# Check PostgreSQL container
docker compose -f docker-compose.prod.yml ps postgres
docker compose -f docker-compose.prod.yml logs postgres --tail=50

# Verify credentials
docker exec missioncontrol-postgres-1 pg_isready -U missioncontrol

# Test connection from API container
docker exec missioncontrol-api-1 python -c "
import asyncio, asyncpg
async def test():
    conn = await asyncpg.connect('postgresql://missioncontrol:password@postgres:5432/missioncontrol')
    print('Connected:', await conn.fetchval('SELECT version()'))
    await conn.close()
asyncio.run(test())
"
```

### Slow Queries

```bash
# Enable query logging temporarily
# Set DATABASE_ECHO=true in .env, then restart API

# Check for long-running queries
docker exec missioncontrol-postgres-1 psql -U missioncontrol -c "
SELECT pid, now() - pg_stat_activity.query_start AS duration, query, state
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY duration DESC;"
```

### Connection Pool Exhausted

```bash
# Check active connections
docker exec missioncontrol-postgres-1 psql -U missioncontrol -c "
SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

# Increase pool size if needed — see [Performance](PERFORMANCE.md)
# Set DATABASE_POOL_SIZE and DATABASE_MAX_OVERFLOW in .env
```

### Migration Failures

```bash
# Check current migration state
docker compose run --rm api alembic current

# Check migration history
docker compose run --rm api alembic history

# If migration failed midway, downgrade and retry
docker compose run --rm api alembic downgrade -1
docker compose run --rm api alembic upgrade head
```

---

## Redis Connectivity

**Symptoms:** Rate limiting errors, session issues, event bus failures.

```bash
# Check Redis container
docker compose -f docker-compose.prod.yml ps redis
docker compose -f docker-compose.prod.yml logs redis --tail=50

# Ping Redis
docker exec missioncontrol-redis-1 redis-cli ping
# Expected: PONG

# Check memory usage
docker exec missioncontrol-redis-1 redis-cli info memory

# Check connected clients
docker exec missioncontrol-redis-1 redis-cli info clients

# Flush cache if corrupted (causes temporary performance hit)
docker exec missioncontrol-redis-1 redis-cli FLUSHDB
```

---

## Docker Issues

### Container Won't Start

```bash
# Check container logs
docker compose -f docker-compose.prod.yml logs <service>

# Check for port conflicts
netstat -tlnp | grep -E ':(8000|3000|5432|6379)'

# Rebuild if needed
docker compose -f docker-compose.prod.yml build --no-cache <service>
docker compose -f docker-compose.prod.yml up -d <service>
```

### Disk Space

```bash
# Check Docker disk usage
docker system df

# Clean up unused images and volumes
docker system prune -af --volumes
```

### Network Issues

```bash
# List Docker networks
docker network ls

# Inspect the mission control network
docker network inspect missioncontrol_default

# Test inter-container connectivity
docker exec missioncontrol-api-1 ping postgres
docker exec missioncontrol-api-1 ping redis
```

---

## Authentication Failures

**Symptoms:** Login fails, JWT errors, "Unauthorized" responses.

```bash
# Verify SECRET_KEY is set and valid
grep MISSIONCONTROL_SECRET_KEY .env

# Check if the key is a valid Fernet key
python -c "
from cryptography.fernet import Fernet
key = b'your_key_here'
Fernet(key)  # Will raise InvalidToken if malformed
print('Key is valid')
"

# Test login via API
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}'
```

**Common Causes:**

1. **SECRET_KEY changed** — All existing JWTs become invalid. Users must re-login.
2. **Clock skew** — Ensure server time is synchronized (`timedatectl status`).
3. **Token expired** — Tokens expire after 30 minutes. Use the refresh token endpoint.

---

## Heartbeat Problems

**Symptoms:** Agents frequently showing offline/online flicker.

```bash
# Check agent heartbeat logs
grep -i heartbeat /var/log/mission-control-agent/agent.log

# Check server-side agent status
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/agents | python -m json.tool

# Increase heartbeat tolerance if network is unreliable
# In agent config.yaml:
# agent:
#   heartbeat_interval: 60  # Increase from default 30
```

---

## Performance Issues

See [Performance](PERFORMANCE.md) for tuning guidance.

---

## Getting Help

If the above steps don't resolve your issue:

1. Collect diagnostic output from the commands above.
2. Check [FAQ](FAQ.md) for known issues.
3. Open an issue at `https://github.com/casa/mission-control/issues`.
4. Include the diagnostic output, Mission Control version (`curl http://localhost:8000/version`), and OS details.
