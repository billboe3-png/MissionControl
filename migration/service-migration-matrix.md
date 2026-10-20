# Service Migration Matrix — Mission Control

**Phase 1 baseline:** 2026-10-20. Source host: GCP `34.35.177.209` (Ubuntu 24.04.5).
Destinations: frontend VM `10.0.0.26` (public `84.12.77.251`), backend VM `10.0.0.33`
(public `84.12.82.239`) — both OCI `VM.Standard.E2.1.Micro`, Ubuntu 22.04.5.

Legend — Destination: **FE** = frontend VM, **BE** = backend VM, **NEW** = new/created on destination,
**NONE** = not migrated. Data: sizes measured on the source on 2026-10-20.

| Service | Source Host | Image/Version | Configuration Location | Persistent Data | Dependencies | Destination | Required Changes | Validation |
|---|---|---|---|---|---|---|---|---|
| **nginx** (edge TLS/reverse proxy) | `34.35.177.209` | `nginx:1.27-alpine` @ `sha256:65645c7b…` | `nginx/default.conf` (bind-mounted, **uncommitted modification**); TLS from host `/etc/letsencrypt` (ro) | `/etc/letsencrypt` (root:root, dirs 0700), `/var/www/letsencrypt` (ACME webroot, unused today) | backend:8000, frontend:3000, dockhand:3000, TLS certs | **FE** | Split out of the single compose; `/api/` → `http://10.0.0.33:8000`; remove `/dockhand/` (or keep internal only); drop dead `3000:3000`; health check must exercise backend, not static `/health`; add log limits | `curl -kI https://<fe>/` 200; `/api/v1/health/live` 200; TLS CN + expiry; websocket upgrade works |
| **frontend** (SPA UI) | `34.35.177.209` | `missioncontrol-frontend:latest` @ `sha256:b07e18ec…` (built 2026-10-14) | `frontend/Dockerfile`, `frontend/nginx.conf` (listens 3000, SPA fallback); **no bind mount** — image is the artefact | none (static build in image) | nginx | **FE** | Rebuild image (do **not** build on a 956 MB VM — build elsewhere and `docker save/load`, or add swap); remove `depends_on: backend`; source build may differ from the 2026-10-14 bundle | `docker run` on FE; `curl http://<fe-container>:3000/` 200; bundle hash compared to source host's running image |
| **backend** (FastAPI/uvicorn) | `34.35.177.209` | `missioncontrol-backend:latest` @ `sha256:189883d1…` (built 2026-10-13) + **bind-mounted** `./backend:/app` | `.env` (9 keys), live `docker-compose.yml` env block (`DOCKER_HOST`, `MISSIONCONTROL_SECRET_KEY`, `PROJECT_DIR=/project`, `SSH_AUTO_ADD_HOST_KEYS`), `backend/Dockerfile` | `backend/app/data` (empty), `backend/app/logs` (empty); no uploads | postgres (healthy), redis (healthy), docker.sock (rw), `/project` bind | **BE** | Publish `8000` bound to `10.0.0.33`; remove nginx/frontend/dockhand deps; rebuild image and check `requirements.txt` delta; carry the **untracked** `official_veeam/agent_remote_target.py`; decide on `docker.sock` mount (recommend socket-proxy or ro); add log limits; set memory limits | `/api/v1/health/live` + `/api/v1/health/ready` 200; `/api/v1/version` = `3.0.0-rc1`; plugin load all-green in logs; one encrypted credential decrypts |
| **postgres** | `34.35.177.209` | `postgres:16-alpine` @ `sha256:57c72fd2…` (16.14) | `docker-compose.yml` service block; `.env` (`POSTGRES_DB/USER/PASSWORD`) | volume `missioncontrol_postgres_data` — **502 MB** (DB 439 MB, 78 tables) | — | **BE** | New volume; restore from `pg_dump -Fc` (pg_dump 16.14 in-container); keep DB/role names; alembic head `h7h8h9i1j2k3`; do **not** publish 5432 | `pg_isready`; table count 78; `alembic_version` = `h7h8h9i1j2k3`; row counts on top tables; restore log clean |
| **redis** | `34.35.177.209` | `redis:7.2-alpine` @ `sha256:dfa18828…` (7.2.14) | compose service block; `.env` (`REDIS_HOST/PORT`) | volume `missioncontrol_redis_data` — **20 KB**, `dbsize 0`, AOF on | — | **BE** | Recreate empty (nothing to replay); keep AOF setting; do not publish 6379 | `redis-cli ping`; `dbsize`; backend readiness reports redis ok |
| **dockhand** (Docker UI) | `34.35.177.209` | `fnsys/dockhand:v1.0.48` @ `sha256:63ffc7dd…` | compose service block + `SESSION_SECRET` env; proxied by nginx at `/dockhand/` | volume `missioncontrol_dockhand_data` — 956 KB | docker.sock (rw), nginx | **DECISION REQUIRED** (recommend: NONE publicly; if kept, BE internal only) | **Not** publicly exposed on the destination; `/dockhand/` removed from the public nginx config; if retained, bind to localhost/VPN and add authentication; never expose `/dockhand/api/*` | `curl https://<public>/dockhand/` must **not** return 200; if internal, only reachable on the private path |
| **host edge agent** (`mission-control-agent.service`) | `34.35.177.209` (host, not Docker) | code `/opt/mission-control-agent` (venv), systemd unit | `/etc/mission-control-agent/config.yaml` (`server_url`, `agent_id 3`, `verify_ssl: false`) | `/var/lib/mission-control-agent/edge.db` — **272 MB** + WAL | backend API over public DNS, plugins docker/linux | **DECISION REQUIRED** (recommend: NONE — retire, or move to BE and re-register) | If retired: remove/stop cleanly and confirm no dashboards depend on agent 3. If moved: copy code + config + state, adjust systemd, verify heartbeat | Agent appears online after cutover (or is intentionally absent); no `401 /api/v1/edge/0/*` spam |
| **TLS certificates + renewal** | `34.35.177.209` (host) | Let's Encrypt, `missioncontrol.optichosting.co.za`, expires **2027-01-06** | `/etc/letsencrypt` (renewal conf: standalone, no hooks); cron `certbot-renewal.sh`; `certbot.timer` | `/etc/letsencrypt` (certs+keys, root-only) | port 80 for standalone; DNS | **FE** | Move `/etc/letsencrypt` intact (or issue fresh at cutover); replace renewal with webroot/DNS-01 that does **not** stop containers; enable ACME location before the 301; recreate timer/cron; renewal only works once DNS points at FE | `openssl x509` CN/expiry on FE; `certbot renew --dry-run` succeeds with nginx running |
| **DNS / public entry point** | registrar → `34.35.177.209` | — | zone `optichosting.co.za`; TTL 360 s (observed) | — | FE public IP | **FE** | Lower TTL ≥24 h before cutover; switch A record at cutover; verify from external vantages (not the Windows workstation) | `dig` from 3 external resolvers → `84.12.77.251`; HTTPS 200 |
| **firewall / edge protection** | GCP VPC firewall + host iptables (INPUT ACCEPT) + fail2ban (184 bans) | — | GCP VPC rules (unreadable from host); `/etc/fail2ban`; `deploy/fail2ban-*.conf` | fail2ban DB | — | **FE + BE** | FE: 80/443 from internet, 22 restricted; BE: 8000 only from `10.0.0.26`, 22 restricted, no 5432/6379/3000. Destination `iptables` is **persisted** (`/etc/iptables/rules.v4`) and rejects everything but 22 — edit that file, not `ufw`; disable `rpcbind:111` | `iptables -S` shows intended rules after reboot; external port scan: only 80/443 open on FE |
| **monitoring / logging** | GCP Ops Agent; journald 4.0 G; json-file logs unbounded (backend 796 MB, nginx 371 MB) | — | `/etc/google-cloud-ops-agent`, logrotate (no docker entry) | journald | — | **FE + BE** (new) | Add `logging: max-size 10m / max-file 3` (stanza exists in stale `docker-compose.prod.yml`); decide monitoring (OCI Monitoring agent, or leave to app dashboards); no GCP agent on OCI | Log file sizes capped; `docker logs` accessible; no disk growth over 24 h |
| **backups** | **none exist** | — | `scripts/backup-db.ps1` / `restore-db.ps1` (Windows, unverified); stale `docs/administrator/BACKUP_AND_RESTORE.md` (2026-07-26) | — | `pg_dump` 16.14 | **BE** (new) + off-host storage | Create a scheduled encrypted `pg_dump -Fc` with retention; **restore-test before cutover**; back up `.env`, `/etc/letsencrypt`, working tree, agent state | Restore into scratch DB reproduces 78 tables + row counts; dump age < 24 h |
| **test fixtures** (`mc-test-postgres`, `mc-test-redis`, 19 dead containers, ~20 unused volumes) | `34.35.177.209` | `postgres:16-alpine`, `redis:7-alpine` | none (manual) | none of value | — | **NONE** | Do not migrate; leave source untouched during the migration | — |

