# Mission Control — Restore Guide

## Overview

The restore script recovers your Mission Control installation from a backup created by `backup.sh`. It restores the database, configuration, plugins, playbooks, and automation.

## Quick Restore

```bash
sudo /opt/missioncontrol/scripts/restore.sh /opt/missioncontrol/backups/missioncontrol_20260717_143022.tar.gz
```

## What Gets Restored

| Component | Restored |
|-----------|----------|
| Database (PostgreSQL) | Yes (unless --no-db) |
| Environment file (.env) | Yes |
| Docker Compose config | Yes |
| Nginx configuration | Yes |
| Application config | Yes |
| Plugins | Yes |
| Playbooks | Yes |
| Automation configs | Yes |

## Restore Options

### Skip Database Restore

```bash
sudo /opt/missioncontrol/scripts/restore.sh backup.tar.gz --no-db
```

### Skip Confirmation Prompt

```bash
sudo /opt/missioncontrol/scripts/restore.sh backup.tar.gz --no-confirm
```

## Restore Process

The restore script:

1. **Extracts** the backup archive
2. **Stops** all Docker services
3. **Restores** configuration files (.env, docker-compose.yml, nginx)
4. **Restores** application configuration
5. **Restores** plugins, playbooks, and automation
6. **Restarts** database containers
7. **Restores** the database from SQL dump
8. **Starts** all services
9. **Verifies** health of all components
10. **Resets** the first-boot marker

## Restore Scenarios

### Complete System Restore

```bash
# Full restore including database
sudo /opt/missioncontrol/scripts/restore.sh /opt/missioncontrol/backups/missioncontrol_20260717_143022.tar.gz
```

### Configuration-Only Restore

```bash
# Restore config without touching the database
sudo /opt/missioncontrol/scripts/restore.sh /opt/missioncontrol/backups/missioncontrol_20260717_143022.tar.gz --no-db
```

### Restore to New Server

1. Install Docker and Docker Compose on new server
2. Copy the backup archive to the new server
3. Copy scripts to `/opt/missioncontrol/scripts/`
4. Run the restore:

```bash
sudo /opt/missioncontrol/scripts/restore.sh /path/to/backup.tar.gz
```

### Restore from External Storage

```bash
# Mount backup share
mount -t nfs backup-server:/exports/mc-backups /mnt/backup-share

# Restore
sudo /opt/missioncontrol/scripts/restore.sh /mnt/backup-share/missioncontrol_20260717_143022.tar.gz
```

## Verification After Restore

```bash
# Check health
/opt/missioncontrol/scripts/health.sh

# Verify API
curl http://localhost/api/v1/version

# Check logs
docker compose logs --tail=50
```

## Important Notes

- **All current data will be lost** when restoring (the database is dropped and recreated)
- **Back up current state** before restoring if you might need it later
- **The .env file is overwritten** — ensure you have the new secrets
- **First boot marker is reset** — the installer will re-run on next boot

## Rollback a Failed Upgrade

If an upgrade failed and you need to revert:

```bash
# Find the pre-upgrade backup
ls -la /opt/missioncontrol/backups/

# Restore it
sudo /opt/missioncontrol/scripts/restore.sh /opt/missioncontrol/backups/missioncontrol_YYYYMMDD_HHMMSS.tar.gz
```

## Troubleshooting

### "Restore cancelled by user"

- You didn't type "yes" at the confirmation prompt
- Re-run with `--no-confirm` to skip the prompt

### Database restore fails

- Check PostgreSQL is running: `docker compose ps postgres`
- Check backup file exists: `ls -la /path/to/backup/db/`
- Manual restore: `gunzip -c backup.sql.gz | docker compose exec -T postgres psql -U mission_control mission_control`

### Services won't start after restore

- Check .env: `cat /opt/missioncontrol/.env`
- Check Docker Compose: `docker compose config`
- Check logs: `docker compose logs backend`

### "Invalid backup archive structure"

- Verify archive: `tar -tzf backup.tar.gz`
- Ensure it was created by `backup.sh`
