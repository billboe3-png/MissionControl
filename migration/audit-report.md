# Phase 1 Audit Report — Mission Control Migration

**Status:** Phase 1 complete — awaiting approval before Phase 2 (design/change plan).
**Audit date:** 2026-10-20 (UTC), 15:55–16:20. Independent re-verification of critical claims by the
lead agent: 16:20–16:35 UTC.
**Scope:** read-only. No containers stopped, no packages installed, no firewall/DNS/config changed,
no secret values read into any document.

**Method:** three independent read-only specialist investigations (production audit; destination and
networking audit; security, backup and recovery review), followed by lead-agent re-verification of
every claim that changes the migration design. Raw reports are kept outside the repository
(`.superpowers/sdd/2026-10-20-controlled-docker-migration/report-*.md`, untracked scratch) because
they contain host identifiers and low-level detail; this document is the authoritative summary.

**Evidence classes used below:**
- **[V]** verified by a command run during the audit (and re-verified by the lead where marked ✓).
- **[A]** assumption — plausible, not directly verified.
- **[?]** unknown — cannot be established with the access available. Listed with what would resolve it.

---

## 1. Executive summary

The migration target (2 VMs: nginx+frontend / backend+PostgreSQL+Redis) is viable, but **three
findings change the shape of Phase 2**:

1. **The source is Google Cloud Ubuntu 24.04, not Oracle Cloud Ubuntu 22.04.** [V ✓] The plan's
   premise ("all servers are Oracle Cloud VMs") is wrong for production. Destination VMs are OCI
   `VM.Standard.E2.1.Micro` (1 GB RAM each). Firewall work is split: GCP rules on the source (no
   action), OCI security lists + **host-persisted iptables** on the destinations.
2. **There is no backup of anything, anywhere.** [V ✓] No `pg_dump` job, no dump on disk,
   `archive_mode=off`, no WAL archiving. The 439 MB database exists only in the live Docker volume.
   The source host already OOM-killed a 1.5 GB process on 2026-10-20.
3. **`/dockhand/` is publicly served without authentication and has the Docker socket mounted rw.**
   [V ✓] `GET /dockhand/api/containers` returns 200 to an anonymous internet client. That is host
   root for anyone who finds it. It must not be reproduced on the destination and should be closed
   on production independently of this migration.

Additionally, the live deployment is **not reproducible from git**: `docker-compose.yml` and
`nginx/default.conf` are uncommitted working-tree edits. [V ✓] A clean clone produces a different stack.

> **Correction added in Phase 2 (2026-10-20):** Phase 1 also stated that the running backend imports an
> **untracked** module (`official_veeam/agent_remote_target.py`) and would fail at import from a clean
> clone. Re-verification for Phase 2 disproved this: `grep -rn 'agent_remote_target' backend --include='*.py'`
> shows the canonical, **tracked** model at `backend/app/models/db/agent_remote_target.py` and its importers.
> The plugin-local copy is a **dead duplicate** with no importer. The reproducibility problem above remains
> valid on the strength of the two uncommitted config files alone. See `destination-diff.md` §2.2.

**No production change is required to complete Phase 1. Nothing was changed.**

---

## 2. Current architecture (authoritative)

See `current-architecture.md` for the full topology. Summary:

| Host | Provider / shape | OS | Role today |
|---|---|---|---|
| `34.35.177.209` (`instance-20260724-161348`) | GCP `e2-medium`, 2 vCPU / 3.9 GB / 77 GB | Ubuntu 24.04.5 | **everything**: nginx, frontend, backend, PostgreSQL, Redis, dockhand, host edge agent |
| `84.12.77.251` / `10.0.0.26` | OCI `VM.Standard.E2.1.Micro`, 956 MB / 45 GB | Ubuntu 22.04.5 | empty (target: nginx + frontend) |
| `84.12.82.239` / `10.0.0.33` | OCI `VM.Standard.E2.1.Micro`, 956 MB / 45 GB | Ubuntu 22.04.5 | empty (target: backend + PostgreSQL + Redis) |

Single Docker Compose project `missioncontrol`, one compose file
`/opt/MissionControl/docker-compose.yml`, six services: `nginx`, `frontend`, `backend`, `postgres`,
`redis`, `dockhand`. External traffic terminates at nginx on 80/443 (80 is a 301 to https).
~15 remote agents poll `https://missioncontrol.optichosting.co.za` every few seconds.

