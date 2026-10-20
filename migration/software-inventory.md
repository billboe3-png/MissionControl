# Software Inventory — Mission Control Migration

**Captured:** 2026-10-20. Source: GCP `34.35.177.209`. Destinations: OCI `.26` (frontend) / `.33`
(backend). "Verified" = command output during the Phase 1 audit.

---

## 1. Source host (production) — verified

| Component | Version / identity | Notes |
|---|---|---|
| OS | Ubuntu **24.04.5 LTS (noble)** | x86_64, kernel `7.0.0-1014-gcp` |
| Init / cgroup | systemd, **cgroup v2** | Docker driver `systemd` |
| Docker Engine | **29.9.1** (API 1.56, min 1.40) | containerd v2.4.2, runc v1.5.2, upgrade + reboot 2026-10-20 |
| Docker Compose | **v5.6.0** (CLI plugin) | compose file format satisfied by much older versions |
| buildx | v0.38.0 | |
| Storage driver | **overlayfs** (`io.containerd.snapshotter.v1`) | data-root `/var/lib/docker` (3.7 G) |
| Logging driver | `json-file` | **no max-size / max-file** anywhere live |
| Python (host) | 3.12 (system) | not used by the app |
| Python (container) | 3.12 (`python:3.12-slim` base) | uvicorn runs `app.main:app`, single process |
| Node (build only) | `node:22-alpine` (frontend build stage) | not present on host |
| PostgreSQL | **16.14** (`postgres:16-alpine`) | `pg_dump` 16.14 available in-container |
| Redis | **7.2.14** (`redis:7.2-alpine`) | AOF on, 0 keys |
| nginx | **1.27-alpine** host-level proxy container | live config = uncommitted `nginx/default.conf` |
| dockhand | `fnsys/dockhand:v1.0.48` | public at `/dockhand/`, no auth |
| SSL/ACME tooling | `certbot` (system package) + `certbot.timer`; user cron `certbot-renewal.sh` | renewal **broken** (see audit R6) |
| SSH/security | `openssh-server`, **fail2ban** (sshd + recidive, 184 bans), `ufw` installed? → **inactive** (iptables INPUT ACCEPT) | |
| Monitoring | Google Cloud Ops Agent (fluent-bit :20202, otel-collector :20201) | GCP-specific |
| Misc | `rsyslog`, `sysstat`, `chrony` (installed; systemd-timesyncd also present), `unattended-upgrades` (auto-reboot off) | |
| Host edge agent | `mission-control-agent.service`, venv at `/opt/mission-control-agent`, Python 3.12 | agent_id 3, `verify_ssl: false` |

### Container images (digests as deployed)

| Image | Digest | Size | Built |
|---|---|---|---|
| `missioncontrol-frontend:latest` | `sha256:b07e18ec599ef1eb75493bbdda6ac7218341809c88dd1385ca1d11f3817682e9` | 78.9 MB | 2026-10-14 |
| `missioncontrol-backend:latest` | `sha256:189883d1c49a5e611c770c8c3bed7923dca5ff62556a99ad2eaf7c9861fc45f1` | 647 MB | 2026-10-13 |
| `nginx:1.27-alpine` | `sha256:65645c7bb6a0…` | 74.5 MB | — |
| `postgres:16-alpine` | `sha256:57c72fd2a128…` | 420 MB | — |
| `redis:7.2-alpine` | `sha256:dfa18828cbc0…` | 56.9 MB | — |
| `fnsys/dockhand:v1.0.48` | `sha256:63ffc7dd086f…` | 853 MB | — |

Unused/stale images on the source (not part of production, not migrated): `missioncontrol2-*` stack
(~1.8 GB), 5 × ruff images, `node:22-slim`, `python:3.12-slim`, `maven`, `alpine`, `hello-world`.

---

## 2. Destination VMs — installed today (verified)

Both are the **same** image/config: OCI `VM.Standard.E2.1.Micro`, Ubuntu 22.04.5, kernel
`6.8.0-1062-oracle`, 1 OCPU (2 threads), **956 MB RAM, no swap**, 45 G disk (42 G free), ~5.9 M free
inodes, `10.0.0.0/24` subnet, 483 packages.

