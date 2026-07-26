# Upgrade Procedures

**Version:** 3.0.0

---

## Pre-Upgrade Checklist

- [ ] Read the release notes for the target version.
- [ ] Verify version compatibility (see below).
- [ ] Create a full backup (see [Backup and Restore](BACKUP_AND_RESTORE.md)).
- [ ] Notify users of the maintenance window.
- [ ] Test the upgrade in a staging environment.
- [ ] Verify disk space (at least 2x the current data size).
- [ ] Check that all agents are online and healthy.

---

## Version Compatibility

| Current Version | Target Version | Upgrade Path |
|---|---|---|
| 2.x | 3.0.0 | Direct upgrade supported |
| 1.x | 3.0.0 | Upgrade to 2.x first, then to 3.0.0 |
| Any | Any (same major) | Direct upgrade supported |

Major version upgrades may include breaking changes to the database schema, API, or configuration format. Always review the changelog.

---

## Docker Compose Upgrade

### Step 1: Backup

```bash
/opt/mission-control/scripts/backup-full.sh
```

### Step 2: Pull New Images

```bash
cd /opt/mission-control
git fetch origin
git checkout v3.0.0  # or the target version tag

# Update image tags if needed
docker compose -f docker-compose.prod.yml pull
```

### Step 3: Run Database Migrations

```bash
docker compose -f docker-compose.prod.yml run --rm api alembic upgrade head
```

### Step 4: Restart Services

```bash
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

### Step 5: Verify

```bash
# Check health endpoints
curl http://localhost:8000/live
curl http://localhost:8000/ready
curl http://localhost:8000/version

# Check all containers
docker compose -f docker-compose.prod.yml ps

# Check logs for errors
docker compose -f docker-compose.prod.yml logs --tail=50 api
```

---

## Manual Upgrade

### Step 1: Backup

Follow the backup procedures in [Backup and Restore](BACKUP_AND_RESTORE.md).

### Step 2: Stop Services

```bash
sudo systemctl stop mission-control
```

### Step 3: Update Code

```bash
cd /opt/mission-control
sudo -u missioncontrol git fetch origin
sudo -u missioncontrol git checkout v3.0.0
```

### Step 4: Update Dependencies

```bash
sudo -u missioncontrol ./venv/bin/pip install -r requirements.txt
```

### Step 5: Run Database Migrations

```bash
sudo -u missioncontrol ./venv/bin/alembic upgrade head
```

### Step 6: Restart Services

```bash
sudo systemctl start mission-control
```

### Step 7: Verify

```bash
curl http://localhost:8000/live
curl http://localhost:8000/ready
curl http://localhost:8000/version
```

---

## Database Migrations

Mission Control uses Alembic for database schema migrations. Migrations run automatically during Docker Compose upgrades but can also be executed manually.

### View Current Revision

```bash
docker compose run --rm api alembic current
```

### View Pending Migrations

```bash
docker compose run --rm api alembic heads
```

### Apply Migrations

```bash
docker compose run --rm api alembic upgrade head
```

### Rollback Migration

```bash
# Rollback one migration
docker compose run --rm api alembic downgrade -1

# Rollback to a specific revision
docker compose run --rm api alembic downgrade <revision_id>
```

### Generate Migration (Development)

```bash
docker compose run --rm api alembic revision --autogenerate -m "description of changes"
```

---

## Rollback Procedures

If an upgrade fails or causes issues, roll back to the previous version:

### Docker Compose Rollback

```bash
# Restore database from backup
docker compose -f docker-compose.prod.yml stop api
docker exec -i missioncontrol-postgres-1 pg_restore \
  -U missioncontrol -d missioncontrol --clean --if-exists \
  < /opt/mission-control/backups/postgres/pre_upgrade.dump

# Checkout previous version
git checkout v2.x.x  # previous version tag

# Restart with previous images
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

### Manual Rollback

```bash
# Stop the service
sudo systemctl stop mission-control

# Restore database
pg_restore -U missioncontrol -d missioncontrol --clean --if-exists \
  < /opt/mission-control/backups/postgres/pre_upgrade.dump

# Checkout previous version
cd /opt/mission-control
git checkout v2.x.x

# Reinstall dependencies
sudo -u missioncontrol ./venv/bin/pip install -r requirements.txt

# Start
sudo systemctl start mission-control
```

---

## Agent Updates

Agents are updated separately from the server. After upgrading the server:

1. Agents will auto-update if `auto_update: true` is configured (see [Agent Deployment](AGENT_DEPLOYMENT.md)).
2. Manual updates: download and install the new agent version on each host.
3. Verify agent connectivity after updates.

---

## Plugin Compatibility

After upgrading the server:

1. Check plugin compatibility on the **Plugins** page.
2. Update any plugins that require a new version for the upgraded server.
3. Remove plugins that are no longer compatible.

See [Plugin Management](PLUGIN_MANAGEMENT.md) for plugin lifecycle procedures.

---

## Post-Upgrade Checklist

- [ ] All health endpoints return healthy status.
- [ ] Dashboard loads correctly.
- [ ] Users can authenticate.
- [ ] Agents are online and sending heartbeats.
- [ ] Plugins are healthy.
- [ ] No errors in application logs.
- [ ] Remote commands execute successfully.
- [ ] Backup schedule is still active.

See [Troubleshooting](TROUBLESHOOTING.md) if issues are encountered.
