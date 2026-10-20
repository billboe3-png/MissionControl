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