| Component | .26 (frontend) | .33 (backend) | Action |
|---|---|---|---|
| Docker / containerd / podman / ctr | **absent** | **absent** | install Docker Engine + compose plugin |
| `/etc/docker`, `/var/lib/docker` | absent | absent | created by install |
| git | absent | absent | install |
| rsync | absent | absent | install (transfer + operator convenience) |
| python3 | 3.10.12 | 3.10.12 | present; **no pip** |
| node / npm | absent | absent | only needed for a local frontend build — **do not** build here |
| nginx (host) | absent | absent | not needed (nginx runs in a container on FE) |
| postgresql / psql | absent | absent | not needed on host (container) |
| redis-server / cli | absent | absent | not needed on host (container) |
| certbot | absent | absent | install on **FE** (renewal) |
| fail2ban | absent | absent | install on **FE** (and BE if SSH exposed) |
| ufw / firewalld / nft | absent | absent | **do not install**; firewall is persisted iptables |
| iptables + iptables-persistent + netfilter-persistent | present | present | **edit `/etc/iptables/rules.v4`** |
| curl / wget / jq / gnupg / ca-certificates | present | present | prerequisites for Docker repo OK |
| make / gcc / java | absent | absent | not needed |
| nc | absent | present | — |
| ping (`iputils-ping`) | present | absent | install on BE if ping-based checks are wanted |
| rpcbind (`:111`) | running | running | disable unless NFS/iSCSI is needed |
| open-iscsi (`iscsid`) | enabled | enabled | inertia of the OCI image; can be left |
| Oracle Cloud Agent (snap) | 1.61.0-6, plugins: monitoring, run-command, cloud-guard, custom logs | same | leave (or restrict, per security posture) |
| systemd-timesyncd | active, synced | active, synced | keep |
| unattended-upgrades | enabled, auto-reboot off | same | keep |

**Egress verified from both:** `registry-1.docker.io` (401 challenge = correct), `ghcr.io`, `quay.io`,
`pypi.org`, `registry.npmjs.org`, `github.com`, `download.docker.com`, `archive.ubuntu.com`,
`security.ubuntu.com`, `keyserver.ubuntu.com` — all reachable.

---

## 3. Software to install (Phase 3 scope — not yet executed)

### Common to both VMs

| Package | Purpose | Pinning recommendation |
|---|---|---|
| `docker-ce`, `docker-ce-cli`, `containerd.io`, `docker-buildx-plugin`, `docker-compose-plugin` | runtime + compose plugin | Pin to the **same** Docker Engine line as production (29.9.x) and compose 5.6.x where the apt repo allows, to keep behaviour identical; otherwise record the version difference. Also pin / hold the package during the migration window so an unattended upgrade cannot restart the daemon mid-cutover |
| `git` | deploy the repository working tree | distro version |
| `rsync` | file transfer, backups | distro version |
| `fail2ban` | SSH brute-force protection (source has it; 184 bans) | distro version + the repo's `deploy/fail2ban-*` config |
| 2 GB swapfile | headroom on a 956 MB instance (D-A) | `/swapfile`, `vm.swappiness=10`, persisted in `/etc/fstab`; verify `free -m` and `swapon --show` after a reboot |

### Frontend VM only
`certbot` (ACME renewal; **webroot** authenticator), optional `python3-certbot-nginx`. Install
`certbot.timer` and remove any standalone-mode renewal script.

### Backend VM only
No PostgreSQL/Redis packages — both run as containers. `git` is needed because the backend is deployed
from the working tree (bind mount `./backend:/app`), and `rsync` for the dump transfer.

### Host configuration steps (Phase 3, not executed)

| Step | FE | BE |
|---|---|---|
| Create `/opt/missioncontrol`, deploy working tree | ✓ | ✓ |
| `.env` transfer with mode 600, keys byte-identical | — | ✓ |
| `/etc/iptables/rules.v4` per `network-security-plan.md` §3 | ✓ | ✓ |
| Disable `rpcbind`; keep `iscsid` | ✓ | ✓ |
| Copy `/etc/letsencrypt` intact; create `/var/www/letsencrypt` | ✓ | — |
| Reboot test to confirm persisted firewall + swap survive | ✓ | ✓ |
| Docker daemon pacing: keep the default, record version | ✓ | ✓ |

