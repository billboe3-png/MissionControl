# Current Architecture — Mission Control (Phase 1 baseline)

**Captured:** 2026-10-20, production live. Read-only audit; no configuration was changed.
**Source of truth for values:** `audit-report.md` (with evidence classes) and `software-inventory.md`.

---

## 1. Topology (as deployed today)

```
                              Internet
                                 │
                 ┌───────────────┴────────────────┐
                 │  DNS: missioncontrol.           │
                 │  optichosting.co.za             │
                 │  → 34.35.177.209 (GCP)          │
                 └───────────────┬────────────────┘
                                 │  TCP 80 (301→443), 443
┌────────────────────────────────┴───────────────────────────────────────────┐
│ GCP  e2-medium  2 vCPU / 3.9 GB / 77 GB  ·  Ubuntu 24.04.5                 │
│ Docker Engine 29.9.1 · compose v5.6.0 · project `missioncontrol`           │
│                                                                            │
│  ┌─────────────────────────── missioncontrol_nginx (bridge 172.19.0.0/16) ─┐│
│  │                                                                         ││
│  │  nginx:1.27-alpine  ── :80/:443 exposed to the internet                 ││
│  │    ├── /            → frontend:3000   (SPA)                             ││
│  │    ├── /api/*       → backend:8000    (REST, websocket upgrade)         ││
│  │    ├── /health      → 200 "ok"        (static; container healthcheck)    ││
│  │    └── /dockhand/*  → dockhand:3000   (**unauthenticated, public**)      ││
│  │                                                                         ││
│  │  frontend  missioncontrol-frontend:latest (image-only, static on 3000)  ││
│  │  backend   missioncontrol-backend:latest  (uvicorn, bind ./backend:/app) ││
│  │  postgres  postgres:16-alpine  16.14   vol missioncontrol_postgres_data  ││
│  │  redis     redis:7.2-alpine    7.2.14  vol missioncontrol_redis_data     ││
│  │  dockhand  fnsys/dockhand:v1.0.48      vol missioncontrol_dockhand_data  ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                            │
│  Host-level (outside Docker):                                              │
│    mission-control-agent.service   agent_id 3, /var/lib/mission-control-…  │
│    nginx TLS material: /etc/letsencrypt (ro, root-only)                    │
│    fail2ban (sshd + recidive, 184 banned) · Google Cloud Ops Agent         │
│    certbot.timer (standalone) + ~/.hermes certbot-renewal.sh (03:00)       │
└────────────────────────────────────────────────────────────────────────────┘
          ▲                                   ▲
          │ HTTPS (poll 5–15 s)               │ SSH (plugin operations)
          │                                   │
   ~15 remote agents                    managed hosts (Veeam, Zabbix,
   (customer sites)                     MikroTik, D-Link, UniFi, Hyper-V…)
```

---

## 2. Request and data flows

| Flow | Path | Notes |
|---|---|---|
| Browser UI | Internet → nginx:443 → `frontend:3000` (static SPA) | SPA calls the API with **relative** `/api/v1/...` paths; no build-time API URL |
| Browser API | nginx `/api/` → `backend:8000` (plain HTTP, compose bridge) | Websocket upgrade enabled with 3600 s read timeout |
| Agent polling | Internet → nginx → `backend:8000` (`/api/v1/edge/<id>/commands`, `/config`, `/bundle/download`, `/inventory`, `/heartbeat`, `/command-result`) | Agents authenticate with an agent API key; ~every 5–15 s from 15 agents |
| Backend → agents | SSH from backend container (egress) | Used by plugins (Veeam relay, Hyper-V, etc.); `SSH_AUTO_ADD_HOST_KEYS=true` |
| Backend → PostgreSQL | compose network `postgres:5432` | Credentials from `.env` |
| Backend → Redis | compose network `redis:6379` | **Health/readiness only**; no cache, sessions, queues or locks. `dbsize 0` |
| Backend → Docker | host `/var/run/docker.sock` mounted **rw** | Docker plugin + system_info report the container host |
| nginx → dockhand | compose network `dockhand:3000`, published at `/dockhand/` | No authentication; dockhand itself has `docker.sock` rw |
| DNS cutover surface | agents are configured with `https://missioncontrol.optichosting.co.za` | A DNS change moves the whole fleet with no agent reconfiguration |

---

## 3. Boot / dependency order (live compose)

