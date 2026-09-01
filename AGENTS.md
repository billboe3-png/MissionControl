# AGENTS.md — Mission Control

> **MANDATORY**: Before any significant work, read `MISSION_CONTROL_PROJECT_CONTROL.md`, `ROADMAP.md`, and `PROJECT_MEMORY.md`. Inspect Git state. Determine the current objective.

Mission Control is an IT operations dashboard / workspace. Stack:
- **Backend**: FastAPI (Python 3.12) + SQLAlchemy 2 + Alembic + Pydantic Settings, in `backend/`
- **Frontend**: React + TypeScript + Vite, in `frontend/`
- **Plugins/agents**: `backend/app/plugins/installed/` (git, docker, zabbix, veeam, unifi, hyperv, **official_dlink**, **official_mikrotik**, system_info), agent command-polling in `backend/app/`

## Project Control System

The canonical project state lives in Git. Key documents:

| File | Purpose |
|------|---------|
| `MISSION_CONTROL_PROJECT_CONTROL.md` | Operating constitution — rules, architecture, current state, blockers, priorities |
| `ROADMAP.md` | Release roadmap with RC1-specific context |
| `PROJECT_MEMORY.md` | Long-term memory — decisions, environment context, plugin inventory, test targets |
| `AGENTS.md` | This file — AI agent instructions |

**GIT REPOSITORY = CANONICAL PROJECT SOURCE OF TRUTH.**

---

Mission Control is an IT operations dashboard / workspace. Stack:
- **Backend**: FastAPI (Python 3.12) + SQLAlchemy 2 + Alembic + Pydantic Settings, in `backend/`
- **Frontend**: React + TypeScript + Vite, in `frontend/`
- **Plugins/agents**: `backend/app/plugins/installed/` (git, docker, zabbix, veeam, unifi, hyperv, official_dlink, official_mikrotik, system_info), agent command-polling in `backend/app/`

## Working branch
- Current work lives on **`release/v3.0.0-rc1`**.
- Key goal: keep backend CI (ruff + pytest + frontend build) green on this branch.

## Local run (top-level from last session)
Backend tests only pass when the environment matches CI expectations:

```powershell
# outside repo: ssh billboe3@34.35.177.209 (key ~/.ssh/id_ed25519)
# server project : /opt/MissionControl  (the repo we push from)
# reference main clone: /tmp/mc-main
```

Test venv on server: `/tmp/testvenv/bin/python -m pytest`; ruff: `/tmp/venv/bin/ruff`.
Temp containers: `mc-test-postgres` (localhost:5432), `mc-test-redis` (localhost:6379).

Env required for a green backend test run (root `backend/`):
```bash
export TESTING=1
export MISSIONCONTROL_SECRET_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
export POSTGRES_DB=mission_control POSTGRES_USER=mission_control POSTGRES_PASSWORD=mission_control
export POSTGRES_HOST=localhost POSTGRES_PORT=5432
export REDIS_HOST=redis REDIS_PORT=6379          # "redis" MUST resolve -> 127.0.0.1
export BACKEND_CORS_ORIGINS=http://localhost
python -m pytest tests/ -q --tb=short
```

### CI gotchas (all backed by real CI failures — do not "fix" blindly)
1. **Secret key must be a real Fernet key** in CI/workflows. `alembic/env.py` loads Settings *before* conftest overrides, so a fake key like `test-key-for-ci-only-...` fails validation. Use `Fernet.generate_key().decode()`.
2. **`alembic upgrade head` is required before pytest** — plugin tables (`git`, `hyperv`, `docker`, `zabbix`) come from Alembic revisions (`merge_heads_rc1` etc.). CI step: `alembic upgrade head && python -m pytest ...`.
3. **`REDIS_HOST: redis` must resolve**. GitHub Actions services are only reachable on `localhost`; config default host is `redis`, and `test_redis_url_computed_correctly` asserts `redis://redis:6379/0`. CI adds `echo "127.0.0.1 redis" | sudo tee -a /etc/hosts` before tests.
4. **Python 3.12**: `asyncio.get_event_loop().run_until_complete(...)` raises `RuntimeError`. Use `asyncio.run(...)`.
5. **Conftest `mock_docker`** (backend/tests/conftest.py) patches health/remote and now `official_docker.cache.cache_manager.get_summary` so dashboard tests get `available=True`.

## Scoring-important decisions
- `tests/api/test_dashboard.py`, `test_setup_api.py`, `test_integration_management.py`, `test_zabbix_provider.py`, and `test_startup_config.py` assertions are **shared with `main`** — fix behavior in app code, not by loosening these tests. This was the discipline that drove fixes in `dashboard_service`, `routers/setup.py`, `integration_service`.
- Remote edit loop (server):
  1. edit local temp copy, 2. `scp <file> billboe3@34.35.177.209:/opt/MissionControl/backend/<path>`, 3. run checks via `ssh ... bash /tmp/script.sh`. Avoid `&&` inside PowerShell-quoted ssh commands (use a script file).

## Commit conventions
Conventional commits used in this repo: `fix(backend): …`, `style(backend): … (272->0)`, `chore: …`, `ci(backend): …`, `feat(agent): …`.
Commit/push from the **server** repo (`/opt/MissionControl`), never from the local OneDrive checkout (local has unrelated uncommitted WIP on git/hyper-V plugins).

## Current status (latest verified)
- Run `31415687763` on `release/v3.0.0-rc1`: **all green** — backend lint ✓, backend tests **1512 passed / 1 skipped**, frontend tsc+build ✓.
- Latest run after Veeam DB bridge (commit `5f0045b`): backend tests **1582 passed / 1 skipped**, ruff ✓ on changed files. Frontend untouched.
- Last commits: `5f0045b` (veeam DB bridge: real job/session/repo data via psql; session-expire fix in `AgentSshExecutor`; agent command poll 5-15s; removes dead `app/providers/veeam/provider_factory.py`), `ebb69f8` (dead provider_factory — now reverted by `5f0045b`), `9576d13` (veeam relay context init).
- Veeam dashboard for CORHQVEEMA is **live with real data** — agent bundle `v0.0.15`; `veeam_backup_servers.timeout=120` (was 30) so relay ops fit the request window. Endpoints verified: `/jobs` (66), `/jobs/stats` (66), `/jobs/stats/daily` (57 jobs/8 dates), `/sessions` (200), `/sessions/stats` (200), `/repositories` (10), `/overview`, `/test` (connected).