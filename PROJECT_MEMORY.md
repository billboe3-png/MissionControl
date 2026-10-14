# Mission Control — Project Memory

> This file captures key decisions, context, and historical information that must persist across sessions and machines. It is the project's long-term memory.

---

## Project Identity

- **Repository**: https://github.com/billboe3-png/MissionControl
- **Project name**: Mission Control
- **Product**: IT operations dashboard / workspace with agent-first architecture
- **Edition focus**: Community Edition v3.0.0-RC1 → v1.0
- **Stack**: FastAPI (Python 3.12) + SQLAlchemy 2 + Alembic + Pydantic Settings (backend), React + TypeScript + Vite (frontend), Agent (Python, systemd)

---

## Key Architectural Decisions

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-08 | Agent-first architecture | All remote operations must go through the Agent; no direct server-to-infrastructure bypass |
| 2026-08 | Plugin-based integrations | Each integration (Git, Docker, Zabbix, Veeam, UniFi, MikroTik, D-Link) is a separate plugin in `backend/app/plugins/installed/` |
| 2026-08 | Agent plugins for network devices | MikroTik and D-Link use agent-side plugins with namespace dispatch (`mikrotik`, `dlink`) |
| 2026-08 | Alembic for all schema changes | Every plugin brings its own migrations; `alembic upgrade head` required before tests |
| 2026-08 | Fernet secret key for CI | `alembic/env.py` loads Settings before conftest; fake keys fail validation |
| 2026-10-14 | Agent-side DB tool discovery | The Veeam agent relay must locate `psql.exe`/`sqlcmd.exe` on the target regardless of installed version/path — never hardcode a version-specific path (the EPHKSDC01 failure was a hardcoded PostgreSQL 15 path on a PostgreSQL 17 host) |
| 2026-10-14 | Windows PostgreSQL relay auth via `pg_ident.conf` UPN form | The relay runs non-interactively as `DOMAIN\user`; PostgreSQL `sspi` maps need a `pg_ident.conf` entry in **UPN** form (`user@DOMAIN`, e.g. `Administrator@KOSTER`) — the `DOMAIN\user` form does not match |
| 2026-10-14 | Backend tests run against in-memory SQLite | `backend/tests/conftest.py` builds its own SQLite DB, so the suite can run inside `missioncontrol-backend-1` without touching production PostgreSQL |

---

## Environment Context

### Server (GCE)
- **Host**: `34.35.177.209`
- **User**: `billboe3`
- **SSH key**: `~/.ssh/id_ed25519`
- **Project path**: `/opt/MissionControl` (canonical repo for commits/pushes)
- **Reference main clone**: `/tmp/mc-main`
- **Test venv**: `/tmp/testvenv/bin/python -m pytest`
- **Ruff venv**: `/tmp/venv/bin/ruff`
- **Test containers**: `mc-test-postgres` (5432), `mc-test-redis` (6379)

### Environments
- **LIVE**: `https://Missioncontrol.optichosting.co.za` (branch: `main`)
- **DEV**: `https://missioncontroldev.optichosting.co.za` (branch: `develop`)

### Containers (production)
- `missioncontrol-backend-1` — FastAPI
- `missioncontrol-frontend-1` — React/Vite (served by nginx)
- `missioncontrol-nginx-1` — Reverse proxy
- `missioncontrol-postgres-1` — PostgreSQL
- `missioncontrol-redis-1` — Redis

---

## Plugin Inventory (as of RC1)

### Backend Plugins (`backend/app/plugins/installed/`)
| Plugin | Type | Tables | Status |
|--------|------|--------|--------|
| git | integration | git_repos, git_credentials, etc. | Active |
| hyperv | integration | hyperv_* | Active |
| official_dlink | agent-relay | dlink_switches, dlink_remote_targets, dlink_mac_entries, dlink_vlans, dlink_port_vlans | Active (NEW) |
| official_docker | integration | docker_* | Active |
| official_mikrotik | agent-relay | mikrotik_servers, mikrotik_remote_targets, mikrotik_interfaces, etc. | Active (NEW) |
| official_unifi | integration | unifi_* | Active |
| official_veeam | integration + collector | veeam_* (jobs, sessions, repos, servers, snapshots) | Active |
| system_info | system | — | Active |
| zabbix | integration | zabbix_* | Active |

