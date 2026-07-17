# Mission Control — Troubleshooting Guide

## Quick Diagnostics

Run the health check script first:

```bash
/opt/missioncontrol/scripts/health.sh
```

Check service status:

```bash
docker compose ps
```

View recent logs:

```bash
docker compose logs --tail=100
```

## Common Issues

### Docker Won't Start

**Symptom:** `Cannot connect to the Docker daemon`

**Causes:**
- Docker service not running
- Nesting not enabled in LXC
- Keyctl not enabled in LXC

**Fix:**
```bash
# Start Docker
systemctl start docker

# If Docker still won't start, check LXC features
# On Proxmox host:
pct set <VMID> -features nesting=1,keyctl=1
pct restart <VMID>
```

### Backend Container Crashes

**Symptom:** `mc-backend` exits immediately

**Check:**
```bash
docker compose logs backend
```

**Common causes:**
1. Missing `MISSIONCONTROL_SECRET_KEY` in `.env`
2. PostgreSQL not ready
3. Redis not ready

**Fix:**
```bash
# Verify .env
cat /opt/missioncontrol/.env | grep SECRET_KEY

# Ensure database is ready
docker compose up -d postgres redis
sleep 10
docker compose up -d backend
```

### Database Connection Refused

**Symptom:** `Connection refused` or `FATAL: password authentication failed`

**Fix:**
```bash
# Check PostgreSQL status
docker compose ps postgres

# Verify credentials in .env match PostgreSQL
docker compose exec postgres psql -U mission_control -d mission_control -c "SELECT 1"

# Reset database password (if needed)
docker compose exec postgres psql -U postgres -c "ALTER USER mission_control WITH PASSWORD 'newpassword'"
# Update .env with new password
# Restart backend
docker compose restart backend
```

### Redis Connection Error

**Symptom:** `Error connecting to Redis`

**Fix:**
```bash
# Check Redis status
docker compose ps redis

# Test Redis connectivity
docker compose exec redis redis-cli ping
# Should return: PONG

# Restart Redis
docker compose restart redis
```

### Port 80 Already in Use

**Symptom:** `Bind for 0.0.0.0:80 failed: port is already allocated`

**Fix:**
```bash
# Find what's using port 80
ss -tlnp | grep :80

# Stop conflicting service
systemctl stop apache2  # or nginx, etc.

# Or change the port in docker-compose.yml
# ports: "8080:80"
```

### Out of Memory

**Symptom:** Container killed, OOM errors in logs

**Fix:**
```bash
# Check memory usage
free -h
docker stats --no-stream

# Increase LXC memory
# On Proxmox host:
pct set <VMID> --memory 12288  # 12GB

# Or reduce resource limits in docker-compose.yml
```

### Disk Space Full

**Symptom:** `No space left on device`

**Fix:**
```bash
# Check disk usage
df -h

# Clean Docker resources
docker system prune -af
docker volume prune -f

# Clean old backups
ls -la /opt/missioncontrol/backups/
rm /opt/missioncontrol/backups/missioncontrol_*.tar.gz  # Keep only needed

# Clean logs
find /opt/missioncontrol/logs -name "*.log" -size +100M -delete
```

### Cannot Pull Docker Images

**Symptom:** `Error response from daemon: Get https://registry-1.docker.io/v2/`

**Fix:**
```bash
# Check DNS
nslookup registry-1.docker.io

# Check internet connectivity
curl -s https://registry-1.docker.io/v2/ > /dev/null

# If behind proxy, configure Docker proxy
mkdir -p /etc/systemd/system/docker.service.d
cat > /etc/systemd/system/docker.service.d/proxy.conf << EOF
[Service]
Environment="HTTP_PROXY=http://proxy:3128"
Environment="HTTPS_PROXY=http://proxy:3128"
EOF
systemctl daemon-reload
systemctl restart docker
```

### Nginx 502 Bad Gateway

**Symptom:** Web UI shows 502 error

**Fix:**
```bash
# Check backend is running
docker compose ps backend

# Check backend health
docker compose exec backend python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/live', timeout=2)"

# Check frontend is running
docker compose ps frontend

# Restart all
docker compose restart
```

### First Boot Stuck

**Symptom:** Container starts but Mission Control never becomes available

**Fix:**
```bash
# Check first boot log
cat /var/log/mission-control-setup.log

# Check Docker logs
docker compose logs

# Manual first boot
/opt/missioncontrol/scripts/firstboot.sh --reset
```

### Migration Errors

**Symptom:** `alembic.util.exc.CommandError: Can't locate revision`

**Fix:**
```bash
# Check current migration state
docker compose exec backend alembic current

# Show migration history
docker compose exec backend alembic history

# Force to head
docker compose exec backend alembic upgrade head

# If still broken, stamp to current state
docker compose exec backend alembic stamp head
```

## Log Locations

| Log | Location |
|-----|----------|
| Backend | `docker compose logs backend` |
| Frontend | `docker compose logs frontend` |
| Nginx access | `/opt/missioncontrol/logs/nginx/access.log` |
| Nginx error | `/opt/missioncontrol/logs/nginx/error.log` |
| First boot | `/var/log/mission-control-setup.log` |
| Backup | `/opt/missioncontrol/logs/backup/` |
| Docker | `journalctl -u docker` |

## Getting Help

1. Run health check: `/opt/missioncontrol/scripts/health.sh`
2. Check logs: `docker compose logs --tail=200`
3. Verify configuration: `docker compose config`
4. Check disk/memory: `df -h && free -h`

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `MISSIONCONTROL_SECRET_KEY` | Yes | Fernet encryption key |
| `POSTGRES_DB` | Yes | Database name |
| `POSTGRES_USER` | Yes | Database user |
| `POSTGRES_PASSWORD` | Yes | Database password |
| `POSTGRES_HOST` | Yes | Database host |
| `POSTGRES_PORT` | Yes | Database port |
| `REDIS_HOST` | Yes | Redis host |
| `REDIS_PORT` | Yes | Redis port |
| `BACKEND_CORS_ORIGINS` | No | Allowed CORS origins |
| `COMPOSE_PROJECT_NAME` | No | Docker Compose project name |
