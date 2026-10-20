# Target Architecture — Mission Control 2-VM Deployment (Phase 2 design)

**Status:** design for approval. Nothing in this document has been executed.
**Baseline:** `migration/audit-report.md` (Phase 1, verified evidence). This design changes nothing that
the audit did not justify.
**Labels:** **[V]** verified · **[A]** assumption · **[?]** unresolved · **[R]** recommendation.

---

## 1. Design summary

| | Frontend VM | Backend VM |
|---|---|---|
| Address | `10.0.0.26` (public `84.12.77.251`) | `10.0.0.33` (public `84.12.82.239`) |
| Provider / shape | OCI `VM.Standard.E2.1.Micro`, 1 OCPU, 956 MB, 45 GB, 0.5 Gbps [V] | same [V] |
| OS | Ubuntu 22.04.5, kernel `6.8.0-1062-oracle` [V] | same [V] |
| Role | public TLS termination, reverse proxy, SPA | API, PostgreSQL, Redis, backups |
| Containers | `mc-nginx`, `mc-frontend` | `mc-backend`, `mc-postgres`, `mc-redis` |
| Published ports | `80`, `443` (internet) | `8000` bound to `10.0.0.33` only |
| Host software | Docker + compose, certbot (webroot renewal), fail2ban, 2 GB swap | Docker + compose, 2 GB swap, backup timer |
| Not installed | PostgreSQL, Redis, Node.js, host nginx, ufw | PostgreSQL/Redis packages, Node.js, host nginx, certbot, ufw |

Deliberate differences from production: **no public Dockhand**, **no published port 3000**, **no host
edge agent**, log rotation enabled, backups scheduled, API docs not proxied publicly by default
(decision item — see §9).

---

## 2. Request path (target)

```
Internet ──443──▶ FE: mc-nginx ──┬─ /            ▶ mc-frontend:3000 (static SPA)
                                 ├─ /api/…       ▶ 10.0.0.33:8000 (mc-backend)
                                 └─ /.well-known/acme-challenge/ ▶ /var/www/letsencrypt (host dir)
Agent fleet ──443──▶ (same path) ── /api/v1/edge/* ──▶ BE:8000
BE: mc-backend ──▶ mc-postgres:5432 (internal)   mc-redis:6379 (internal, readiness only)
```

- No cross-host `depends_on` exists (impossible in Compose). Startup order is enforced per host.
- The API is reached over plain HTTP on the private VCN path; TLS terminates at the edge.
- `Host`, `X-Forwarded-For`, `X-Forwarded-Proto`, websocket `Upgrade` headers are preserved, matching
  today's behaviour.

---

## 3. Deployment layout (files)

New tracked directory `deploy/migration-2vm/` (created in Phase 3, not now):

```
deploy/migration-2vm/
  docker-compose.frontend.yml     # mc-nginx + mc-frontend
  docker-compose.backend.yml      # mc-backend + mc-postgres + mc-redis
  nginx/default.conf              # target edge config (derived from the live file)
  env/frontend.env.example        # no secrets
  env/backend.env.example         # key names only
  README.md                       # deploy + validate instructions
```

Runtime paths on the hosts:

| Host | Path | Content |
|---|---|---|
| FE | `/opt/missioncontrol/` | repository working tree (deployment source) |
| FE | `/opt/missioncontrol/deploy/migration-2vm/` | compose + nginx config for this host |
| FE | `/etc/letsencrypt/` | TLS material (copied, root-only) |
| FE | `/var/www/letsencrypt/` | ACME webroot (host-writable, mounted ro into nginx) |
| BE | `/opt/missioncontrol/` | repository working tree (backend runs bind-mounted from it) |
| BE | `/opt/missioncontrol/.env` | secrets, mode `600` |
| BE | `/var/backups/missioncontrol/` | nightly dumps, mode `700` |

**Backend parity note [V]:** production runs the backend from a bind mount (`./backend:/app`) and mounts
the repo at `/project` (`PROJECT_DIR=/project`). The target keeps both mounts so plugin behaviour is
unchanged. Consequence: the destination must carry the **working tree**, not a bare `git clone`.

---

## 4. Compose design — backend host

