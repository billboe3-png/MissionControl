# Backup and Restore

**Version:** 3.0.0

---

## Backup Components

| Component | Tool | Priority |
|---|---|---|
| PostgreSQL database | `pg_dump` | Critical |
| Redis data | `redis-cli BGSAVE` | High |
| Configuration files | File copy | High |
| Plugin data | File copy | Medium |
| Log archives | File copy | Low |

---

## PostgreSQL Backup

### Manual Backup

```bash
# Full database backup
docker exec missioncontrol-postgres-1 pg_dump \
  -U missioncontrol \
  -Fc \
  -f /backups/missioncontrol_$(date +%Y%m%d_%H%M%S).dump \
  missioncontrol

# Copy backup out of container
docker cp missioncontrol-postgres-1:/backups/ ./backups/
```

### Automated Backup Script

Create `/opt/mission-control/scripts/backup-db.sh`:

```bash
#!/bin/bash
set -euo pipefail

BACKUP_DIR="/opt/mission-control/backups/postgres"
CONTAINER="missioncontrol-postgres-1"
DB_USER="missioncontrol"
DB_NAME="missioncontrol"
RETENTION_DAYS=30
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Dump database
docker exec "$CONTAINER" pg_dump -U "$DB_USER" -Fc -f "/backups/${DATE}.dump" "$DB_NAME"

# Copy from container
docker cp "${CONTAINER}:/backups/${DATE}.dump" "${BACKUP_DIR}/${DATE}.dump"

# Compress
gzip "${BACKUP_DIR}/${DATE}.dump"

# Remove old backups
find "$BACKUP_DIR" -name "*.dump.gz" -mtime +"$RETENTION_DAYS" -delete

echo "[$(date)] Backup completed: ${DATE}.dump.gz"
```

```bash
chmod +x /opt/mission-control/scripts/backup-db.sh
```

### Cron Schedule

```bash
# Daily backup at 2:00 AM
crontab -e
0 2 * * * /opt/mission-control/scripts/backup-db.sh >> /var/log/mission-control-backup.log 2>&1
```

### Restore

```bash
# Decompress
gunzip backups/20260726_020000.dump.gz

# Stop the API server to prevent writes
docker compose stop api

# Restore database
docker exec -i missioncontrol-postgres-1 pg_restore \
  -U missioncontrol \
  -d missioncontrol \
  --clean \
  --if-exists \
  < backups/20260726_020000.dump

# Run any pending migrations
docker compose run --rm api alembic upgrade head

# Restart API server
docker compose start api
```

---

## Redis Backup

### Manual Backup

```bash
# Trigger background save
docker exec missioncontrol-redis-1 redis-cli BGSAVE

# Copy RDB file
docker cp missioncontrol-redis-1:/data/dump.rdb ./backups/redis_$(date +%Y%m%d_%H%M%S).rdb
```

### Automated Redis Backup

Add to the backup script:

```bash
# Redis backup
docker exec missioncontrol-redis-1 redis-cli BGSAVE
sleep 5
docker cp missioncontrol-redis-1:/data/dump.rdb "${BACKUP_DIR}/redis_${DATE}.rdb"
```

### Redis Restore

```bash
# Stop Redis
docker compose stop redis

# Copy RDB file
docker cp backups/redis_20260726_020000.rdb missioncontrol-redis-1:/data/dump.rdb

# Start Redis
docker compose start redis
```

Redis data is reconstructable from the database, so Redis backup priority is lower than PostgreSQL.

---

## Configuration Backup

```bash
# Backup configuration files
tar -czf config_$(date +%Y%m%d).tar.gz \
  .env \
  docker-compose.yml \
  docker-compose.prod.yml \
  nginx/ \
  --exclude='*.log'
```

Store configuration backups in a separate location from database backups.

---

## Plugin Backup

```bash
# Backup installed plugins
tar -czf plugins_$(date +%Y%m%d).tar.gz \
  /opt/mission-control/plugins/
```

---

## Full Backup Script

Create `/opt/mission-control/scripts/backup-full.sh`:

```bash
#!/bin/bash
set -euo pipefail

BACKUP_BASE="/opt/mission-control/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

mkdir -p "${BACKUP_BASE}/postgres" "${BACKUP_BASE}/redis" "${BACKUP_BASE}/config" "${BACKUP_BASE}/plugins"

echo "[$(date)] Starting full backup..."

# PostgreSQL
/opt/mission-control/scripts/backup-db.sh

# Redis
docker exec missioncontrol-redis-1 redis-cli BGSAVE
sleep 5
docker cp missioncontrol-redis-1:/data/dump.rdb "${BACKUP_BASE}/redis/${DATE}.rdb"

# Config
tar -czf "${BACKUP_BASE}/config/${DATE}.tar.gz" \
  /opt/mission-control/.env \
  /opt/mission-control/docker-compose.yml

# Plugins
tar -czf "${BACKUP_BASE}/plugins/${DATE}.tar.gz" \
  /opt/mission-control/plugins/ 2>/dev/null || true

# Cleanup old backups
find "$BACKUP_BASE" -name "*.gz" -mtime +"$RETENTION_DAYS" -delete
find "$BACKUP_BASE" -name "*.rdb" -mtime +"$RETENTION_DAYS" -delete
find "$BACKUP_BASE" -name "*.dump" -mtime +"$RETENTION_DAYS" -delete

echo "[$(date)] Full backup completed."
```

```bash
chmod +x /opt/mission-control/scripts/backup-full.sh
crontab -e
# Add: 0 2 * * * /opt/mission-control/scripts/backup-full.sh >> /var/log/mission-control-backup.log 2>&1
```

---

## Disaster Recovery

### Recovery Time Objective (RTO)

- **Docker Compose:** ~15 minutes
- **Manual install:** ~30 minutes
- **Cloud (from snapshot):** ~10 minutes

### Recovery Point Objective (RPO)

- With daily backups: 24 hours
- With continuous WAL archiving: Near-zero

### Recovery Steps

1. Provision a new host or restore from VM snapshot.
2. Install Docker and Docker Compose (see [Installation](INSTALLATION.md)).
3. Restore configuration files from backup.
4. Restore PostgreSQL from the most recent backup.
5. Restore Redis from the most recent backup.
6. Run database migrations: `docker compose run --rm api alembic upgrade head`.
7. Start all services: `docker compose -f docker-compose.prod.yml up -d`.
8. Verify health: `curl http://localhost:8000/live`.
9. Reconnect agents (update `config.yaml` if the server URL changed).
10. Validate plugin status on the dashboard.

### Testing Recovery

Test your backup and recovery process quarterly:

1. Spin up an isolated environment.
2. Restore backups.
3. Verify all data is intact.
4. Confirm agents can connect.
5. Test all critical workflows.

See [Installation](INSTALLATION.md) for deployment steps and [Upgrades](UPGRADES.md) for migration procedures.
