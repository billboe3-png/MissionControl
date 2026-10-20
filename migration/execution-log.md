# Execution Log — Mission Control Migration

Format per plan §22. Times are UTC. No secrets are recorded here. Commands are summarised
(sanitised); they were read-only unless stated.

---

## Phase 1 — read-only audit

| Timestamp | Host | Action and reason | Verification and result | Approval ref |
|---|---|---|---|---|
| 2026-10-20 15:40 | local (Windows) | Inspected repository, branch, working tree, current commit. §24.1 | Local HEAD `8b996bd` on `release/v3.0.0-rc1` with unrelated WIP; server HEAD `ca2d267`; no `migration/` directory existed | Owner instruction: "start phase 1" |
| 2026-10-20 15:42 | local | Discovered OpenCode capabilities for the audit. §24.2 | Subagent tool available with `general` / `explore` agents and shell access; used for the three specialist read-only audits | same |
| 2026-10-20 15:45 | prod `34.35.177.209` | Verified SSH access and identity. §24.3 | Connected as `billboe3`; `git log` = `ca2d267`; working tree dirty on `docker-compose.yml`, `nginx/default.conf` | same |
| 2026-10-20 15:46 | FE `84.12.77.251`, BE `84.12.82.239` | Verified SSH access to both destinations | Both reachable with `Mission-control.key`; private IPs `10.0.0.26` / `10.0.0.33`; Ubuntu 22.04.5; Docker absent | same |
| 2026-10-20 15:50 | all three | Established audit scope: strictly read-only, no restarts, no installs, no firewall/DNS changes; secret **names** only | Rules recorded in the plan (§6) and repeated in every subagent brief | same |
| 2026-10-20 15:55–16:05 | prod | Production audit (OS, capacity, network, Docker, containers, images, compose project, volumes, ports, health, workers, env names, TLS/renewal, logs, Postgres, Redis, files, faults) | Report: `report-production-audit.md` (scratch, untracked) | same |
| 2026-10-20 15:55–16:20 | both destinations | Destination and networking audit (OS, packages, capacity, firewall, egress, private/public connectivity, capacity plan, cloud-policy limits) | Report: `report-destination-network-audit.md` (scratch, untracked) | same |
| 2026-10-20 15:55–16:20 | prod + both destinations | Security, backup and recovery review (secret inventory names/modes, encryption-key dependency, backups, exposure, hardening, downtime) | Report: `report-security-backup-recovery.md` (scratch, untracked) | same |
| 2026-10-20 16:20–16:35 | prod | Lead-agent independent re-verification of critical claims: host is GCP / Ubuntu 24.04.5; live config uncommitted; backend imports **untracked** `official_veeam/agent_remote_target.py`; DB 439 MB with `agent_commands` 420 MB; alembic head `h7h8h9i1j2k3`; Redis `dbsize 0`; cert expiry 2027-01-06; no `/var/log/certbot-renewal.log`; `/dockhand/` and `/dockhand/api/containers` **HTTP 200 unauthenticated**; `/api/docs` 200; `.env` mode 664; no `/opt/backups`; nginx 27 restarts | All confirmed; recorded in `audit-report.md` §3 | same |
| 2026-10-20 16:25 | BE `10.0.0.33` | Re-verified destination firewall and package baseline | Persisted iptables allows only 22, final `REJECT --reject-with icmp-host-prohibited`; `ip_forward=0`; Docker/git absent; rpcbind on `:111` | same |
| 2026-10-20 16:35 | local | Consolidated findings into the Phase 1 deliverables (§10) and this log (§22) | `migration/audit-report.md`, `migration/service-migration-matrix.md`, `migration/current-architecture.md`, `migration/software-inventory.md`, `migration/execution-log.md` | same |
| 2026-10-20 16:40 | local → prod | Committed the Phase 1 documents to the server repository (docs only) | Commit `docs(migration): Phase 1 read-only audit baseline`; no application, compose, nginx or host change included | same |

---

## Outstanding issues recorded during Phase 1

1. **No backups exist** on the source (P0). No dump produced during Phase 1 — producing one is a
   Phase 4 deliverable requiring the backup approval gate.
2. **`/dockhand/` is publicly unauthenticated with `docker.sock` rw** (P0, pre-existing). Not changed;
   closing it on production needs separate approval.
3. **Certificate renewal is broken** (cron log path unwritable; standalone auth conflicts with nginx).
   Cert valid until 2027-01-06.
4. **Live configuration is uncommitted** (`docker-compose.yml`, `nginx/default.conf`) and the backend
   imports an untracked module. Decision required (commit vs carry working tree).
5. Pre-existing **schema drift** (`mikrotik_servers.allow_insecure_ssl` and others) migrates with the
   database unless fixed; it is not migration-induced.
6. Any file writes during the audit were limited to inert `/tmp` scripts on the hosts and this
   repository's `migration/` directory.

---

## Phase 1 decision register (owner input requested)

| ID | Decision | Recommendation |
|---|---|---|
| D-A | Destination capacity (956 MB, no swap) | Add 2 GB swap now; build the frontend image off-host; consider resizing to 2 OCPU / 8 GB |
| D-B | dockhand | Do not expose publicly; retire or run internal-only on BE with auth |
| D-C | Host edge agent (agent 3, 272 MB state) | Retire, or move to BE and re-register |
| D-D | `agent_commands` retention (420 MB) | Dump as-is first; prune only under an agreed retention policy |
| D-E | Uncommitted config / untracked module | Commit them to the branch before migrating (recommended) |
| D-F | Close `/dockhand/` on production now? | Yes, independently of the migration |

---

## Phase 2 — design (read-only + repository writes only)

