# Mission Control — Backup Guide

## Overview

The backup script creates timestamped, compressed backups of your Mission Control installation. Backups include the database, configuration, plugins, playbooks, automation, and logs.

## Quick Backup

```bash
sudo /opt/missioncontrol/scripts/backup.sh
```

## What Gets Backed Up

| Component | Location in Backup | Included by Default |
|-----------|-------------------|-------------------|
| Database (PostgreSQL) | `db/missioncontrol.sql.gz` | Yes |
| Environment file (.env) | `config/env.backup` | Yes |
| Docker Compose config | `config/docker-compose.yml.backup` | Yes |
| Nginx configuration | `config/nginx/` | Yes |
| Application config | `config/app/` | Yes |
| Plugins | `plugins/` | Yes |
| Playbooks | `playbooks/` | Yes |
| Automation configs | `automation/` | Yes |
| Logs | `logs/` | Yes |
| Docker volumes | `db/postgres_volume.tar.gz` | Full backup only |

## Backup Options

### Full Backup (Including Docker Volumes)

```bash
sudo /opt/missioncontrol/scripts/backup.sh --full
```

### Skip Database Backup

```bash
sudo /opt/missioncontrol/scripts/backup.sh --no-db
```

### Custom Output Directory

```bash
sudo /opt/missioncontrol/scripts/backup.sh --output-dir /mnt/backup-share
```

## Backup Storage

Backups are stored in `/opt/missioncontrol/backups/`:

```
/opt/missioncontrol/backups/
├── missioncontrol_20260717_143022.tar.gz    (compressed archive)
├── missioncontrol_20260716_080000.tar.gz    (previous backup)
└── ...
```

- Maximum 10 backups are kept (oldest are removed automatically)
- Each backup is compressed with gzip
- Backup size depends on database size and plugin count

## Automated Backups

### Using Cron

Add to root's crontab:

```bash
# Daily backup at 2 AM
0 2 * * * /opt/missioncontrol/scripts/backup.sh --full >> /var/log/mission-control-backup.log 2>&1

# Weekly full backup to external storage
0 3 * * 0 /opt/missioncontrol/scripts/backup.sh --full --output-dir /mnt/backup-share
```

### Using Systemd Timer

Create `/etc/systemd/system/mc-backup.timer`:

```ini
[Unit]
Description=Mission Control Backup Timer

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

Create `/etc/systemd/system/mc-backup.service`:

```ini
[Unit]
Description=Mission Control Backup
After=docker.service

[Service]
Type=oneshot
ExecStart=/opt/missioncontrol/scripts/backup.sh --full
StandardOutput=journal
StandardError=journal
```

Enable:

```bash
systemctl enable --now mc-backup.timer
```

## Backup to External Storage

### NFS Mount

```bash
# Mount backup share
mount -t nfs backup-server:/exports/mc-backups /mnt/backup-share

# Backup to mounted share
sudo /opt/missioncontrol/scripts/backup.sh --output-dir /mnt/backup-share
```

### SCP to Remote Server

```bash
# Create backup
sudo /opt/missioncontrol/scripts/backup.sh

# Copy to remote
scp /opt/missioncontrol/backups/missioncontrol_*.tar.gz user@backup-server:/backups/
```

## Backup Verification

Verify a backup is valid:

```bash
# Check archive integrity
tar -tzf /opt/missioncontrol/backups/missioncontrol_20260717_143022.tar.gz > /dev/null && echo "Archive OK"

# List backup contents
tar -tzf /opt/missioncontrol/backups/missioncontrol_20260717_143022.tar.gz
```

## Restore from Backup

See [RESTORE.md](RESTORE.md) for restore instructions.

## Troubleshooting

### "Database backup failed"

- Check PostgreSQL is running: `docker compose ps postgres`
- Check database exists: `docker compose exec postgres psql -U mission_control -l`
- Manual backup: `docker compose exec postgres pg_dump -U mission_control mission_control | gzip > backup.sql.gz`

### "Permission denied"

- Run as root: `sudo ./backup.sh`

### Backup is very large

- Check database size: `docker compose exec postgres psql -U mission_control -d mission_control -c "SELECT pg_size_pretty(pg_database_size('mission_control'))"`
- Consider vacuuming: `docker compose exec postgres psql -U mission_control -d mission_control -c "VACUUM FULL"`