### Agent Plugins (`.agents/agent/plugins/`)
| Plugin | Namespace | Capabilities |
|--------|-----------|--------------|
| dlink_plugin.py | `dlink` | CLI, REST API, WebUI stream, inventory, MAC, VLAN |
| mikrotik_plugin.py | `mikrotik` | CLI, REST, native API, WebFig relay, neighbor discovery |
| active_directory_plugin.py | `active_directory` | AD inventory via PowerShell/SSH |

---

## Database Migration History (Key Revisions)

| Revision | Description |
|----------|-------------|
| `a1b2c3d4e5f7` | Add Zabbix plugin tables |
| `b2c3d4e5f6a8` | Add Veeam plugin tables |
| `c3d4e5f6a7b9` | Add UniFi plugin tables |
| `d4e5f6a7b8c0` | Add Docker plugin tables |
| `471bafbbdcd7` | Add missing Veeam server fields |
| `e5f6a7b8c9d0` | Add Veeam snapshots table |
| `m1dlink0001` | Add D-Link plugin tables |
| `m1kr0t1k0001` | Add MikroTik plugin tables |
| `m2kr0t1k0002` | Add MikroTik relay columns |
| `m3kr0t1k0003` | Make MikroTik relay required |

---

## CI Gotchas (from AGENTS.md — preserved)

1. **Secret key**: Must be real Fernet key in CI. `alembic/env.py` loads Settings *before* conftest overrides. Use `Fernet.generate_key().decode()`.
2. **Migrations first**: `alembic upgrade head` required before pytest — plugin tables come from Alembic.
3. **Redis host**: `REDIS_HOST: redis` must resolve to 127.0.0.1. CI adds `/etc/hosts` entry.
4. **Python 3.12**: `asyncio.get_event_loop().run_until_complete()` raises `RuntimeError`. Use `asyncio.run()`.
5. **Mock docker**: `conftest.mock_docker` patches health/remote and `official_docker.cache.cache_manager.get_summary`.

---

## Recent Work (RC1 Sprint)

### Veeam DB Bridge (commit `5f0045b`)
- Real job/session/repo data via psql
- Session-expire fix in `AgentSshExecutor`
- Agent command poll 5-15s
- Removed dead `app/providers/veeam/provider_factory.py`
- Veeam dashboard for CORHQVEEMA live with real data
- Agent bundle `v0.0.15`, `veeam_backup_servers.timeout=120`

### Veeam Agent-Relay Reliability (EPHKSDC01) — 2026-10-14
- **Symptom**: Jobs page showed "Veeam DB bridge unavailable" for `EPHKSDC01` even though the agent was online.
- **Root cause 1 (code)**: `.agents/agent/plugins/veeam_plugin.py` hardcoded `C:\Program Files\PostgreSQL\15\bin\psql.exe`; the host has only **PostgreSQL 17**, so the relayed PowerShell failed with "The term ... is not recognized".
  - Fix: agent-side, version-agnostic discovery — `_PSQL_CANDIDATES` (PG 15,16,17,18,14,13,12; PG15 kept first to preserve EBENCDC), `_psql_paths(target_id)` / `_resolve_psql_path(target_id)` (per-target cache), `_resolve_psql_path_via_remote(remote_manager, target_id)` for the Windows-local `_collect_jobs_via_relay`. Used by `_db_detect`, `_run_db_query_via_relay`, and `_collect_jobs_via_relay`.
- **Root cause 2 (host auth)**: PostgreSQL `sspi map=veeam` rejected the relay identity `KOSTER\Administrator` → `FATAL: SSPI authentication failed for user "postgres"`. `pg_ident.conf` matched only UPN-format entries (`admin_barry@KOSTER`, `"SYSTEM@NT AUTHORITY"`).
  - Fix (user-approved option 1): append `veeam Administrator@KOSTER postgres` to `C:\Program Files\PostgreSQL\17\data\pg_ident.conf` (backup `pg_ident.conf.bak`) and `pg_ctl reload`. The `DOMAIN\user` form (`KOSTER\Administrator`) does **not** work.