```
postgres (healthy) ─┐
redis (healthy) ────┴→ backend (healthy) ─┬→ frontend (started)
                                          └→ nginx (started)
dockhand (started) ─────────────────────────→ nginx
```

All six services live in **one** compose project and one file. `docker-compose.prod.yml` and
`docker-compose.production.yml` exist in the repo but are **stale and unused** (the first contains the
log-rotation stanza the live file lacks; the second is a two-line override fragment).

---

## 4. Storage map

| Data | Where | Size | Migrated as |
|---|---|---|---|
| Application database | volume `missioncontrol_postgres_data` | 502 MB (logical DB 439 MB) | `pg_dump -Fc` + restore (preferred) |
| Redis | volume `missioncontrol_redis_data` | 20 KB, 0 keys | recreate empty |
| Dockhand state | volume `missioncontrol_dockhand_data` | 956 KB | only if dockhand is retained |
| Edge-agent state | host `/var/lib/mission-control-agent/edge.db` (+WAL/SHM) | 272 MB | only if the host agent is migrated |
| Repo + code | `/opt/MissionControl` working tree | 553 MB (`backend` 233 MB, `frontend` 277 MB) | working tree over SSH (not a bare clone) |
| TLS | host `/etc/letsencrypt` | — | copy intact with modes |
| App data/uploads | `backend/app/data`, `backend/app/logs` | empty | nothing to move |
| Container logs | Docker json-file | backend 796 MB, nginx 371 MB | **not** migrated |

---

## 5. Security boundary (current)

| Control | State |
|---|---|
| Public ingress | 80 (301→443), 443, 22. Port 3000 is published by compose but closed at the provider firewall |
| Host firewall | `ufw` **inactive**; iptables INPUT ACCEPT; external filtering is the GCP VPC firewall |
| SSH | key-only, `PermitRootLogin without-password`; fail2ban active (184 bans) |
| TLS | Let's Encrypt, TLSv1.2, RSA; expiry **2027-01-06**; renewal broken |
| Container privileges | `docker.sock` rw in **backend** and **dockhand**; no `privileged`, no host network |
| Secrets at rest | `.env` mode **664** (world-readable); `agent-data/config.yaml` mode 664 containing a live agent key; 33 encrypted credentials in the DB bound to `MISSIONCONTROL_SECRET_KEY` |
| Publicly exposed extras | `/dockhand/` + `/dockhand/api/*` (**unauthenticated**), `/api/docs`, `/api/openapi.json` |

---

## 6. External integrations observed

- **Agents** (~15 in the DB, poll every 5–15 s; heartbeat 30 s; inventory 300 s).
- **Plugins with background sync loops**: docker (120 s), dlink, mikrotik, unifi, zabbix, veeam, git,
  hyperv, system_info. These run **inside the single backend process** (asyncio tasks) — no Celery, no
  broker, no external scheduler.
- **Host edge agent** (`agent 3`, "prod-01") runs plugins `docker` and `linux` against the local host.
- **Monitoring**: Google Cloud Ops Agent (GCP-specific, does not migrate).

---

## 7. Failure domains / capacity reality

- One host runs everything. A host-level OOM (observed 2026-10-20 14:06 UTC) is a total-outage event.
- No swap on any of the three hosts.
- No backups of the database exist; `archive_mode=off`, so there is no PITR.
- `agent_commands` dominates storage (420 MB of 439 MB) and grows ~2 k rows/day.
- nginx has restarted 27 times since 2026-10-14 (cause unknown; not currently failing).

---

## 8. Target architecture (for approval in Phase 2 — not yet built)

```
                 Internet (443)
                       │
        ┌──────────────┴──────────────┐
        │ FE  10.0.0.26 / 84.12.77.251 │   OCI, Ubuntu 22.04.5, 956 MB (+ swap)
        │  nginx:443 ── / → frontend:3000
        │           └── /api/ → http://10.0.0.33:8000
        │  /etc/letsencrypt (moved), ACME webroot/DNS-01 renewal
        └──────────────┬──────────────┘
                       │ private 10.0.0.0/24 (all ports permitted; FE→BE:8000 only)
        ┌──────────────┴──────────────┐
        │ BE  10.0.0.33 / 84.12.82.239 │   OCI, Ubuntu 22.04.5, 956 MB (+ swap)
        │  backend:8000 (published to 10.0.0.33 only)
        │  postgres:5432 (internal), redis:6379 (internal)
        └─────────────────────────────┘
```