---

## 3. Verified facts

### 3.1 Production host

| Item | Value | Class |
|---|---|---|
| Cloud / zone | GCP `africa-south1-b`, machine type `e2-medium` | [V ✓] |
| OS / kernel / arch | Ubuntu 24.04.5 LTS (noble), `7.0.0-1014-gcp`, x86_64 | [V ✓] |
| CPU / RAM / swap | 2 vCPU, 3908 MB, **no swap** | [V ✓] |
| Disk | 77 G, 38 G used (50 %), 39 G free; `/var/lib/docker` 3.7 G; journald 4.0 G | [V] |
| Docker / Compose | Engine 29.9.1 (API 1.56), compose plugin v5.6.0, overlayfs, cgroup v2 | [V] |
| Containers | 6 running (nginx, frontend, backend, postgres, redis, dockhand); 19 stopped leftovers | [V] |
| Compose project | `missioncontrol` from `/opt/MissionControl/docker-compose.yml` only | [V ✓] |
| Published ports | 80, 443 (and a dead 3000) — all on nginx; backend/postgres/redis/dockhand unpublished | [V ✓] |
| Host firewall | `ufw` **inactive**; iptables INPUT ACCEPT; fail2ban active (184 banned IPs); external policy is GCP VPC firewall | [V] |
| Logging | `json-file`, **no rotation**; backend log 796 MB, nginx 371 MB | [V] |
| Monitoring | Google Cloud Ops Agent only (ports 20201/20202); no Prometheus/Zabbix agent | [V] |
| Backups | **none**; `archive_mode=off`; no `.sql`/`.dump` on disk | [V ✓] |
| OOM event | 2026-10-20 14:06:52 UTC — global OOM killed a 1.5 GB `python` process | [V] |
| Time / DNS | NTP via systemd-timesyncd; public DNS `missioncontrol.optichosting.co.za → 34.35.177.209` | [V ✓] |

### 3.2 Services as deployed

| Service | Image (digest short) | Runtime facts |
|---|---|---|
| nginx | `nginx:1.27-alpine` (`65645c7bb6a0`) | Config bind-mounted from `nginx/default.conf` (**modified vs git**); `/etc/letsencrypt` ro; healthcheck hits static `/health`, not the backend |
| frontend | `missioncontrol-frontend:latest` (`b07e18ec599e`, built 2026-10-14) | **Image-only** (no mount). Serves the built SPA on 3000 behind nginx |
| backend | `missioncontrol-backend:latest` (`189883d1c49a`, built 2026-10-13) | Runs **bind-mounted** `./backend:/app`; single uvicorn process, no workers/celery; image is 7 days older than the code |
| postgres | `postgres:16-alpine` (`57c72fd2a128`) | 16.14, volume `missioncontrol_postgres_data` (502 MB) |
| redis | `redis:7.2-alpine` (`dfa18828cbc0`) | 7.2.14, AOF on, **dbsize 0** — liveness dependency only |
| dockhand | `fnsys/dockhand:v1.0.48` (`63ffc7dd086f`) | Docker UI, `docker.sock` rw, proxied at `/dockhand/` **without auth** |
| host agent | `mission-control-agent.service` (not a container) | `agent_id 3`, code `/opt/mission-control-agent`, config `/etc/mission-control-agent/config.yaml`, state `/var/lib/mission-control-agent/edge.db` (**272 MB**), `verify_ssl: false` |

### 3.3 Data

| Item | Value | Class |
|---|---|---|
| DB size | `mission_control` **439 MB**, 78 tables, UTF8 / `en_US.utf8`, public schema only | [V ✓] |
| Largest table | `agent_commands` **420 MB** of which ~347 MB is TOAST; 97 529 rows (2026-09-18 → 2026-10-20) | [V ✓] |
| Extensions / roles | `plpgsql` only; role `mission_control` is **superuser** | [V] |
| Alembic | repo head = DB version = `h7h8h9i1j2k3` (no alembic drift) | [V ✓] |
| Runtime schema drift | `mikrotik_servers.allow_insecure_ssl` missing (logged every 5 min); `plugin_configs`, `agents.last_seen`, `host_url` also absent | [V] |
| Encrypted secrets at rest | 16/16 `agent_remote_targets.password_encrypted`, 15/15 `veeam_backup_servers.legacy_ssh_password_encrypted`, 2/6 `integration_profiles.encrypted_secret` = **33 ciphertexts bound to `MISSIONCONTROL_SECRET_KEY`** | [V] |
| Redis | `dbsize 0`; app uses Redis only for health/readiness | [V ✓] |
| Uploads / user files | none (`backend/app/data` empty) | [V] |
| Other persistent state | dockhand volume 956 KB; host agent `edge.db` 272 MB; no backups | [V] |