- **Validation**: `SELECT current_user` → `postgres`; provider `collect_dataset(... "job_stats_daily")` → `success: true` with real jobs (`EPHKSDC01_EXT`, `EPHKSDC01_EXT\EPHKSDC01_NAS`); `collect_all` refreshed all 8 `veeam_snapshots` datasets for server 29.
- **Deploy**: agent bundle `v0.0.45` (agent 20 self-updated); `.agents/agent/tests/test_veeam_mssql.py` **42 passed**.
- Also in this change: `column_case` now accepts `auto` in `agent_remote_target` (ORM model + API schema), matching `bridge.py`.

### MikroTik Agent-Relay
- Backend plugin: `official_mikrotik` with routes at `/api/v1/plugins/mikrotik/`
- Agent plugin: `.agents/agent/plugins/mikrotik_plugin.py`
- Namespace dispatch patched on Agent 2 (prod-01) with `"mikrotik"`
- Test target: `10.161.0.14` (RouterOS 7.24) via Agent 6 (zabbix-proxy)

### D-Link Agent-Relay
- Backend plugin: `official_dlink` with routes at `/api/v1/plugins/dlink/`
- Agent plugin: `.agents/agent/plugins/dlink_plugin.py`
- Namespace dispatch patched on Agent 2 with `"dlink"`
- Test target: `10.161.0.12` (DGS-1210) via Agent 6 (zabbix-proxy)
- Credentials: admin / `RandomCrap304!` (password only, no username)

### Frontend Pages Added
| Plugin | Pages | Routes |
|--------|-------|--------|
| D-Link | DashboardPage, SwitchesPage, PortsPage, TerminalPage, WebUIPage | `/dlink`, `/dlink/ports/:id`, `/dlink/terminal/:id`, `/dlink/webui/:id` |
| MikroTik | (existing) | `/mikrotik/...` |

### Navigation Updates
- D-Link group added under "Infrastructure"
- Updated `frontend/src/config/navigation.ts` and `frontend/src/App.tsx`

---

## Known Issues / Technical Debt

| Issue | Location | Status |
|-------|----------|--------|
| Veeam circular import | `official_veeam/api.py` ↔ `provider.py` | Causes backend crashes; needs fix |
| Agent 6 offline | systemd start-limit-hit | Requires manual `reset-failed && start` |
| D-Link import | Local `relay.py` wrong `AgentCommand` import | Container fixed; local needs sync |
| Local OneDrive WIP | Uncommitted changes on git/hyper-V plugins | Do not commit from local |

---

## Test Targets (Live Infrastructure)

| Target | IP | Type | Agent | Credentials |
|--------|-----|------|-------|-------------|
| CORHQVEEMA | — | Veeam | Agent 2 (prod-01) | Veeam creds |
| EPHKSDC01 | 192.168.12.2 | Veeam (PostgreSQL 17) | Agent 20 (Eagles Pride Koster) | Windows SSPI via relay user `Administrator` (mapped in `pg_ident.conf` as `Administrator@KOSTER`); server id 29, target id 17 |
| MikroTik | 10.161.0.14 | RouterOS 7.24 | Agent 6 (zabbix-proxy) | SSH |
| D-Link | 10.161.0.12 | DGS-1210 | Agent 6 (zabbix-proxy) | admin / RandomCrap304! |
| Zabbix proxy | 10.161.0.10 | Zabbix | Agent 6 (zabbix-proxy) | — |

---