Deliberate differences from today: no public dockhand, no public port 3000, no host edge agent
(unless approved), no `docker.sock` on the frontend host, log rotation enabled, backups scheduled.

Full design detail — compose split, TLS renewal, firewall rules, capacity model — is in
`target-architecture.md`, `network-security-plan.md` and `destination-diff.md`.

---

## 9. Phase 2 evidence updates (2026-10-20)

Targeted read-only checks added during Phase 2. These refine, and in one case correct, the Phase 1
record.

### 9.1 Correction — the untracked Veeam module is **not** imported

Phase 1 stated that the backend imports the untracked
`official_veeam/agent_remote_target.py` and that a git-only deploy would fail at import. Re-verified:

```
grep -rn 'agent_remote_target' backend --include='*.py'
  → backend/app/models/db/agent_remote_target.py      (tracked, canonical model)
  → importers of app.models.db.agent_remote_target     (bridge/collector code)
  → the plugin-local copy: definition only, no importer
```

The plugin-local file defines the same table as the tracked model and is a **dead duplicate**. It is
preserved in the provenance branch but excluded from the deployment. See `destination-diff.md` §2.2.

### 9.2 Dockhand is effectively unused (D-B evidence)

| Signal | Value |
|---|---|
| `dockhand.db` users / sessions | **0 / 0** |
| Dockhand authentication | `auth_settings.auth_enabled = 0` (disabled) |
| Environments, git repos, stacks, backups configured | 0 |
| nginx requests to `/dockhand*` (whole log) | 326, of which 282 were not our audit `curl` |
| Nature of the real traffic | one browser session from an owner device (14 Oct) that received `404`s on `/dockhand/api/...`, i.e. the SPA loads but its API calls fail under the sub-path |
| Production dependencies on it | none found in the repo, compose, scripts or the database |

Conclusion: no operational dependency; the only human user is the owner, and the UI is partly broken as
deployed. Supports "do not migrate; close the route" (D-B/D-F) rather than "re-platform it".

### 9.3 Host edge agent — role established (D-C evidence)

| Signal | Value |
|---|---|
| Service | `mission-control-agent.service`, systemd, venv at `/opt/mission-control-agent` |
| Registered as | agent **id 3** |
| Agent row | reports itself as the host it runs on (source host, private `10.218.0.4`); `last_heartbeat` is current (live) |
| Plugins | `docker` (unavailable — local image lookup error), `linux` inventory |
| Local state | `/var/lib/mission-control-agent/edge.db`, 272 MB: `sync_log` ≈ 456 k rows, heartbeat/inventory tables — a local send buffer |
| Commands ever dispatched to it | **2**, last on 2026-09-22 |
| References from `agent_remote_targets` / integration profiles | **none** reference agent 3 |
| Automation depending on it | none found |

Conclusion: it monitors **the machine it is installed on** and buffers its own telemetry. Its value ends
with the source host. Recommendation: retire with the source host; if host-level inventory of the new
backend VM is wanted later, install a **fresh** agent there post-cutover (new agent id, new API key) as a
separate change. The 272 MB state is not migrated.

### 9.4 `agent_commands` profile (D-D evidence)

98,015 rows; 420 MB total (heap 64 MB, indexes 8.9 MB, TOAST ≈ 347 MB); ~4.5 KB/row; status split
completed 64,450 / failed 33,564 / dispatched 1; **no foreign keys reference it**; growth 2.6–5.4 k
rows/day over the last 10 days. Migrated in full; pruning deferred to a separate retention policy.
Details and estimates in `backup-manifest.md` §4.

### 9.5 Working tree and uncommitted configuration (D-E evidence)

Two modified tracked files (compose, nginx) plus 13 untracked entries, largely build artefacts.
Preserved in branch `migration/prod-live-snapshot-2026-10-20` (commit `75a8280`) created in a temporary
worktree so the running checkout was never altered; live file hashes re-verified afterwards. Classification
and exclusions in `destination-diff.md` §2.

### 9.6 Build host capability (D-A evidence)

The operator workstation runs **Docker 29.8.2 / compose 5.5.1 with 8.1 GB RAM**, so off-host image builds
are available without touching the 956 MB VMs. Destination hosts remain Docker-free at design time.