### 3.4 TLS and renewal

- Certificate served: `CN=missioncontrol.optichosting.co.za`, Let's Encrypt, **expires 2027-01-06 07:34 UTC**. [V ✓]
- Second lineage `missioncontroldev.optichosting.co.za` expires 2026-11-20; not referenced by nginx. [V]
- Renewal is **not healthy**: `certbot.timer` uses **standalone** on port 80 (held by the nginx
  container), and the 03:00 user cron script `certbot-renewal.sh` fails on its first line
  (`/var/log/certbot-renewal.log` unwritable by `billboe3`, `set -e` aborts) before certbot runs.
  The script also **stops and starts the nginx container** to free port 80. [V ✓]
- There is no ACME challenge location in the live nginx config; port 80 is a blanket 301. [V]

### 3.5 Reproducibility of the deployment

- `docker-compose.yml` and `nginx/default.conf` are **modified, uncommitted** on the server — they
  are the live configuration (dockhand service, `/dockhand/` proxy, `/health` check, cipher list,
  websocket timeouts). [V ✓]
- The running backend **imports an untracked module**:
  `backend/app/plugins/installed/official_veeam/agent_remote_target.py` (untracked per `git status`,
  import succeeds inside the container). [V ✓]
  **Corrected in Phase 2 — see the note in §1.** The file is a dead duplicate of the tracked
  `backend/app/models/db/agent_remote_target.py`; no module imports it. The file is untracked, but it is
  **not** a runtime dependency.
- Untracked `deploy/2vm/` is an OCI migration scaffold written earlier today (not committed). [V]
- Other untracked artifacts: agent installers/zips, `backend/tests/test_agent_token_service.py`,
  `test_veeam_collector.py`, `test_veeam_column_case.py` (the last imports a nonexistent symbol).
- Local Windows checkout is **not** the live line: local HEAD `8b996bd` does not contain the server
  commits `0123e0c..ca2d267`. The server tree is authoritative. [V]

### 3.6 Destination VMs

| Item | Frontend VM (`.26`) | Backend VM (`.33`) | Class |
|---|---|---|---|
| Provider / shape | OCI `af-johannesburg-1`, `VM.Standard.E2.1.Micro` (1 OCPU, 956 MB, 0.5 Gbps) | same | [V ✓] |
| OS / kernel | Ubuntu 22.04.5 LTS, `6.8.0-1062-oracle`, x86_64 | same | [V ✓] |
| RAM / swap | 956 MB / **none** | 956 MB / **none** | [V ✓] |
| Disk / inodes | 45 G, 42 G free, ~5.9 M inodes free | same | [V ✓] |
| Docker / git / pip / node / nginx / certbot / fail2ban / ufw | **all absent** | **all absent** | [V ✓] |
| Host firewall | `iptables` persisted in `/etc/iptables/rules.v4` (`netfilter-persistent`): allow 22, **REJECT everything else** | identical | [V ✓] |
| `ip_forward` / FORWARD | `0` / REJECT | `0` / REJECT | [V ✓] |
| Listening | sshd 22, rpcbind **111**, resolved stub | same | [V ✓] |
| Egress | Docker Hub, ghcr, quay, pypi, npm, GitHub, Ubuntu mirrors all reachable | same | [V] |
| Private path `.26 ↔ .33` | all ports delivered; only 22 has a listener — **8000 is not cloud-blocked, only host-firewall-rejected** | same | [V ✓] |
| Public ingress | 80/443 reach the host from the internet (host rejects); 22 is source-allowlisted | same | [V] |

---

## 4. Assumptions (plausible, not verified)

- [A] The GCP VPC firewall allows only 80/443/22 to production and blocks 3000 (empirically 3000 is
  closed; the rule set itself is unreadable without GCP credentials).
- [A] The OCI destination public IPs are **reserved** (1:1 NAT confirmed; reservation type is not
  readable from inside the instance).
- [A] Rebuilding `missioncontrol-frontend` from current source reproduces the 2026-10-14 bundle
  closely enough; it is not bit-identical to what production serves.