### Explicitly NOT installed on the destination
`ufw`/`firewalld` (the image's persisted iptables is the control), a host nginx, a host PostgreSQL or
Redis, Node.js/npm (build the frontend image elsewhere), and the GCP Ops Agent.

---

## 4. Image build and transfer strategy

**D-A resolution: build off-host on the operator workstation** (verified: Docker **29.8.2**, compose
5.5.1, **8.1 GB RAM**), transfer by `docker save | gzip | ssh docker load`. Rationale: a Vite/npm build
needs ~1–1.5 GB and the FE VM has 956 MB — it would be OOM-killed. Building on the source is also
rejected (históric OOM with production running). CI-based builds remain an option for a later change
(a registry and credentials would have to be introduced — not justified for one migration).

| Artefact | Strategy | Reason |
|---|---|---|
| `missioncontrol-backend` | **Rebuild off-host** from `backend/Dockerfile` against the deployment branch working tree; verify the `requirements.txt` delta vs the 2026-10-13 image | the live container runs current code (bind mount) on older dependencies |
| `missioncontrol-frontend` | **Build off-host**, transfer as above, cache the npm layer on the workstation | 956 MB destination cannot build it |
| `nginx:1.27-alpine`, `postgres:16-alpine`, `redis:7.2-alpine` | Pull on the destination, pin by **digest** (same digests as source where possible) | reproducibility |
| `fnsys/dockhand:v1.0.48` | **Not migrated** (D-B) | unused, unauthenticated, empty state |

Naming: `missioncontrol-<component>:<git-sha>-<YYYYMMDD>`. Every image is recorded by digest in the
Installation Report (`execution-log.md`) so a future rebuild is deterministic. Build inputs are the
working tree of `migration/2vm-deploy` at a recorded commit — never `release/v3.0.0-rc1` directly,
which does not contain the live config.

---

## 5. Capacity assessment (D-A)

| Quantity | Value | Source |
|---|---|---|
| Destination RAM / swap / disk | 956 MB / 0 MB / 42 GB free | Phase 1 audit |
| Measured live usage — BE role (backend + postgres + redis) | 175 + 47 + 4 = **226 MB** | `docker stats`, 2026-10-20 |
| Measured live usage — FE role (nginx + frontend) | 5 + 3 = **8 MB** | `docker stats` |
| Dockerd overhead (not in container stats) | ≈ 80–120 MB | estimate **[A]** |
| Peak risk | frontend build, `npm ci`, `pg_restore` of 439 MB | measured behaviour on other hosts |

Conclusion: current shapes are **sufficient for the steady state** but have thin headroom for restore
work, Vite builds and OOM spikes; the source host has already OOM-killed a process once. Therefore:

1. **Do not resize now.**
2. Add **2 GB swap** on both VMs (`/swapfile`, `vm.swappiness=10`, persisted in `/etc/fstab`) as a safety
   net — 2 GB of 42 GB free.
3. **Build off-host**; never build on a destination.
4. Resize (2 OCPU / 8 GB) only if observed: sustained host RAM > 80 %, any OOM kill, sustained swap
   thrash, or backup/restore durations that threaten the RTO.
5. Do not use swap as capacity; it is for cold pages and short spikes.

---

## 5. Version gaps and compatibility notes

| Item | Source | Destination today | Note |
|---|---|---|---|
| OS | Ubuntu 24.04.5 | Ubuntu 22.04.5 | Same glibc generation family; containers are unaffected. Host-level scripts must avoid 24.04-only commands |
| Docker | 29.9.1 | none | Install; verify `docker compose config` accepts the split files |
| Compose | v5.6.0 | none | `depends_on: condition:` and `env_file` are supported by any modern plugin |
| PostgreSQL | 16.14 | none | Pin `postgres:16-alpine` **by digest**; restore with matching `pg_dump` 16.14 |
| Redis | 7.2.14 | none | Pin digest; empty keyspace |
| TLS | Let's Encrypt (RSA) | none | Move `/etc/letsencrypt`; certbot on FE |
| Python | 3.12 (container) | 3.10 (host) | Irrelevant to the app, which ships its own interpreter in the image |

---

## 6. Items that are software-adjacent and must not be forgotten

- `/etc/hosts` on production pins `redis` and `postgres` to `127.0.0.1` (CI workaround). **Do not copy.**
  Inside compose, service names resolve through Docker's embedded DNS.
- Production has **no log rotation**; the correct stanza already exists in the stale
  `docker-compose.prod.yml` and should be carried into both split compose files.
- `unattended-upgrades` is enabled on all three hosts with automatic reboot off — a Docker upgrade
  mid-migration is possible; pin/observe before cutover.
- The destination's persisted `iptables` (`netfilter-persistent`) will silently revert ad-hoc rules on
  reboot. Any firewall change must be written to `/etc/iptables/rules.v4` and re-verified after a reboot.
- **Docker and the host firewall interact:** published container ports are DNATed and traverse `FORWARD`,
  not `INPUT`, so `INPUT` rules are not the gate for 80/443. The real public gate is the OCI security list
  plus the container bind address; see `network-security-plan.md` §3.1. Do not run `iptables-save` after
  Docker has started.
- `verify_ssl: false` in the host agent config is **not** carried (the agent is not migrated); the plugins
  running on BE keep their existing settings inside the database.

---

## 7. Phase 2 additions at a glance

| New artefact | Where |
|---|---|
| Target architecture, compose split, TLS renewal design, capacity model | `migration/target-architecture.md` |
| Source revision, working-tree classification, per-host configuration diffs | `migration/destination-diff.md` |
| Firewall rules, exposure matrix, D-F change proposal | `migration/network-security-plan.md` |
| Backup scope, commands, verification, `agent_commands` profile | `migration/backup-manifest.md` |
| Cutover sequence, validation set, abort points | `migration/cutover-runbook.md` |
| Rollback scenarios, reconciliation, point-of-no-return | `migration/rollback-runbook.md` |
| Evidence for D-B/D-C/D-D/D-E and the Phase 1 correction | `migration/current-architecture.md` §9 |
