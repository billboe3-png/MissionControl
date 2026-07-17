# Mission Control — Upgrade Guide

## Overview

Upgrading Mission Control is safe and automated. The update script creates a backup before upgrading and can automatically rollback on failure.

## Quick Upgrade

```bash
sudo /opt/missioncontrol/scripts/update.sh
```

## What the Update Script Does

1. **Creates backup** of current configuration and database
2. **Pulls latest images** from Docker registry
3. **Rebuilds containers** with updated code
4. **Runs database migrations** automatically
5. **Restarts all services** with zero-downtime sequence
6. **Verifies health** of all components
7. **Rolls back** automatically if health check fails

## Upgrade Options

### Upgrade to Specific Version

```bash
sudo /opt/missioncontrol/scripts/update.sh --version 3.1.0
```

### Skip Backup (Not Recommended)

```bash
sudo /opt/missioncontrol/scripts/update.sh --no-backup
```

### Skip Automatic Rollback

```bash
sudo /opt/missioncontrol/scripts/update.sh --no-rollback
```

## Manual Upgrade

If the automated script fails, you can upgrade manually:

```bash
# Enter the install directory
cd /opt/missioncontrol

# Backup first
/opt/missioncontrol/scripts/backup.sh

# Pull latest code (if using git-based deployment)
git pull origin main

# Pull latest images
docker compose pull

# Rebuild containers
docker compose build --no-cache

# Run migrations
docker compose up -d postgres redis
sleep 10
docker compose exec backend alembic upgrade head

# Restart all services
docker compose down
docker compose up -d

# Verify health
/opt/missioncontrol/scripts/health.sh
```

## Rollback

If an upgrade fails and automatic rollback didn't trigger:

```bash
# List available backups
ls -la /opt/missioncontrol/backups/

# Restore from backup
sudo /opt/missioncontrol/scripts/restore.sh /opt/missioncontrol/backups/missioncontrol_YYYYMMDD_HHMMSS.tar.gz
```

## Version Information

Check current version:

```bash
# From API
curl http://localhost/api/v1/version

# From .env file
grep MC_VERSION /opt/missioncontrol/.env
```

## What's Updated During Upgrade

| Component | Updated |
|-----------|---------|
| Docker images | Yes (pulled from registry) |
| Database schema | Yes (Alembic migrations) |
| Environment file | No (preserved) |
| Nginx config | Yes (from deployment package) |
| Plugins | No (preserved) |
| Playbooks | No (preserved) |
| Logs | No (preserved) |
| Backups | No (preserved) |

## Pre-Upgrade Checklist

- [ ] Check current version: `curl http://localhost/api/v1/version`
- [ ] Review release notes for breaking changes
- [ ] Ensure sufficient disk space (at least 2x current installation)
- [ ] Schedule maintenance window if needed
- [ ] Notify users of potential downtime

## Post-Upgrade Verification

```bash
# Run health checks
/opt/missioncontrol/scripts/health.sh

# Check all services are running
docker compose ps

# Verify API responds
curl http://localhost/api/v1/health/live

# Check logs for errors
docker compose logs --tail=50
```

## Troubleshooting

### Upgrade hangs at "Pulling images"

- Check internet connectivity: `curl -s https://registry-1.docker.io/v2/`
- Check DNS: `nslookup registry-1.docker.io`
- Try manually: `docker compose pull`

### Database migration fails

- Check migration state: `docker compose exec backend alembic current`
- Review migration history: `docker compose exec backend alembic history`
- Manual fix: `docker compose exec backend alembic upgrade head`

### Services won't start after upgrade

- Check logs: `docker compose logs backend`
- Verify .env: `cat /opt/missioncontrol/.env`
- Rollback: `sudo /opt/missioncontrol/scripts/restore.sh <backup>`