- [A] Backend `requirements.txt` has not changed since the 2026-10-13 image build (the container runs
  current code on older dependencies — needs a rebuild or a delta check).
- [A] The 15 remote agents tolerate a short outage (< one poll+exec window) during cutover.
- [A] No external system hard-codes the source IP `34.35.177.209` (all agent configuration found uses
  the DNS name).

## 5. Unknowns (and what resolves each)

| Unknown | Resolver |
|---|---|
| Exact GCP firewall rules / source ranges | GCP console or `gcloud` credentials (none on host) |
| Exact OCI security-list / NSG rules; whether 80/443 is truly `0.0.0.0/0`; the `8000` source scope | OCI console |
| Whether `84.12.77.251` / `84.12.82.239` are reserved | OCI console |
| Why the Windows workstation is dropped on destination 80/443 while six other nodes reach them | OCI console (possible Network Firewall/WAF); do not use this workstation as the only cutover check |
| Cause of nginx's 27 restarts | not recoverable (docker events not retained) |
| Whether `agent_commands` (420 MB, mostly TOAST) can be pruned | owner decision, not an audit finding |
| DNS TTL / zone detail | registrar/DNS provider; one resolver was seen caching for ~45 h |

---

## 6. Discrepancies between the plan, the repository and reality

| # | The plan/repo says | Reality | Impact |
|---|---|---|---|
| D1 | "All servers are Oracle Cloud Ubuntu VMs" | Source is **GCP Ubuntu 24.04**; destinations are OCI Ubuntu 22.04 | Firewall/ops steps must be provider-specific |
| D2 | Deployment reproducible from git | Live compose + nginx conf uncommitted; backend imports an untracked module | A git-only deploy is broken at import and loses dockhand/`/health` |
| D3 | Preserve existing architecture | An untracked `deploy/2vm/` scaffold exists targeting OCI 1 GB/Ubuntu 22.04 | Prior (unfinished) work overlaps this migration; must be reconciled, not duplicated |
| D4 | Docker absent on destinations | Confirmed absent — but so are git, pip, node, nginx, certbot, fail2ban, ufw | Phase 3 is broader than "install Docker" |
| D5 | "Oracle security lists" | Destinations also run **persisted host iptables** rejecting all but 22 | Opening ports requires editing `/etc/iptables/rules.v4`; `ufw` commands will fail |
| D6 | Backend listens on 8000 for nginx | Backend is `expose`d only; cross-host nginx needs a published port bound to `10.0.0.33:8000` | Concrete compose change required in Phase 2 |
| D7 | Compose file as a unit | Cross-host `depends_on` (nginx→backend/frontend/dockhand; frontend→backend) | A split per-host compose is **mandatory**, not optional |
| D8 | Frontend/nginx move together | Frontend is an image-only container; nginx is a separate edge proxy | Two images, two configs, one host |
| D9 | (not mentioned) | `dockhand` runs in the same compose project, publicly exposed, socket-mounted | Must be decided: retire, keep internal, or authenticate |
| D10 | (not mentioned) | A **host-level edge agent** (`mission-control-agent.service`, 272 MB SQLite) is part of production | Must be migrated or intentionally retired, or agent 3 goes dark |

---

## 7. Risks