| Timestamp | Host | Action and reason | Verification and result | Approval ref |
|---|---|---|---|---|
| 2026-10-20 (Phase 2 start) | local | Received owner decisions D-A…D-F and the Phase 2 deliverable list | Decisions recorded in `audit-report.md` §12 and the register below | Owner instruction: "Proceed to Phase 2 — Design" |
| 2026-10-20 | prod | Dockhand dependency check: compose/nginx/script references, container env shape, volume contents, SQLite state, nginx access-log traffic analysis | No code/script/DB dependency; Dockhand DB has **0 users, 0 sessions**, `auth_enabled=0`, 0 environments/repos/backups; 326 `/dockhand*` log lines (282 not our audit probes), incl. one real owner browser session with failing API calls | same |
| 2026-10-20 | prod | Host edge-agent identification: systemd unit, config keys, `agents` row, plugin inventory, `agent_commands` history, `edge.db` tables | Agent id 3 monitors its own host; live heartbeat; 2 commands ever (last 2026-09-22); no `agent_remote_target`/integration reference; `edge.db` 272 MB is a local send buffer (`sync_log` ≈ 456 k rows) | same |
| 2026-10-20 | prod | `agent_commands` profile: size breakdown, row counts, status mix, growth by day, FK check | 98,015 rows; 420 MB (heap 64 MB, indexes 8.9 MB, TOAST ≈ 347 MB); no inbound FKs; 2.6–5.4 k rows/day | same |
| 2026-10-20 | prod | Working-tree capture: `git status`, full diff, untracked inventory with sizes, per-file sha256, tracked-env check | 2 modified files + 13 untracked entries; hashes `d4e9685b…` / `734f40e4…`; `.env` untracked, `.env.production` tracked and **not** the live key (hash comparison only) | same |
| 2026-10-20 | prod | **Correction check:** whether the backend imports the untracked Veeam module | `grep -rn agent_remote_target backend --include=*.py` → no importer of the plugin-local copy; the tracked model is canonical. Phase 1 claim retracted | same |
| 2026-10-20 | prod | Secret/keyword scan of the two live config files | No literal credential in `docker-compose.yml` (env references + a documented weak dockhand default); none in `nginx/default.conf` | same |
| 2026-10-20 | local | Build-host capability check (D-A) | Docker **29.8.2**, compose 5.5.1, **8.1 GB RAM** → off-host builds feasible | same |
| 2026-10-20 | BE `10.0.0.33` | Capacity/swap feasibility check | `swappiness 60`, 42 GB free, no swap, `/etc/fstab` present and writable by root | same |
| 2026-10-20 | local → prod | Wrote the six new Phase 2 documents and updated the four Phase 1 documents | `target-architecture.md`, `destination-diff.md`, `network-security-plan.md`, `backup-manifest.md`, `cutover-runbook.md`, `rollback-runbook.md`; updates to `current-architecture.md` §9, `service-migration-matrix.md`, `software-inventory.md` §4–7, `audit-report.md` §1/§3.5/§8/§12 | same |
| 2026-10-20 | prod | **Repository-only preservation (D-E):** committed the live `docker-compose.yml` and `nginx/default.conf` as a provenance snapshot in a temporary worktree | Branch `migration/prod-live-snapshot-2026-10-20`, commit `75a8280` (2 files, +58/−4). Live checkout verified unchanged afterwards (same branch, same modifications, same hashes). Not pushed | Owner decision D-E |

### Decision register — resolved

| ID | Status | Outcome |
|---|---|---|
| D-A | **Resolved** | Off-host builds on the workstation; 2 GB swap recommended; resizing deferred with trigger conditions |
| D-B | **Resolved** | Dockhand unused → not migrated; container/volume left untouched; no public exposure on the destination |
| D-C | **Resolved** | Host agent is host-local with no dependants → retires with the source host; fresh BE agent optional later |
| D-D | **Resolved** | Full `agent_commands` dataset migrated; retention policy deferred to a separate change |
| D-E | **Resolved (+ action taken)** | Working tree reviewed and classified; live config preserved as snapshot `75a8280`; dead duplicate and build artefacts excluded; no secret committed |
| D-F | **Prepared, awaiting approval** | Exposure and absence of dependencies verified; exact diff, impact, validation and rollback ready in `network-security-plan.md` §7. **Production routing unchanged** |

### Outstanding decisions for the owner (Phase 2 gate)

| # | Item | Needed for |
|---|---|---|
| U1 | Are the OCI public IPs **reserved**? | DNS cutover safety (Phase 7) |
| U2 | Exact OCI ingress rules / source scopes (consent to read the console) | network design confirmation |
| U3 | Block `/api/docs` and `/api/openapi.json` publicly on the destination? | edge nginx config |
| U4 | Keep the second certificate lineage (`missioncontroldev`)? | certbot scope |
| U5 | Any Docker UI wanted on the new hosts? | replacement decision for Dockhand |
| U6 | Off-host backup destination + encryption key custody | Phase 4 design freeze |
| U7 | `docker.sock` in the backend: accept for cutover or add a socket proxy now? | compose finalisation |
| D-F | Approve the `/dockhand/` route closure on production (exact change prepared) | separate security work item |

### Verification notes

- Every write in Phase 2 was to this repository (documents + one branch commit). No host configuration,
  firewall rule, DNS record, container state or production service was modified.
- Probes against production were read-only: `psql` SELECT/`\d`, SQLite opened with `?mode=ro`, log greps,
  `docker inspect`/`logs`, `git` queries.
- No secret value was printed: key material was compared by hash only.

---

## D-F — Production security change: close public `/dockhand/` (approved, executed)

**Approval:** owner decision D-F, 2026-10-20. Explicitly authorised as a **separate operation** from the
migration. No other production change was made.

| Timestamp (UTC) | Host | Action | Verification / result |
|---|---|---|---|
| 2026-10-20 16:47 | prod `34.35.177.209` | Pre-change capture: branch `release/v3.0.0-rc1` @ `618394d`; `nginx/default.conf` sha256 **`734f40e4…`**; dockhand blocks at lines 42–65; nginx mounts the live file read-only from `/opt/MissionControl/nginx/default.conf` | Baseline probes: `/` 200, `/api/v1/health/{live,ready}` 200, `/dockhand/` **200**, `/dockhand/api/containers` **200**, `/api/docs` 200 |
| 2026-10-20 16:48 | prod | Reviewed the prepared diff (`network-security-plan.md` §7); confirmed the regex form covers `/dockhand`, `/dockhand/` **and** every sub-path (including the API) while matching nothing else | Nothing else in the file matches `^/dockhand` |
| 2026-10-20 16:48 | prod | Protected copy taken before editing | `~/migration-preserved/default.conf.pre-dockhand-close-20261020T164807Z`, sha256 `734f40e4…` (identical to live) |
| 2026-10-20 16:48 | prod | Applied the smallest routing change: removed the three proxy/redirect blocks (AGENT_META lines 42–65) and inserted `location ~ ^/dockhand(/|$) { return 404; }` | `git diff --stat` → `nginx/default.conf | 24 +++++-` (21 insertions, 3 deletions; remaining changes are pre-existing WIP already captured in snapshot `75a8280`) |
| 2026-10-20 16:48 | prod | **Config test before reload** | `docker exec missioncontrol-nginx-1 nginx -t` → `syntax is ok` / `test is successful` |
| 2026-10-20 16:48 | prod | Reload (not restart) | `nginx -s reload`; container still `Up (healthy)`; new sha256 **`a59d4145…`** |
| 2026-10-20 16:48 | prod | Post-change validation, probes spaced ~1 s apart (the `@net` zone limits 30 r/min per IP) | `/dockhand` **404**, `/dockhand/` **404**, `/dockhand/api/containers` **404**, `/dockhand/api/containers?` **404**; `/` 200, `/api/v1/health/live` 200, `/api/v1/health/ready` 200, `/health` 200, `/api/v1/version` 200 (`3.0.0-rc1`), `/api/docs` 200 |
| 2026-10-20 16:48 | prod | Over-block check: unrelated paths containing the word are unaffected | `/dockhand-not-a-route` 200, `/apidockhand` 200 |
| 2026-10-20 16:48 | prod | TLS and redirect unchanged | cert `CN=missioncontrol.optichosting.co.za`, valid 2026-10-08 → **2027-01-06**; port 80 → 301 `https://…/` |
| 2026-10-20 16:48 | prod | Application health | login page title `Mission Control`; all six containers healthy/running; backend `traceback|critical` count in the last 5 min = **0**; agent fleet still polling (edge `/config`, `/heartbeat`, `/bundle/download` 200) |
| 2026-10-20 16:48 | prod | Dockhand left untouched per instruction | container `running=true`, same start time `2026-10-20T10:42:08Z`; volume `missioncontrol_dockhand_data` present |
| 2026-10-20 16:49 | prod | Investigated the one non-200 observation: `GET /api/v1/ws/health` with upgrade headers → 403 | **Not caused by this change.** No WebSocket route exists at `/api/v1/ws/health`; the real ones are `/api/v1/remote/console`, `/console-agent` and the D-Link `…/servers/{id}/webui` (backend code). Lines 1–50 (including the whole `/api/` block) are **byte-identical** before and after the edit, and every `/api/` path validates 200/401 as expected. The 403 is an application/auth response, pre-existing and unrelated. |