```yaml
# docker-compose.backend.yml (design sketch)
name: mc-be
services:
  postgres:
    image: postgres:16-alpine@sha256:57c72fd2a128…      # same digest as production
    restart: unless-stopped
    env_file: .env
    volumes: [ "mc-postgres-data:/var/lib/postgresql/data" ]
    healthcheck: { test: ["CMD-SHELL","pg_isready -U $POSTGRES_USER -d $POSTGRES_DB"], interval: 10s, timeout: 5s, retries: 5 }
    logging: { driver: json-file, options: { max-size: "10m", max-file: "3" } }
    # no ports — database stays internal
  redis:
    image: redis:7.2-alpine@sha256:dfa18828cbc0…
    restart: unless-stopped
    command: ["redis-server","--appendonly","yes"]
    volumes: [ "mc-redis-data:/data" ]
    healthcheck: { test: ["CMD","redis-cli","ping"], interval: 10s, timeout: 5s, retries: 5 }
    logging: { driver: json-file, options: { max-size: "10m", max-file: "3" } }
  backend:
    image: missioncontrol-backend:<git-sha>-<date>       # built off-host, loaded by digest/tag
    restart: unless-stopped
    env_file: .env
    depends_on:
      postgres: { condition: service_healthy }
      redis:    { condition: service_healthy }
    ports:
      - "10.0.0.33:8000:8000"     # private VCN only, never 0.0.0.0
    volumes:
      - ./backend:/app                       # parity with production
      - ../..:/project                       # PROJECT_DIR=/project
      - /var/run/docker.sock:/var/run/docker.sock   # docker plugin parity (see §8 risk)
    working_dir: /app
    environment:
      DOCKER_HOST: unix:///var/run/docker.sock
      PROJECT_DIR: /project
      SSH_AUTO_ADD_HOST_KEYS: "true"
    healthcheck:
      test: ["CMD","python","-c","import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/live',timeout=2)"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    logging: { driver: json-file, options: { max-size: "10m", max-file: "3" } }
volumes:
  mc-postgres-data:
  mc-redis-data:
```

Design notes:
- `MISSIONCONTROL_SECRET_KEY` comes from `.env` only (production currently sets it both inline and via
  `.env` — a duplicate source of truth; the target keeps the `.env` form only).
- No memory limits are imposed initially: measured production usage is 175 MB (backend), 47 MB
  (postgres), 4 MB (redis) [V], and hard limits on a 956 MB host risk avoidable OOM kills. Limits are a
  tuning step after a 24 h observation window (§7).
- `docker.sock` is retained because the Docker/System-Info plugins read it. It is a known
  privilege-escalation surface; a socket proxy is a post-migration hardening item, not a cutover change.

---

## 5. Compose design — frontend host

```yaml
# docker-compose.frontend.yml (design sketch)
name: mc-fe
services:
  frontend:
    image: missioncontrol-frontend:<git-sha>-<date>
    restart: unless-stopped
    expose: ["3000"]
    logging: { driver: json-file, options: { max-size: "10m", max-file: "3" } }
  nginx:
    image: nginx:1.27-alpine@sha256:65645c7bb6a0…
    restart: unless-stopped
    depends_on: { frontend: { condition: service_started } }
    ports: ["80:80", "443:443"]        # no 3000
    volumes:
      - ./nginx/default.conf:/etc/nginx/conf.d/default.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
      - /var/www/letsencrypt:/var/www/letsencrypt:ro
    healthcheck:
      test: ["CMD-SHELL","wget -q --spider --no-check-certificate https://127.0.0.1/api/v1/health/live || exit 1"]
      interval: 15s
      timeout: 5s
      retries: 3
    logging: { driver: json-file, options: { max-size: "10m", max-file: "3" } }
```

Nginx changes relative to the live config (full diff in `destination-diff.md`):

| Change | Reason |
|---|---|
| `proxy_pass http://10.0.0.33:8000` for `/api/` | cross-host API |
| remove `location /dockhand/` and the `/dockhand` redirect | D-B (not migrated) |
| remove `3000:3000` publish | dead today; unnecessary exposure |
| add `location ^~ /.well-known/acme-challenge/` before the 80 → 443 redirect | certificate renewal without stopping containers |
| healthcheck targets `/api/v1/health/live` (not static `/health`) | the current check does not prove the API is reachable |
| keep the live cipher list, websocket headers and 3600 s timeouts | preserve behaviour |
| keep `server_name` and the certificate paths | unchanged |
| `client_max_body_size` / buffering unchanged | agent inventory uploads depend on it |

---

## 6. TLS and renewal design

- Copy `/etc/letsencrypt` intact (both lineages) with modes preserved; `missioncontrol` expires
  **2027-01-06**, so cutover does not depend on renewal [V].
- Replace the standalone authenticator (which requires stopping nginx) with **webroot**:
  `certbot renew --webroot -w /var/www/letsencrypt` driven by the existing `certbot.timer`, with a
  deploy hook `docker exec mc-nginx nginx -s reload`.