| ID | Risk | Likelihood | Impact | Mitigation (Phase 2+) |
|---|---|---|---|---|
| R1 | **No backup exists**; a failure during migration loses the only copy of the DB | Medium | Critical | Produce and **restore-test** an encrypted `pg_dump -Fc` as step 0 of Phase 4 |
| R2 | Destination RAM (956 MB, no swap) is insufficient for PG+backend+Redis, or OOMs during image build | **High** | High | Add 2 GB swap on both VMs; build frontend image elsewhere; set container memory limits; consider resizing to 2 OCPU / 8 GB |
| R3 | Fernet key loss/mismatch silently breaks 33 encrypted credentials | Low | Critical | Carry `MISSIONCONTROL_SECRET_KEY` byte-for-byte; decrypt-verify one row post-restore |
| R4 | `/dockhand/` unauthenticated + docker.sock rw = host root exposure | **Certain (live)** | Critical | Close on production now (separate approval); do not proxy it publicly on the destination |
| R5 | Git-only deployment breaks (untracked modules, uncommitted config) | High if attempted | High | Treat the working tree as the artefact; or commit the WIP first (recommended) |
| R6 | Certificate renewal is broken; cert expires 2027-01-06 | Certain | High at expiry | Move `/etc/letsencrypt`, replace standalone+container-stop renewal with webroot/DNS-01 on the destination |
| R7 | `agent_commands` (420 MB) makes dump/transfer slower than expected | Medium | Medium | Accept ~440 MB, or agree a retention prune before dump (owner decision) |
| R8 | Destination iptables/FORWARD REJECT breaks Docker published ports | Medium | High | Validate after Docker install; persist rules in `/etc/iptables/rules.v4` |
| R9 | Agents hard-bound to the DNS name; DNS TTL 360 s (one resolver cached 45 h) | Medium | Medium | Cut over DNS with TTL lowered in advance; verify from multiple vantage points |
| R10 | Host already OOMs under load; a dump/restore on the source adds pressure | Medium | High | Run `pg_dump` during a quiet window with `nice`/`ionice`; do not run pytest/ruff on the host during migration |
| R11 | Backend runs 7-day-old dependencies against current code | Medium | Medium | Rebuild backend image and smoke-test in Phase 5 |
| R12 | `docker.sock` rw in backend keeps host-root blast radius | Certain | High | Consider a socket proxy or read-only mount on the destination (design decision) |

---

## 8. Required application/configuration changes (input to Phase 2)

1. **Split the compose file per host.** Frontend VM: `nginx` + `frontend` (drop `depends_on: backend`,
   `depends_on: dockhand`, `env_file` where irrelevant). Backend VM: `backend` + `postgres` + `redis`
   (publish `8000` bound to `10.0.0.33`).
2. **Point nginx `/api/` at `http://10.0.0.33:8000`**, keep relative API paths (already the case), keep
   websocket upgrade headers and timeouts.
3. **Decide dockhand.** Recommendation: do not serve it publicly; either run it on the backend VM
   with an authenticated reverse proxy on localhost only, or retire it. Never re-expose
   `/dockhand/api/*` to the internet.
   **Resolved in Phase 2 (D-B):** no dependency found (0 users, 0 sessions, auth disabled, empty state,
   no code/script/DB reference) and only one human visitor ever → **not migrated**. The public route is
   handled as a separate security item (D-F) with an exact change proposal in `network-security-plan.md` §7.
4. **Carry the working tree, not just git** — or commit the reviewed parts of it before migrating.
   **Resolved in Phase 2 (D-E):** the live `docker-compose.yml` and `nginx/default.conf` are preserved as a
   provenance snapshot (branch `migration/prod-live-snapshot-2026-10-20`, commit `75a8280`); the untracked
   Veeam module is a dead duplicate and is **excluded**; see `destination-diff.md` §2.
5. **Carry the host agent** (`/opt/mission-control-agent`, `/etc/mission-control-agent`, `/var/lib/
   mission-control-agent`, systemd unit) or explicitly retire it.
   **Resolved in Phase 2 (D-C):** it monitors only the machine it runs on, has no dependants and no
   automation, so it **retires with the source host**; a fresh agent on the BE VM is an optional
   post-cutover change.
6. **Replace cert renewal** with an ACME challenge that does not stop containers (webroot on port 80
   before the 301, or DNS-01), and move `/etc/letsencrypt` intact.
7. **Add log rotation** (`json-file` max-size/max-file) — the correct stanza already exists in the
   stale `docker-compose.prod.yml`.
8. **Add a database backup schedule** on the destination — none exists today on either side.
9. **Fix the destination firewall** in `/etc/iptables/rules.v4` (80/443 from internet, 8000 only from
   `10.0.0.26`, keep 22 restricted) and disable `rpcbind`.
10. **Do not copy** the source `/etc/hosts` `127.0.0.1 redis/postgres` lines — they are CI hacks.

---

## 9. Backup, downtime and recovery implications

- **Backup requirement (blocking):** take `pg_dump -Fc` (pg_dump 16.14 is available in the container),
  store it encrypted off-host, and **verify by restoring into a scratch database** before any cutover
  approval. Include: `.env` (secret), `/etc/letsencrypt`, the repo working tree, the host agent state.
- **Downtime:** the DB dump itself is a read (no downtime). The write freeze window is the tail of the
  migration only: ~10–20 min of true write freeze, ~20–40 min degraded service. Agents heartbeat every
  30 s and buffer results; plugin sync loops run at 120 s / 300 s.