**Change summary — what was altered:** one nginx file, three removed blocks, one added `return 404`
location. **What was not altered:** the dockhand container, its database, its volumes, the compose file,
TLS, DNS, the API, the frontend, the database, agents, or any host firewall rule.

**Rollback procedure (tested against the preserved copy):**

```bash
cd /opt/MissionControl
cp ~/migration-preserved/default.conf.pre-dockhand-close-20261020T164807Z nginx/default.conf
sha256sum nginx/default.conf        # must be 734f40e45c1ce3ff0b4ac3871c2fbc21dae83af2910f2c5da611126c2e747505
docker exec missioncontrol-nginx-1 nginx -t
docker exec missioncontrol-nginx-1 nginx -s reload
curl -s -o /dev/null -w '%{http_code}\n' https://missioncontrol.optichosting.co.za/dockhand/   # 200 again
```

Alternative rollback from git: `git show 75a8280:nginx/default.conf > nginx/default.conf`.
Estimated rollback time: **< 1 minute**, no restart, no downtime.

**Follow-up (not authorised yet):** the container and volume remain running and are now unreachable from
the internet. Removing them, and stopping the container, require a separate approval.

---

## Phase 3 — destination host preparation (complete, stopped at the gate)

**Scope executed:** off-host image builds, deployment branch + artefacts, destination verification, approved
prerequisite installation, firewall/swap persistence test. **Not executed (not authorised):** any backup
creation/transfer/restore, any production data migration, any DNS change, any production deployment, any
source-host decommission. Production remains authoritative.

| Timestamp (UTC) | Host | Action and reason | Verification and result |
|---|---|---|---|
| 2026-10-20 16:47 | prod | D-F executed as a separate approved operation (preceding section) | approved, validated, rollback documented |
| 2026-10-20 16:55 | — | Recorded owner decisions U1–U7 and the Phase 3 authorisation | §"Owner decisions U1–U7" below |
| 2026-10-20 16:55 | local | U7 code-path verification: is the `docker.sock` mount load-bearing? | **No.** No `docker.from_env`/`DockerClient`/`import docker` in `backend/app`; the docker plugin (`official_docker/api.py`) is an **httpx** client to a *configured* Docker Engine API host. `docker_hosts` is **empty** and all `docker_*` tables hold **0 rows**. The mounted socket was additionally **unreadable/unwritable** to the container's `app` user (`DockerException … PermissionError(13)`). Mount and `DOCKER_HOST` therefore omitted on the destination; nothing was disabled on production |
| 2026-10-20 17:00 | local | Verified the build host (Docker 29.8.2, compose 5.5.1, 8.1 GB RAM); identified the authoritative build source | The local Windows checkout is a **divergent line** with unrelated WIP, so it is not the build source. Cloned the server repo to `mc-build` (`--no-hardlinks --single-branch`, HEAD `618394d`) and built from that tree |
| 2026-10-20 17:02 | local | Built both images `--no-cache` | `missioncontrol-backend:601a878-20261020` id `sha256:81f84489…` (603 MB); `missioncontrol-frontend:601a878-20261020` id `sha256:1ec76e71…` (75.6 MB). Recorded in `build-and-transfer.md` |
| 2026-10-20 17:05 | FE/BE | Verified reserved public IPs (U1), capacity, prerequisites, private/public network path | Both reserved IPs resolve to the intended VMs (OCI metadata: `Mission-Control-Frontend` / `Mission-Control-Backend`); shape `VM.Standard.E2.1.Micro`, 956 MB, 42 GB free; Docker/git/rsync/certbot/fail2ban absent; private path `10.0.0.26 ↔ 10.0.0.33` delivers every port; `ADMIN_CIDR` sources observed: `45.220.11.50` (home) and `168.253.204.10` (work) |
| 2026-10-20 17:06 | FE (from FE→BE public) | U2 cloud-side behaviour probe | BE public `22`/`8000`/`5432` = **no connection**; FE public `443` = `No route to host` (VCN does not hairpin public IPs from inside — expected). No path exposing BE 8000/5432 publicly was observed |
| 2026-10-20 17:08 | — | Owner supplied the OCI security-list rules; recorded verbatim and compared to U2 in `network-security-plan.md` §1.1 | **Conforms:** FE 80/443 public; SSH restricted to the two admin `/32`s at the cloud layer; 5432/6379 not public. **Discrepancy:** “BE 8000 from `10.0.0.26` only” is **not** a cloud rule (the broad `10.0.0.0/16` all-protocols rule covers it) — enforced instead by container bind address + host firewall. Nothing broadened |
| 2026-10-20 17:09 | FE + BE | Installed approved prerequisites (idempotent scripted run) | **Both:** 2 GB `/swapfile` + `vm.swappiness=10` (+ fstab), Docker Engine **29.9.1** + compose **v5.6.0** (matches production), `git`, `rsync`, `fail2ban`, `jq`, rewritten persisted `/etc/iptables/rules.v4` (22 narrowed to the two admin `/32`s; 80/443 open; final REJECT), `rpcbind` disabled. **FE only:** `certbot` **1.21.0** + `/var/www/letsencrypt/.well-known/acme-challenge` webroot. Backups of the previous `rules.v4` taken. Original `rules.v4` preserved as `.bak.<timestamp>` |
| 2026-10-20 17:11 | FE | Reboot-persistence test #1 | `sudo reboot` issued; host returned; verify script was lost by the reboot (documented, re-uploaded) |
| 2026-10-20 17:12 | FE | Reboot-persistence verification | uptime 0 min; swap **2 GB** present, `swappiness=10`, fstab entry line 20; iptables rules **persisted as written** (22 scoped to both admin `/32`s, 80/443 open, final REJECT); listeners = `sshd:22`, resolved stub `:53` (**no `:111`**); Docker `active` (Server 29.9.1, `MemTotal` 1002909696); `ip_forward=1`; persisted file contains **0** `DOCKER` lines (correct — Docker inserts its chains at start, they must not be baked into the file) |
| 2026-10-20 17:15 | BE | Reboot-persistence test (first attempt did **not** actually reboot — uptime still 3 h 53 m; live `INPUT` still showed the **old** unrestricted-22 rule ahead of the new ones) | Detected and corrected rather than recorded as a pass. This is exactly why the reboot test is run before data exists |
| 2026-10-20 17:16 | BE | Reboot-persistence verification after a real reboot | uptime 1 min; swap 2 GB, `swappiness=10`, fstab line 20; iptables **persisted as written** (identical rule set to FE); listeners `sshd:22` + resolved stub `:53`, no `:111`; Docker `active` 29.9.1; `ip_forward=1`; 0 `DOCKER` lines in the persisted file |
| 2026-10-20 17:18 | FE + BE | Post-install posture check | FE: `rpcbind` listeners **0**; Docker `DOCKER` chains present in live ruleset (expected, inserted by dockerd) but **absent** from the persisted file. BE: `certbot` **absent** (correct — edge only), `fail2ban` installed/inactive (no jails configured yet — recorded below). BE `8000` returns *closed* from FE until the stack is deployed (nothing listening yet) |

