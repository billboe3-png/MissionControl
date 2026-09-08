# Mission Control — Deployment Environments

## Environments

### DEV

- URL: https://missioncontroldev.optichosting.co.za
- Git branch: `develop`
- Compose project: `missioncontrol-dev`
- Database: `missioncontrol_dev`
- Redis DB: logical DB 0 via `redis` service in DEV compose project
- Env file: `.env.dev` or `.env.dev.example`
- Nginx upstreams: `missioncontrol-dev-backend-1`, `missioncontrol-dev-frontend-1`

### LIVE

- URL: https://missioncontrol.optichosting.co.za
- Git branch: `main`
- Compose project: `missioncontrol-live`
- Database: `missioncontrol_live`
- Redis DB: logical DB 0 via `redis` service in LIVE compose project
- Env file: `.env.production` or `.env.production.example`
- Nginx upstreams: `missioncontrol-live-backend-1`, `missioncontrol-live-frontend-1`

## Docker Architecture

Base compose file: `docker-compose.yml`
Overrides:
- `docker-compose.dev.yml`
- `docker-compose.production.yml`

## Secrets

- Never commit real secrets.
- `.env.dev` and `.env.production` are gitignored.
- Rotate `MISSIONCONTROL_SECRET_KEY` between DEV and LIVE.

## Deployment

### DEV

```bash
git checkout develop
git pull origin develop
COMPOSE_PROJECT_NAME=missioncontrol-dev ENV_FILE=.env.dev ./scripts/deploy-dev.sh
```

### LIVE

```bash
git checkout main
git pull origin main
COMPOSE_PROJECT_NAME=missioncontrol-live ENV_FILE=.env.production ./scripts/deploy-live.sh
```

## Backup

### DEV backup

```bash
COMPOSE_PROJECT_NAME=missioncontrol-dev POSTGRES_DB=missioncontrol_dev ./scripts/backup-db.ps1 backups
```

### LIVE backup

```bash
COMPOSE_PROJECT_NAME=missioncontrol-live POSTGRES_DB=missioncontrol_live ./scripts/backup-db.ps1 backups
```

Store backups outside application containers and outside DEV environments. Recommended naming: `missioncontrol_<project>_<timestamp>.sql.gz`.

## Restore

### DEV restore

```bash
COMPOSE_PROJECT_NAME=missioncontrol-dev POSTGRES_DB=missioncontrol_dev ./scripts/restore-db.ps1 backups/missioncontrol_missioncontrol-dev_20260822_120000.sql.gz
```

### LIVE restore

```bash
COMPOSE_PROJECT_NAME=missioncontrol-live POSTGRES_DB=missioncontrol_live ./scripts/restore-db.ps1 backups/missioncontrol_missioncontrol-live_20260822_120000.sql.gz
```

## Backup validation

```bash
bash scripts/validate_backup.sh -e dev
bash scripts/validate_backup.sh -e live
```

## Rollback

1. Identify last known-good Git commit on the target branch (`main` for LIVE, `develop` for DEV).
2. Redeploy that branch/commit via the appropriate deploy script.
3. If a database migration is irreversible and must be undone, restore the most recent environment-specific backup using the restore script above.
4. Do not migrate backups between environments; DEV and LIVE backups are not interchangeable due to different databases and secrets.