- **Recovery:** rollback = keep production untouched and repoint DNS back (TTL 360 s). The old host
  must not be decommissioned until the destination has passed acceptance and the rollback window has
  elapsed.
- **Certificates:** the current cert is valid until 2027-01-06, so cutover does not depend on renewal —
  but renewal must be fixed on the destination before that date.

---

## 10. Proposed sequence (for Phase 2 approval)

1. Approval of this report + Phase 2 design (split compose, dockhand decision, agent handling,
   firewall/cert design, capacity decision).
2. Phase 3: install Docker + tooling, add swap, fix iptables persistence, harden destinations.
3. Phase 4: **backup + restore test** (gate), then deploy backend VM stack and restore the DB.
4. Phase 5: deploy nginx + frontend on the frontend VM, point at `10.0.0.33:8000`.
5. Phase 6: validate application + data end-to-end from an external vantage (not this workstation).
6. Phase 7: cutover runbook and rollback rehearsal.
7. Cutover only after explicit written approval.

---

## 11. Phase 1 acceptance gate

Presented to the owner for review and approval. **No material infrastructure change has been made.**
The following require an explicit decision before Phase 2 can be planned:

- **D-A** Capacity: keep the 956 MB VMs (with swap + external image builds) or resize them?
- **D-B** Dockhand: retire, keep internal, or authenticate?
- **D-C** Host edge agent (agent 3): migrate to the backend VM or retire?
- **D-D** `agent_commands` retention: dump as-is (~440 MB) or prune after owner-approved retention?
- **D-E** Commit the uncommitted live config + untracked modules before migration, or carry the
  working tree as-is?
- **D-F** May the `/dockhand/` public exposure be closed on production now, ahead of the migration?

---

## 12. Phase 2 decision outcomes (owner decisions, 2026-10-20)

| ID | Owner decision | Phase 2 handling | Where documented |
|---|---|---|---|
| D-A | Build images **off-host**; review real capacity, consider a 2 GB swap; resize only if measurement justifies it | Build host = operator workstation (Docker 29.8.2, 8.1 GB, verified). Swap 2 GB at `swappiness=10` recommended as a safety net. Resizing deferred with explicit trigger conditions | `software-inventory.md` §4–5, `target-architecture.md` §7 |
| D-B | Prefer internal-only if required; otherwise recommend retirement after verifying dependencies; never expose the admin UI publicly; do not remove the production service now | Dependency check completed → unused. **Not migrated.** Container/volume untouched on the source. Route closure handled under D-F | `current-architecture.md` §9.2, `service-migration-matrix.md` (dockhand row) |
| D-C | Preserve functionality until purpose/dependencies are established; migrate only if required; never disable production during Phase 2 | Purpose established: host-local telemetry with no dependants. **Not migrated**; retires with the source host. Fresh BE agent is an optional post-cutover change | `current-architecture.md` §9.3, `service-migration-matrix.md` (host-agent row) |
| D-D | Migrate the complete dataset; defer pruning to a separate retention-policy change; do not delete/truncate production rows | Full dataset in scope; profile, size breakdown, growth, restore implications and capacity check recorded; retention policy proposed as follow-up | `backup-manifest.md` §4 |
| D-E | Preserve the working tree, review it, selectively commit suitable changes; keep secrets out of Git; document the exact revision and config differences | Reviewed and classified; provenance snapshot committed as `75a8280` on `migration/prod-live-snapshot-2026-10-20` (live checkout untouched); dead duplicate module and build artefacts excluded; secrets not committed | `destination-diff.md` (all) |
| D-F | Separate security work item: establish exposure/auth/dependencies, present exact change + impact + validation + rollback, obtain explicit approval, do not remove Dockhand or its data | Exposure confirmed (200 anonymous), dependencies absent, exact nginx diff + validation + rollback prepared — **approval still required before any production routing change** | `network-security-plan.md` §7 |

**Corrected finding from Phase 2 evidence:** the Phase 1 claim that the backend imports the untracked
`official_veeam/agent_remote_target.py` is **wrong** — it is a dead duplicate with no importer (see §1 note
and §3.5). The reproducibility problem remains valid because of the two uncommitted config files.

**No application, host, firewall, DNS or production configuration change was made in Phase 2.** The only
writes were to this repository: the Phase 2 documents and the provenance snapshot commit.