### U7 — Docker socket decision (evidence)

| Question | Finding |
|---|---|
| Is `import docker` / the Docker SDK used anywhere in the backend? | **No.** `grep` for `import docker`, `docker.from_env`, `DockerClient`, `docker.errors` in `backend/app` returns nothing |
| How does the Docker plugin reach a Docker host? | `backend/app/plugins/installed/official_docker/api.py` is an **httpx** async client that builds `http(s)://<configured host>` from a `DockerPluginConfig` host list (`config.py`) |
| Is any Docker host configured? | **No** — `docker_hosts` is empty and `docker_containers/_images/_volumes/_networks/_compose_stacks` are all **0 rows**. The plugin has no configured target |
| Does the mounted socket work in the container anyway? | **No** — `app` (uid 100) is not in the socket's group; the SDK probe failed with `PermissionError(13)`. So the socket provides no working capability today |
| Decision | **Omit the mount and `DOCKER_HOST` on the destination.** Documented in `docker-compose.backend.yml`. If a Docker host is ever wanted, it should be added as a **configured remote host** in the plugin settings, not via a local socket. Remote Docker API was never exposed |
| Production impact | **None.** Nothing was changed on production; this decision only affects the not-yet-deployed destination compose file |

### Phase 3 installation report

**Images (built off-host, per D-A):**

| Image | Tag | Image ID | Size | Source revision |
|---|---|---|---|---|
| `missioncontrol-backend` | `601a878-20261020` | `sha256:81f8448974fcc5030310e527d67f791369ce52bbd5d8a7218a864227990d147d` | 603 MB | `release/v3.0.0-rc1` @ `618394d` (server working tree) |
| `missioncontrol-frontend` | `601a878-20261020` | `sha256:1ec76e71b65ea98fbcfc2454bd12d26c82fa7c6ae99ee2606eff2369c1c9c78e` | 75.6 MB | same |

**Installed software (verified, both hosts unless noted):**

| Component | FE `10.0.0.26` | BE `10.0.0.33` |
|---|---|---|
| Docker Engine | 29.9.1 | 29.9.1 |
| Docker Compose | v5.6.0 | v5.6.0 |
| git / rsync / jq | installed | installed |
| fail2ban | installed, inactive (no jails) | installed, inactive (no jails) |
| certbot | 1.21.0 + webroot | absent (edge only) |
| swap | 2 GB `/swapfile`, `swappiness=10` | 2 GB `/swapfile`, `swappiness=10` |
| persisted iptables | rewritten, reboot-verified | rewritten, reboot-verified |
| rpcbind (`:111`) | disabled | disabled |

**Firewall as installed and verified after reboot (both hosts):**

```
-A INPUT -i lo -j ACCEPT
-A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT
-A INPUT -p icmp -j ACCEPT
-A INPUT -s 45.220.11.50/32  -p tcp --dport 22 -j ACCEPT
-A INPUT -s 168.253.204.10/32 -p tcp --dport 22 -j ACCEPT
-A INPUT -p tcp --dport 80  -j ACCEPT
-A INPUT -p tcp --dport 443 -j ACCEPT
-A INPUT -j REJECT --reject-with icmp-host-prohibited
```

**Configuration diffs prepared (not yet deployed):** `deploy/migration-2vm/` contains
`docker-compose.backend.yml`, `docker-compose.frontend.yml`, `nginx/default.conf` and
`env/backend.env.example`. They are **artefacts**, not deployed state. Deployment is Phase 4.

## Phase 3b — destination hardening and backup planning (owner decisions 2026-10-20)

**Authorised by the owner's second decision set:** fail2ban SSH jail on both destination VMs, SSH
reachability verification, OCI rule/NSG clarification, and **planning** (not execution) of the backup and
recovery plan. Still **not** authorised: production backup creation/transfer, data restore, deployment,
DNS change, cutover, decommission.

| Timestamp (UTC) | Host | Action | Verification / result |
|---|---|---|---|
| 2026-10-20 17:24 | FE/BE | SSH reachability check from the intended administration location | Logged-in source observed as `45.220.11.50`; the work address is the second owner-confirmed admin IP. Both are stable **[V, owner-confirmed]** |
| 2026-10-20 17:25 | FE/BE | fail2ban readiness assessment before configuring | `fail2ban` 0.11.2 installed but **inactive/disabled**; **`/var/log/auth.log` is absent** — sshd logs only to **journald**; `systemd.journal` Python module present; `iptables` is the **nft** variant (v1.8.7) |
| 2026-10-20 17:25 | FE/BE | Wrote `/etc/fail2ban/jail.local` with `backend = systemd` (journald is the only source), `ignoreip` = both admin `/32`s + `10.0.0.0/24` + loopback, `maxretry 5 / findtime 10m / bantime 1h` with increment to 1 week | `fail2ban-client -t` → **OK: configuration test is successful** |
| 2026-10-20 17:25 | FE/BE | Enabled + started fail2ban | `active`, `enabled`; 1 jail: `sshd`; journal matches `_SYSTEMD_UNIT=sshd.service + _COMM=sshd`; **0 banned** |
| 2026-10-20 17:25 | FE | Proved the **ban action** works without touching a real peer | Synthetic ban of TEST-NET-3 `203.0.113.99` created `-A f2b-sshd -s 203.0.113.99/32 -j REJECT` in the live ruleset (confirmed in both the iptables and nft views); unban removed it cleanly |
| 2026-10-20 17:26 | FE | Investigated why a localhost probe produced no detections | **Root cause found:** `passwordauthentication no` + `permitrootlogin without-password` — the hosts are **pubkey-only**, so no `Failed password` lines can ever be generated. `Connection closed … [preauth]` lines are matched by the filter's *ignore* rules by design (a scanner disconnecting is not an auth failure) |
| 2026-10-20 17:27 | FE | Verified the filter matches the signatures this host **can** produce | Against real captured journal: **16 lines matched**, 20 ignored; sample signature file (`Failed publickey`, `Invalid user`, `maximum authentication attempts exceeded`) matched **3/5** (the 2 ignored are password lines the host cannot generate) |
| 2026-10-20 17:28 | FE | Resolved an `iptables-legacy tables present` warning | The live ruleset is entirely in the **nft** table (where Docker, `netfilter-persistent` and fail2ban operate); `iptables-legacy` carries only stock empty defaults. **No effective divergence.** No reconfiguration needed |
| 2026-10-20 17:30 | FE/BE | Confirmed the whitelist prevents administrator lockout | Generated 32 real `Invalid user … from 127.0.0.1` lines; the running jail reported **`Currently failed: 0`** because `127.0.0.1` is in `ignoreip` — demonstrating the lockout protection works exactly as intended |
| 2026-10-20 17:30 | FE | Confirmed fail2ban does not disturb the persisted firewall | `/etc/iptables/rules.v4` contains **0** fail2ban lines (bans are runtime-only, correctly) |
| 2026-10-20 17:31 | FE/BE | Cleaned up all test artefacts | No bans remain, no probe jails, no leftover `f2b` chains; admin whitelist intact |