- The webroot must be reachable over plain HTTP before the 301 redirect. The 301 stays for everything
  else.
- Renewal only works once DNS points at the FE VM; until then the copied certificate serves traffic.
- Fallback if webroot proves fragile: DNS-01 via the registrar API (adds a credential — decision item).
- The old `certbot-renewal.sh` (stops the container, unwritable log, `set -e`) is **not** carried.

---

## 7. Capacity design (D-A)

Measured environment [V]:

| Item | Value | Source |
|---|---|---|
| Production live usage | backend 175 MB, postgres 47 MB, redis 4 MB, nginx 5 MB, frontend 3 MB, dockhand 98 MB | `docker stats` 2026-10-20 |
| Destination RAM / swap | 956 MB / 0 MB, 42 GB free disk, 0.5 Gbps | audit |
| Image footprint | backend 647 MB, frontend 79 MB, nginx 75 MB, postgres 420 MB, redis 57 MB | audit |
| DB dump payload | 439 MB logical (420 MB `agent_commands`) | audit |
| Host-level headroom | dockerd ≈ 80–120 MB, page cache, journald | estimate [A] |

Recommendation [R]:
1. **Do not resize now.** Add a **2 GB swapfile** on both VMs as a safety net
   (`/swapfile`, `vm.swappiness=10`, persisted in `/etc/fstab`), because the current hosts have none and
   the source host has already OOM-killed a process once [V]. Disk impact is 2 GB of 42 GB free [V].
2. **Build images off-host** on the operator workstation (Docker 29.8.2, 8.1 GB RAM [V]) and transfer by
   `docker save | gzip | ssh docker load`. The FE VM cannot build a Vite bundle in 956 MB — it would be
   OOM-killed [A, high confidence].
3. Observe for 24 h after the backend is up; resize to a 2 OCPU / 8 GB shape only if: sustained host RAM
   > 80 %, any OOM kill, or page-cache thrash is observed.
4. Do not enable `zram` or aggressive overcommit to compensate; swap is for cold pages, not capacity.

---

## 8. Behaviour changes that must be accepted

| Change | Effect | Why |
|---|---|---|
| Docker plugin reads the **backend VM's** daemon | the Docker widget shows Mission Control's own containers instead of the old host's | parity with the mounted socket; unavoidable when the backend moves |
| `system_info` reports the backend VM | host identity card changes | `platform.node()` inside the container |
| Dockhand not migrated | `/dockhand/` disappears at cutover | D-B; it is unused and unauthenticated (evidence in `service-migration-matrix.md`) |
| Host edge agent not migrated | agent 3 goes offline when the old host is retired | D-C; it monitors only the host it runs on and has no dependants (evidence) |
| nginx healthcheck now depends on the API | nginx becomes `unhealthy` during API outages (it is not auto-restarted) | the current static check hides API failures |
| `/api/docs` and `/api/openapi.json` | recommendation: block at the edge on the destination | hardening; needs approval because it changes behaviour |

---

## 9. Unresolved questions and decisions

| # | Question | Impact | Owner action |
|---|---|---|---|
| U1 | Are the OCI destination public IPs **reserved**? | an ephemeral IP would break DNS after a stop/start | check OCI console before cutover |
| U2 | Exact OCI security-list rules (source scopes, 8000 rule) | private/public exposure guarantee | check console; design assumes 80/443 open, 8000 intra-VCN only |
| U3 | Should `/api/docs` + `/api/openapi.json` be blocked publicly? | information exposure vs. developer convenience | approve/deny |
| U4 | Keep the second certificate lineage (`missioncontroldev`, expires 2026-11-20) or drop it? | one fewer renewal target | decide |
| U5 | Is a Docker UI wanted at all on the new hosts (replacement for Dockhand)? | if yes: internal-only, authenticated, not proxied publicly | decide |
| U6 | Off-host backup destination and encryption key custody | RPO/recovery | decide in Phase 4 |
| U7 | `docker.sock` in backend: accept for cutover, or socket-proxy now? | security vs. change risk | recommendation: accept now, harden after |

---

## 10. Migration order (summary; detailed in the runbooks)

1. Build and stage images off-host (Phase 3).
2. Prepare FE/BE hosts: Docker, swap, firewall, directories, TLS copy (Phase 3).
3. Take and **restore-test** a backup (Phase 4 gate).
4. Bring up BE: postgres + redis + backend, restore data, validate locally (Phase 5).
5. Bring up FE: frontend + nginx pointed at BE, validate through the edge (Phase 6).
6. End-to-end validation, then cutover approval, then DNS (Phase 7+).
