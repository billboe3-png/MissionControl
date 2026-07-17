# Deployment Guide

## Prerequisites

- Docker and Docker Compose v2+
- PostgreSQL 16+ (or use the Docker service)
- Redis 7.2+ (or use the Docker service)
- A Fernet encryption key (generate with the command below)

## Generate Secret Key

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Quick Start (Docker)

```bash
git clone <repository>
cd MissionControl

# Copy and edit environment file
cp .env.example .env
# Edit .env and set:
#   MISSIONCONTROL_SECRET_KEY=<your-generated-key>
#   POSTGRES_PASSWORD=<strong-password>

# Start the stack
docker compose up -d
```

The backend will:
1. Validate `MISSIONCONTROL_SECRET_KEY`
2. Run Alembic migrations
3. Seed the database
4. Start the API server

**Access points:**
- Application: http://localhost (via nginx)
- API: http://localhost/api/v1
- API Docs: http://localhost/api/docs
- Health Check: http://localhost/api/v1/health/live
- Readiness Check: http://localhost/api/v1/health/ready

## Production Deployment

For production, use `docker-compose.prod.yml`:

```bash
# Production stack (no bind mounts, resource limits, log rotation)
docker compose -f docker-compose.prod.yml up -d
```

### Production Differences

| Feature | Development | Production |
|---------|-------------|------------|
| Source code | Bind-mounted | Built into image |
| docker.sock | Mounted | Not mounted |
| Resource limits | None | 512M backend, 128M frontend/nginx |
| Restart policy | unless-stopped | always |
| Logging | stdout | json-file (10MB, 3 files) |

### Environment Variables

See `.env.example` for all available variables. Key production settings:

| Variable | Required | Description |
|----------|----------|-------------|
| `MISSIONCONTROL_SECRET_KEY` | Yes | Fernet key for credential encryption |
| `POSTGRES_USER` | Yes | Database user (no default) |
| `POSTGRES_PASSWORD` | Yes | Database password (no default) |
| `POSTGRES_DB` | No | Database name (default: mission_control) |
| `REDIS_HOST` | No | Redis host (default: redis) |
| `REDIS_PORT` | No | Redis port (default: 6379) |

## Backup & Restore

### Backup

```bash
# Create a timestamped backup
./scripts/backup-db.ps1
# Backups saved to ./backups/mission_control_YYYYMMDD_HHMMSS.sql.gz
```

### Restore

```bash
# Restore from a backup (prompts for confirmation)
./scripts/restore-db.ps1 ./backups/mission_control_20260716_143022.sql.gz
```

**Warning:** Restore drops and recreates the database. All current data will be lost.

## Monitoring

### Health Endpoints

- `GET /api/v1/health/live` — Liveness probe (always 200 if running)
- `GET /api/v1/health/ready` — Readiness probe (checks PostgreSQL and Redis)
- `GET /api/v1/version` — Application version
- `GET /api/v1/status` — Platform status

### Structured Logging

All requests are logged with:
- Request ID (X-Request-ID header)
- HTTP method and path
- Response status code
- Response time in milliseconds

Example log line:
```
2026-07-16T14:30:22 INFO [missioncontrol] a1b2c3d4e5f6 GET /api/v1/dashboard 200 45.2ms
```

### Rate Limiting

- Default: 60 requests/minute per IP
- Login endpoint: 5 requests/minute per IP
- Health/version/agent endpoints: unlimited
- Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`

## Troubleshooting

### Backend won't start

1. Check `MISSIONCONTROL_SECRET_KEY` is set in `.env`
2. Ensure PostgreSQL and Redis are running
3. Check logs: `docker compose logs backend`

### Database migration errors

```bash
# Check current migration state
docker compose exec backend alembic current

# Run pending migrations
docker compose exec backend alembic upgrade head
```

### Redis connection errors

```bash
# Verify Redis is running
docker compose exec redis redis-cli ping
# Should return: PONG
```

## CI/CD

GitHub Actions CI runs on every push and PR:

1. **Backend**: ruff lint + pytest
2. **Frontend**: TypeScript check + production build

See `.github/workflows/ci.yml` for configuration.