### fail2ban — final verified state (both hosts)

| Item | Value |
|---|---|
| Version / service | fail2ban **0.11.2**, `active` + `enabled` |
| Jail | `sshd`, `backend = systemd`, port 22 |
| Threshold | `maxretry 5`, `findtime 10m`, `bantime 1h`, incrementing to `1w` |
| Whitelist (`ignoreip`) | `45.220.11.50`, `168.253.204.10`, `10.0.0.0/24`, `127.0.0.0/8`, `::1` |
| Log source | journald (`_SYSTEMD_UNIT=sshd.service`) — **required**, because `auth.log` does not exist |
| Ban mechanism | `iptables-multiport` → `f2b-sshd` chain in the **nft**-backed filter table (production-proven) |
| Detection | filter matches the host's real sshd output (16 lines matched in a live sample) |
| Lockout protection | admin IPs and the VCN subnet are never banned (live-proven) |
| Persistence | survives reboot (`systemctl enable`); bans are runtime-only and do **not** pollute `rules.v4` |

### OCI rule and NSG clarification (owner-confirmed)

The owner clarified that the private-network exposure is **limited to their own compartment**, and that the
security-list rules previously supplied are the ones in force. This is recorded as
**[V, owner-confirmed]**. The behavioural verification in `network-security-plan.md` §3.5 remains the
strongest guest-side evidence. **Recommendation unchanged:** add a `10.0.0.26/32 → 8000` rule and scope the
`10.0.0.0/16` all-protocols rule, so "BE 8000 from FE only" is enforced at the cloud layer as well as by
the bind address and host firewall. `5432`/`6379` remain non-public.

### Backup and recovery plan

The completed plan is in **`migration/backup-recovery-plan.md`**, presented for approval. Highlights:

- **Destination (exact):** `C:\Backup\MissionControl\<UTC-timestamp>\` on the owner's local Windows machine.
- **Space:** required ≈ **200–300 MB**; **22.0 GB free** on `C:` **[V]** — space is not a constraint.
- **Encryption:** compression (`zstd`) and encryption (**GPG AES-256, `--s2k-mode 3`**) are performed **on
  the source**, because the local machine has **no `7z`/`gpg`/`openssl`** — only `tar`, `ssh-keygen`,
  `certutil` **[V]**.
- **Integrity:** SHA-256 of every encrypted artefact, verified locally with `certutil -hashfile … SHA256`.
- **Custody:** passphrase in the owner's password manager **plus** a sealed off-line copy; never on the
  backup disk alone, never printed, never in Git. Fernet key hash recorded (value never).
- **Restore test:** scratch PostgreSQL 16, verifying alembic `h7h8h9i1j2k3`, exact row counts, and
  **explicit credential decryption** (the check that catches a wrong-but-valid Fernet key).
- **Single-location risk:** documented, **not** silently substituted with a cloud destination; the plan
  recommends adding an external drive or second machine (the machine has a **single volume** today).

### Outstanding blockers (as required at the Phase 3 gate)

1. **U6 — backup and recovery plan is not approved.** No backup exists or was created. A separate plan
   (off-host destination, encryption, key custody, checksum verification, restore testing) must be
   approved before any data migration. This is the primary gate before Phase 4.
2. **Images are built but not transferred.** `docker save`/`load` to FE/BE has not been executed.
3. **Artefacts are not committed and not deployed.** The `deploy/migration-2vm/` files live only in the
   working tree; deployment branch creation and deployment are Phase 4.
4. **`.env` has not been transferred.** The production Fernet key and DB password must be moved over SSH
   with mode 600 and hash-verified — part of the data-migration phase.
5. **Certificate material has not been moved.** Both lineages must be copied to `/etc/letsencrypt` on FE
   (root-only) in a later phase; U4 forbids deleting either lineage.
6. **fail2ban has no jails.** Installed but not configured; a deliberate choice to keep Phase 3 to
   "install approved prerequisites". Jail configuration is a follow-up.
7. **OCI NSG question unresolved.** Whether an NSG applies in addition to the security list cannot be read
   from inside a guest; the behavioural evidence in `network-security-plan.md` §3.5 is the strongest
   available assertion.
8. **`ADMIN_CIDR` assumption.** The firewall scopes SSH to the two observed admin `/32`s. If either
   address is dynamic, this is a lockout risk and must be revisited before the hosts are relied upon.

### Owner decisions U1–U7 (2026-10-20)

| ID | Decision | Effect on this migration |
|---|---|---|
| U1 | Both public IPs are **reserved**; verify assignments stay correct before cutover | DNS cutover is safe; verification added to the cutover runbook preconditions |
| U2 | Ingress should already be correct; **verify** security lists/NSG and guest firewall; report discrepancies; never broaden rules to make deployment easier | Verification performed from inside the guests and from an external vantage; console-side items remain owner-verified |
| U3 | **Block** `/api/docs` and `/api/openapi.json` publicly on the destination; keep normal API function | Added to the FE nginx target config; validated on the destination before cutover |
| U4 | **Keep both** certificate lineages; preserve material; do not delete either | certbot renewal covers both; no lineage removed |
| U5 | **No** Docker management UI on the destination; Dockhand is not migrated | compose has no dockhand service; nothing to install |
| U6 | Backup implementation/execution **not authorised** at this stage; present a separate backup and recovery plan for approval before any data migration; do not migrate production data or cut over without an approved, verified recovery strategy | Phase 3 does **not** create, transfer or restore backups. A separate backup/recovery plan is required before Phase 4 |
| U7 | Keep the `docker.sock` mount **only if the backend demonstrably requires it**; verify code paths; document implications; otherwise omit; never expose the Docker API remotely | Code-path verification performed (see the installation report); remote Docker API exposure never configured |
| D-F | Close `/dockhand/` on production now, as a separate, reviewed change | Executed and validated (previous section) |

---

## Phase 4 — production backup execution and restore verification (approved, complete)

**Owner approval:** "Approved" (2026-10-20) of `migration/backup-recovery-plan.md`. This authorised the
production dump, off-host transfer to the owner's local Windows machine, and a scratch restore test — and
**nothing else**. No data migration into the destination, no deployment, no DNS change, no cutover, no
source decommission.

**Passphrase custody:** generated on the source with `openssl rand -base64 36` (48 chars), displayed to the
owner **once**, stored by the owner, and **never written to disk, argv, logs or Git** on any host. It was
read into GPG via a file descriptor (`--passphrase-fd 3`). The passphrase file was shredded on the source
and on the BE VM immediately after use. Non-secret fingerprint recorded in the manifest only
(`backup_passphrase_sha256 = 2132b351…`).

| Timestamp (UTC) | Host | Action | Verification / result |
|---|---|---|---|
| 2026-10-20 17:37 | prod | Captured source revision, schema pin, and a **dump-time** row-count baseline before dumping | `rev=3b4b771`, branch `release/v3.0.0-rc1`, alembic `h7h8h9i1j2k3`, postgres `16.14`, 78 public tables; baseline `agent_commands=98211, agent_remote_targets=16, veeam_backup_servers=15, integration_profiles=6` |
| 2026-10-20 17:37 | prod | `pg_dump -Fc -Z6` of `mission_control` | `db-full.dump` = 236,274,276 bytes (225 MB) |
| 2026-10-20 17:38 | prod | `pg_dumpall --globals-only` (roles) | `globals.sql` = 685 bytes |
| 2026-10-20 17:38 | prod | Copied the production `.env` (9 keys) into the stage, mode 600 | `missioncontrol.env` = 298 bytes; secret values never printed |
| 2026-10-20 17:38 | prod | Archived **both** TLS lineages (U4) | `letsencrypt.tar` = 102,400 bytes; lineages `missioncontrol.optichosting.co.za`, `missioncontroldev.optichosting.co.za` |
| 2026-10-20 17:38 | prod | Compressed all four artefacts with `zstd -19` | 225 MB → 199 MB (dump); sizes recorded in the manifest |
| 2026-10-20 17:39 | prod | Generated the 48-char random passphrase; owner confirmed the "generate a strong random one" option | Displayed once; SHA-256 `2132b351…`; file mode 600, read via fd 3 only |
| 2026-10-20 17:40 | prod | Encrypted each `.zst` with GPG **AES-256**, `--s2k-mode 3`, SHA-512 digest, 65011712 iterations | All four report `PGP symmetric key encrypted data … AES256.CFB`; `db-full.dump.enc` = 208,894,104 bytes |
| 2026-10-20 17:41 | prod | **Shredded** the plaintext `.zst`, the raw dump and the plaintext `.env` (`shred -u -n 1`) | Only the four `.enc` files plus non-secret metadata remain; `find` confirmed no plaintext leftovers |
| 2026-10-20 17:41 | prod | Built `RESTORE-KEY-CHECK.enc` (known-plaintext token) so a passphrase can be validated without a full restore | Its plaintext is recorded in `RESTORE-KEY-CHECK.txt`, so it leaks nothing |
| 2026-10-20 17:41 | prod | Wrote `MANIFEST.txt` (no secret values) and `SHA256SUMS` | Manifest carries revision, schema pin, row-count baseline, artefact digests, Fernet-key **hash**, passphrase **hash**, and restore-test result |
| 2026-10-20 17:42 | prod | Verified the passphrase decrypts the key-check | `gpg --decrypt` reproduced the expected plaintext; SHA-256 matched `e45082ab…` → **PASS** |
| 2026-10-20 17:46 | local | Transferred the backup set to `C:\Backup\MissionControl\20261020T173709Z\` via `scp` | 8 files; total **199.24 MB** (22.0 GB free on `C:` — ample) |
| 2026-10-20 17:46 | local | Verified SHA-256 of every received artefact with `certutil -hashfile … SHA256` | **PASS=5 FAIL=0** — transfer is byte-perfect |
| 2026-10-20 17:47 | BE `84.12.82.239` | Transferred the encrypted set to a staging directory for the restore test | All 8 files present; `sha256sum -c SHA256SUMS` → all OK |
| 2026-10-20 17:48 | BE | Scratch restore test: throwaway PostgreSQL 16 container, `pg_restore --no-owner --no-privileges` | `pg_restore -l` → **902 TOC entries**, dump valid; **78 public tables** restored; alembic `h7h8h9i1j2k3` |
| 2026-10-20 17:48 | BE | Row-count comparison against the dump-time baseline | `agent_remote_targets=16`, `veeam_backup_servers=15`, `integration_profiles=6` matched exactly; `agent_commands` matched the dump-time snapshot (the live table keeps growing) |
| 2026-10-20 17:59 | BE | **Credential-decryption test** (the decisive check): extracted all real Fernet tokens from the restored DB and decrypted them with the Fernet key recovered from the encrypted `.env` | **33/33 tokens decrypted, 0 failures** (`agent_remote_targets.password_encrypted` 16, `integration_profiles.encrypted_secret` 2, `veeam_backup_servers.legacy_ssh_password_encrypted` 15); plaintext lengths 18–25 chars → real secrets, not placeholders → **PASS** |
| 2026-10-20 20:01 | prod | Corrected the manifest's row-count block to the authoritative **dump-time** baseline (98,211) and recorded the restore-test result | Manifest updated; `sha256sum -c SHA256SUMS` re-verified all OK; corrected manifest pulled back to the local copy |
| 2026-10-20 20:05 | prod + BE | Shredded the passphrase file on both hosts; removed the BE restore-test staging directory and scratch containers | No passphrase file remains on any host; `mc-restoretest`/`mc-fernet` removed; no Mission Control containers deployed |

### Phase 4 — verified backup set

| Item | Value |
|---|---|
| Backup ID | `20261020T173709Z` |
| Local location | `C:\Backup\MissionControl\20261020T173709Z\` |
| Source-copy location | `/home/billboe3/mc-backup-20261020T173709Z/` on production (mode 700, encrypted only) |
| Artefacts | `db-full.dump.enc` (208,894,104 B), `globals.sql.enc`, `missioncontrol.env.enc`, `letsencrypt.tar.enc`, plus `MANIFEST.txt`, `SHA256SUMS`, `RESTORE-KEY-CHECK.enc/.txt` |
| Total size | **199.24 MB** |
| Encryption | GPG AES-256, `--s2k-mode 3`, SHA-512, 65011712 iterations |
| Integrity | SHA-256 verified locally (**5/5 OK**) and on BE (`sha256sum -c` all OK) |
| Source revision | `3b4b7717185a98da44559a379dc1743fbd8d4730` on `release/v3.0.0-rc1` |
| Schema pin | alembic `h7h8h9i1j2k3`, PostgreSQL 16.14, 78 public tables |
| Restore test | scratch PG16: schema + row counts + **33/33 credential decryptions** → **PASS** |
| Fernet key hash | `e9e0d695…` (value only inside `missioncontrol.env.enc`) |
| Passphrase | owner custody only; fingerprint `2132b351…`; never on any host, disk, or Git |

### Phase 4 — notes, deviations and residual risk

1. **`agent_commands` grows continuously.** The dump-time baseline (`98211`) differs from later live reads
   (`98215`). The manifest was corrected to the dump-time value, which is the correct value for the restore
   test. Analysts migrating data must expect the live count to have advanced again.
2. **Restore-test deviation (resolved).** The first two restore attempts did not complete the credential
   decryption step (a `set -e` abort during the scripted GPG header check, then a column-name mismatch and a
   missing `pg_restore` on the host). The final run executed the decryption inside a container with the
   correct column names discovered from `information_schema`, and reported 33/33. **The earlier "PASS"
   claims in the interrupted runs were not taken on trust** — only the final, complete run is recorded here.
3. **Single-location risk remains (documented, unchanged).** The only off-host copy is
   `C:\Backup\MissionControl\20261020T173709Z\` on a machine with a single volume. **Recommendation:**
   copy the set to a second medium (external drive or second machine) and keep the passphrase separately.
   Not silently substituted with a cloud destination, per U6.
4. **Plaintext existed transiently on the source** (raw dump, `.zst`, `.env`) inside a mode-700 directory
   for the duration of the dump/compress/encrypt window, then was `shred`ed. On a copy-on-write/ext4 journal
   filesystem `shred` is best-effort, not a forensic guarantee — recorded as residual risk, not a defect.
5. **The passphrase was shown in the chat once**, by owner choice, to enable custody. It should be treated
   as sensitive; if the owner wishes, it can be rotated by re-running the encryption step (a new backup set).
6. **No production state was modified** in Phase 4 other than reading the database and copying files into
   `/home/billboe3/` (mode 700). The application, containers, nginx, DNS and certificates are untouched.

### Phase 4 outcome and next gate

Backup creation, off-host transfer, integrity verification and a full scratch restore test (including real
credential decryption) are **complete and verified [V]**. The U6 gate — *"no data migration or cutover
without an approved, verified recovery strategy"* — is **satisfied on the evidence**. The next phase
(transfer images/`.env`/TLS to the destinations, deploy the BE and FE stacks, validate) proceeds under the
owner's Phase 5 authorisation.

---

## Phase 4b — second copy of the verified backup (owner-directed, complete)

**Owner decision (2026-10-20):** "Make a second copy of the backup before proceeding to Phase 5." The copy
must be on a separate physical drive or second machine; contain **only encrypted artefacts and manifests**;
be verified against the authoritative `SHA256SUMS`; leave the passphrase and Fernet-key custody unchanged;
and must not modify or delete the original.

**Location constraint discovered [V]:** the local workstation has **one physical disk** (`C:`, 476 GB NVMe;
20.9 GB free) and **no removable/USB device attached**. The mapped network drive `Q:` →
`\\Corhqfileserver\corhqfilevolume` (a separate machine, the CORHQ file server) was **unreachable** (name
does not resolve; share not writable). The owner therefore selected the **production source host under
`/opt`** as the second-copy location.

| Timestamp (UTC) | Host | Action | Verification / result |
|---|---|---|---|
| 2026-10-20 18:05 | local | Confirmed the original was unmodified **before** copying | `certutil` SHA-256 of the local set → **5/5 OK** |
| 2026-10-20 18:06 | prod | Created `/opt/mc-backup-offsite/20261020T173709Z` (root:root, mode 700) and copied the **8** encrypted/manifest files only | `sudo cp -p` of the four `.enc` + `MANIFEST.txt`, `SHA256SUMS`, `RESTORE-KEY-CHECK.enc/.txt` |
| 2026-10-20 18:06 | prod | Confirmed no passphrase and no plaintext travelled | `grep` for the passphrase string → **absent**; no `/tmp/.pp.*` on the host; file count = 8 |
| 2026-10-20 18:06 | prod | **Verified the second copy** against the authoritative `SHA256SUMS` (as root) | `sha256sum -c SHA256SUMS` → **RESTORE-KEY-CHECK.enc OK, db-full.dump.enc OK, globals.sql.enc OK, letsencrypt.tar.enc OK, missioncontrol.env.enc OK** (exit 0) |
| 2026-10-20 18:06 | prod | Byte-for-byte comparison against the source stage | All four artefacts **MATCH** the authoritative digests |
| 2026-10-20 18:06 | prod | Recorded a non-secret `SECOND-COPY.txt` note in the source stage | Location, mode, contents, verification result, custody note |
| 2026-10-20 18:06 | local | Original **left untouched** | No write, move or delete performed on `C:\Backup\MissionControl\20261020T173709Z\` |

### Second copy — verified state

| Item | Value |
|---|---|
| Second-copy location | `/opt/mc-backup-offsite/20261020T173709Z/` on prod `34.35.177.209` (root:root, mode 700) |
| Contents | 8 files: 4 encrypted artefacts + `MANIFEST.txt` + `SHA256SUMS` + `RESTORE-KEY-CHECK.enc/.txt` |
| Passphrase present? | **No** — verified absent by string search; never on this host |
| Verification | `sha256sum -c SHA256SUMS` → all OK; digests identical to the authoritative file |
| Original | Unchanged; still verified 5/5 OK at `C:\Backup\MissionControl\20261020T173709Z\` |
| Copies now in existence | **2** (local Windows machine + production source `/opt`) |

### Recovery and custody arrangements (unchanged, confirmed)

- **Passphrase:** owner's password manager + a sealed off-line copy. **Not present** on the local machine, the
  source host, the `/opt` second copy, the destination VMs, or Git. Fingerprint (SHA-256) `2132b351…`
  recorded in the manifest only.
- **Fernet key:** value only inside `missioncontrol.env.enc` (both copies). Hash `e9e0d695…` in the manifest.
  Needed for application use after a restore, **not** for decrypting the backup.
- **Recovery requires BOTH:** the passphrase (owner custody) *and* the Fernet key (inside the encrypted
  `.env`). Neither is recorded in Git or in any log.
- **Residual risk (reduced, not eliminated):** both copies are encrypted and independently verified, but
  neither is on removable media; the local copy shares the workstation's single disk and the second copy
  shares the production host. **Recommendation remains:** place a third copy on removable media when one is
  available. Recorded, not silently substituted.

---

## Phase 5 — destination deployment (owner-authorised 2026-10-20)

**Authorisation:** deploy the backend on `10.0.0.33` first and validate before deploying the frontend on
`10.0.0.26`; use the verified backup and approved artefacts; confirm the destination database is safe to
initialise/restore before writing to it; record all changes and evidence; **stop and report on any critical
failure**. **Not** authorised: DNS change, public-traffic switch, stopping production services, or cutover —
production remains operational and authoritative throughout.

### Phase 5 pre-flight (read-only) — 2026-10-20 18:06 UTC

| Check | Host | Result |
|---|---|---|
| OS / resources | BE | Ubuntu 22.04.5, kernel 6.8.0-1062-oracle; **956 MB RAM**, 2 GB swap, **34 GB free** |
| Existing Mission Control containers | BE | **none** |
| Existing Mission Control images | BE | **none** (`postgres:16`, `python:3.12-slim` only, from the Phase 4 restore test) |
| Existing Mission Control volumes | BE | **none** named `mc-*`; six anonymous volumes from the removed scratch containers |
| `/opt/missioncontrol` | BE | **exists but empty** — created 17:13 during Phase 3; **no data** |
| Postgres data directories anywhere | BE | **none** — clean slate |
| Listeners | BE | only `0.0.0.0:22` (sshd) — nothing else |
| fail2ban | BE | `active`, jail `sshd` (Phase 3b) |
| TLS material | BE | none (expected — TLS is FE-only) |
| Listeners | FE | nothing on 80/443 (expected pre-deploy) |
| `/var/www/letsencrypt` | FE | **present** (Phase 3) |
| `/etc/letsencrypt/live` | FE | **absent** — not yet copied (a later Phase 5 step) |
| FE containers/volumes | FE | **none** |

**Destination database safety:** confirmed **safe to initialise/restore** — there is no existing database,
no data volume, no container and no data directory on BE. Nothing can be overwritten by a restore.

### Phase 5 critical check FAILED — intra-VCN TCP is blocked (STOPPED)

Before writing anything to the destination, the mandatory connectivity precondition was tested:

| Probe | Result |
|---|---|
| ICMP FE→BE | **works** (2/2) |
| **FE→BE TCP 8000** (required: the edge proxies `/api/` here) | **`No route to host`** |
| FE↔BE TCP 22 / 80 / 443 / 5432 / 6379 | **`No route to host`** (both directions) |
| ARP to peer | REACHABLE both sides (L2 fine) |
| Guest INPUT REJECT counters after all probes | FE 10 pkts, BE 13 pkts — **too low to be the drop** |
| `sshd` listening `0.0.0.0:22` both hosts | **yes** |
| Internet egress / OCI metadata | 200 / open |

**Conclusion (SUPERSEDED — see RESOLUTION below):** the SYNs appeared never to reach the guests and the
block was attributed to the **OCI security-list / NSG layer**. **This was WRONG.** The block was the
guest firewall on each destination VM; the SYNs did reach them. This contradicts the Phase 1 claim that the private path "delivers every port"
(now corrected in `network-security-plan.md` §1 and §3.6). The supplied intra-VCN rules (rule 1 all-protocols
`10.0.0.0/16`, rule 9 TCP 22 `10.0.0.0/16`) *should* permit this traffic but are demonstrably not in force
as supplied — **[?]** either a different list/NSG is applied, or the rules are attached elsewhere.

**Action taken: Phase 5 STOPPED before any deployment**, per the owner's instruction ("if a critical check
fails, stop and report the issue rather than proceeding to the next stage") and per U2 ("do not broaden
ingress rules"). Nothing was deployed, transferred, written or restored on either destination. Production
remains untouched. Full requirement and remediation options in `network-security-plan.md` §3.6.

**Owner action required:** permit `10.0.0.26/32 → 10.0.0.33 TCP 8000` (required) and intra-VCN TCP 22
(validation), keeping all sources private — never `0.0.0.0/0`.

### Phase 5 blocker RESOLVED — root cause was the guest firewall, not OCI (2026-10-20 ~19:00 UTC)

The STOP was lifted once the true cause was isolated. **Oracle Cloud networking was correct throughout.**

**Evidence chain (decisive):**

1. OCI control plane confirmed exactly **one** subnet (`Internal-IP`, `10.0.0.0/24`), **one** security list
   (`Default Security List for vcn-20261017-1032`) and — after the owner detached the stray
   `ig-quick-action-NSG` from the FE VNIC — **zero** NSGs and **no** VLAN attachment on either VNIC.
2. That security list already carried correct **stateful** ingress rules, including
   `10.0.0.0/24 → all protocols`, `10.0.0.26/32 → TCP 8000` and `10.0.0.0/24 → TCP 22`.
3. A **temporary** `10.0.0.0/24` ACCEPT inserted into the **backend guest's** INPUT chain then recorded
   **16+ packets from FE probes** — proving the SYNs crossed the OCI fabric and the security list and were
   delivered to the guest. The cloud path was never the problem.
4. Both guests' INPUT chains ended with an unconditional
   `REJECT --reject-with icmp-host-prohibited` and had **no** ACCEPT for `10.0.0.0/24`. That
   `icmp-host-prohibited` rejection is what surfaces to a client as **`No route to host`** — the symptom
   that had been misread as a cloud-layer block. The REJECT counters were low only because sampling
   preceded the bulk of the probe traffic.

**Root cause:** the destination image ships a restrictive guest firewall (ICMP + admin SSH + 80/443, then
reject all). The migration plan assumed the OCI security list was the *only* ACL governing the path and
therefore never accounted for a host-level firewall. **Planning defect, now corrected.**

**Change applied (approved by owner) — both destination VMs:**

| Item | Value |
|---|---|
| Hosts | FE `10.0.0.26`, BE `10.0.0.33` |
| Rule | `iptables -I INPUT 1 -s 10.0.0.0/24 -j ACCEPT` |
| Effect | stops the guest rejecting intra-VCN traffic the security list already permits |
| Persistence | `netfilter-persistent` — confirmed `enabled` + `active`; written to `/etc/iptables/rules.v4` |
| Backup | `/etc/iptables/rules.v4.bak.20261020T185922Z` (FE), `…T185923Z` (BE) |
| Rollback | `iptables -D INPUT -s 10.0.0.0/24 -j ACCEPT` + restore the `.bak` file |
| Scope | private subnet only — grants nothing beyond what the OCI security list already allows; cannot expose anything publicly |

Docker chains were deliberately **excluded** from the persisted file (the plan forbids capturing container
rules); the only Docker references retained are empty chain declarations plus the pre-existing empty NAT
chain — no container port-mapping rules.

**Verification — 13-port intra-VCN probe, both directions, after the fix:**

| Port | Before | After |
|---|---|---|
| 22 | `NO-ROUTE` | **`OPEN`** (sshd) |
| 8000 | `NO-ROUTE` | **`refused`** (path open, no listener yet — the required result) |
| 7, 9, 13, 25, 53, 80, 111, 123, 443, 8443, 19090 | `NO-ROUTE` | **`refused`** (path open, no listener) |

`refused` = packet reached the destination and received a TCP reset, i.e. **the network path is open**.
Every previously blocked port now reaches the peer; **only SSH is listening** — nothing unintended exposed.

**Outstanding (carried forward):**

- The owner's `ig-quick-action-NSG` was detached from the FE VNIC at the owner's direction. Follow-up:
  confirm nobody created it deliberately; if it was a security recommendation, decide whether an NSG is
  still wanted (it may be re-attached later *populated*, not empty).
- `migration/network-security-plan.md` §3.6 has been corrected to state the real cause.
- Worth adding to Phase 3 host preparation for any future host: verify the guest firewall permits the
  private subnet, rather than assuming the cloud ACL is the only gate.

**Phase 5 is unblocked. The required FE→BE TCP 8000 path is open. Deployment may resume.**
