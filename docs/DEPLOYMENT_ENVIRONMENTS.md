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

- Run `scripts/backup-db.ps1` against LIVE PostgreSQL container.
- Store backups outside application containers and outside DEV environments.

## Rollback

- Identify last known-good Git commit on `main`.
- Redeploy LIVE from that commit.
- Database rollback is a separate concern; if a migration is irreversible, restore from the most recent LIVE backup.