## Dependency chain (as deployed)

```
postgres (healthy) ─┐
redis (healthy) ────┴→ backend (healthy) ─┬→ frontend (started) ─┐
                                          └→ nginx (started)     ├→ nginx
dockhand (started) ───────────────────────────────────────────────┘
```

**Target chain after the split** — no cross-host `depends_on` is possible:

```
FE:  nginx → frontend:3000 (same host)          + nginx → 10.0.0.33:8000 (over the private path)
BE:  postgres (healthy) ─┐
     redis (healthy) ────┴→ backend (healthy)
```

## Secrets / key material (must move, never committed)

| Item | Location on source | Handling |
|---|---|---|
| `MISSIONCONTROL_SECRET_KEY` (Fernet; decrypts 33 stored credentials) | `/opt/MissionControl/.env` (mode **664 — world-readable**) | Transfer over SSH only; set 600 on the destination; **byte-identical**; verify one decryption after restore |
| DB credentials | `.env` (`POSTGRES_*`) | Same transfer; do not rotate unless approved |
| Redis host/port | `.env` (`REDIS_*`) | Service name `redis` resolves inside compose only |
| TLS private key + chain | `/etc/letsencrypt/archive/...` (root 0600) | `rsync`/`tar` over SSH as root; preserve modes |
| Remote-agent API keys | DB (`agents` table) + `agent-data/config.yaml` (mode 664) | Travel with the DB; restrict file modes on the destination |
| SSH access to managed hosts | `~/.ssh` on source + encrypted DB rows | Not migrated unless required by a plugin that runs on BE |