## Agent 2 (prod-01) — GCP Server
- Has namespace dispatch patched for `mikrotik` and `dlink`
- Runs in Docker: `/opt/mission-control-agent/`
- Not the same as `.agents/` in repo (that's source)

---

## Agent 6 (zabbix-proxy) — 10.161.0.10
- Separate machine; server cannot SSH into it directly
- Runs Agent as systemd service: `mission-control-agent`
- Goes offline after restart commands (systemd start-limit-hit)
- Recovery: `sudo systemctl reset-failed mission-control-agent && sudo systemctl start mission-control-agent`
- Has network access to 10.161.0.12 (D-Link) and 10.161.0.14 (MikroTik)

---

## Important File Locations

| Purpose | Path |
|---------|------|
| Project control | `MISSION_CONTROL_PROJECT_CONTROL.md` |
| Roadmap | `ROADMAP.md` |
| This memory | `PROJECT_MEMORY.md` |
| Agent instructions | `AGENTS.md` |
| Backend plugins | `backend/app/plugins/installed/` |
| Agent plugins | `.agents/agent/plugins/` |
| Alembic migrations | `backend/alembic/versions/` |
| Frontend pages | `frontend/src/pages/{dlink,mikrotik,veeam,unifi,zabbix,...}/` |
| Tests | `backend/tests/` |

---

## Verified CI Status (latest)

- **Known good baseline (2026-10-14)** — tag `v3.0.0-rc1-known-good` on `release/v3.0.0-rc1`: Veeam agent-relay EPHKSDC01 fix (version-agnostic `psql` discovery) + `column_case` `auto` support + documentation sync. Agent tests **42 passed**; backend Veeam / `agent_remote_target` suites **PASS**; ruff clean on changed files; frontend build green; live EPHKSDC01 validation **`success: true`** (all 8 `veeam_snapshots` refresh).
  - Harness caveat: running the backend suite **inside the production `missioncontrol-backend-1` container** can hang on lifespan / real-integration tests (`test_veeam_plugin.py`, `test_veeam_routes.py`) — use targeted files there, or a clean test env for the full suite.
- Latest full backend run on `release/v3.0.0-rc1` (`3332a8b`): **1700 passed / 2 failed (Python-3.11-venv-only env checks) / 1 skipped**
- The 2 failures (`test_startup_config::test_valid_returns_dict`, `test_marketplace::test_check_all_compatible`) assert Python**3.12+**; server venv is **3.11.15** → they pass in CI (both workflows pin `PYTHON_VERSION: 3.12`). Never "fix" them.
- Tenancy/authz hardening shipped `9b80d6f..7d31f5b` (`edf06a6` + `578c0ac` + `7d31f5b`); ruff clean on all 15 changed files; targeted **160 passed**.
- Veeam stale-test fix `3332a8b`: corrected `bridge.py` (model attrs `url`/`username`/`encrypted_password`, SQL cols `rest_url`/`rest_username`/`rest_password_encrypted`), restored `_first_server` enterprise-ordering (lost in `fa77db2`), removed obsolete `tests/test_veeam_provider.py` (`578c0ac`). Targeted veeam **68 passed**.
- Full-suite baseline pre-fix verified via `git stash`: all 24 failures pre-existed at HEAD `9b80d6f`; 22 were stale Veeam tests, 2 env-only.

## Test Infrastructure (server)

- Temp containers (running, host ports bound): `mc-test-postgres` (0.0.0.0:5432), `mc-test-redis` (0.0.0.0:6379).
- Server venv **3.11.15** at `/opt/MissionControl/backend/.venv` (AGENTS.md top-level snippet is stale regarding Python version).

---

## Parking Lot (Ideas Not for RC1)

| Idea | Reason | Potential Sprint |
|------|--------|------------------|
| Edge agent support (IoT) | Not required for RC1 | 4.x |
| Workflow orchestration engine | Not required for RC1 | 4.x |
| GitOps integration | Not required for RC1 | 4.x |
| Terraform provider | Not required for RC1 | 4.x |
| OpenTelemetry integration | Not required for RC1 | 4.x |
| Secret manager integration | Not required for RC1 | 4.x |
| Multi-region agent federation | Enterprise feature | 4.x |
| OPA-based RBAC policies | Enterprise feature | 4.x |
| AI-powered playbook generation | Enterprise feature | 4.x |
| Mobile-responsive terminal UI | Not required for RC1 | 3.3.0 |
| Plugin marketplace reviews/ratings | Not required for RC1 | 3.3.0 |

---

## Remote Edit Loop (Standard Procedure)

1. Edit local temp copy
2. `scp <file> billboe3@34.35.177.209:/opt/MissionControl/backend/<path>`
3. Run checks via `ssh ... bash /tmp/script.sh`
4. **Never** use `&&` inside PowerShell-quoted ssh commands — use a script file
5. Commit/push from server `/opt/MissionControl` only