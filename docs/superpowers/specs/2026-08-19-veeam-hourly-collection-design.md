# Veeam Hourly Collection + Snapshot Cache

Date: 2026-08-19
Status: Approved (design)
Branch: `release/v3.0.0-rc1`

## Problem

The Veeam dashboard pages (`/jobs`, `/sessions`, `/repositories`, `/overview`,
stats pages) hit the live agent relay on **every page load**. Each relay op takes
~20–26s (SSH → psql on the Veeam server); `/overview` takes ~100s. Data does not
change that often, so most of that latency is wasted work.

## Goal

- Collect Veeam datasets **every hour** in the background.
- Pages serve from the cached snapshot **instantly**.
- A manual **Refresh** button triggers a live collection on demand.
- Keep all existing response shapes byte-identical (scoring-important tests).

## Non-goals

- Caching `/test`, `/health`, `/servers`, `/restore-points` (out of scope;
  servers/restore-points currently return relay failures anyway).
- Changing the existing relational sync (jobs/repos/license → dashboard widgets).

## Scope additions (from live dashboard review)

Two live-dashboard defects are fixed as part of this work:

1. **Connection badge shows "Error" although the DB bridge works.** For
   community servers, `get_health` (`provider.py`) marks healthy only if
   `rest_available` **or** `powershell_available` is true. This server's agent
   reports `db_available` (the DB bridge that actually serves the data).
   Fix: `healthy = bool(rest_available or powershell_available or db_available)`.

2. **Storage Usage shows 0 B.** The agent's `_db_collect("repositories")` query
   selects only `id, name, description, type, host_id, path, is_unavailable,
   status` from `backuprepositories`. Capacity lives in `backuprepositorycontainer`
   (`totalspace`, `freespace` bigints), joinable via
   `"backuprepositorycontainer.repositories".repositoryid = backuprepositories.id`
   (verified live — all 10 repos return real totalspace/freespace).
   Fix: extend the collector SQL to LEFT JOIN the container and map
   `capacityBytes` / `usedSpaceBytes` / `freeSpaceBytes` into each repo dict
   (the fields `get_summary` already reads). Agent bundle rebuild required.

## Design

### 1. New cache table: `veeam_snapshots`

One row per `(server_id, dataset)`.

| column | type | notes |
|---|---|---|
| `id` | int PK | |
| `server_id` | FK `veeam_backup_servers.id` | CASCADE |
| `dataset` | str(50) | `summary`, `jobs`, `sessions`, `repositories`, `job_stats`, `session_stats`, `job_stats_daily`, `license`, `capacity_tier` |
| `payload` | JSON text | exact relay payload dict (what the route returns) |
| `collected_at` | datetime | last successful collection |

- Unique constraint on `(server_id, dataset)`.
- `job_stats_daily` dataset key **includes the `days` value** (e.g.
  `job_stats_daily:7`) so a 14-day request never serves the cached 7-day
  payload.
- SQLAlchemy model in `models.py` + Alembic migration.
- Store the **exact payload** the provider methods return — no reshaping, so
  routes can serve snapshots verbatim and response shapes stay identical.

### 2. Hourly background collector

New module `collector.py` in `backend/app/plugins/installed/official_veeam/`:

- `async def collect_dataset(db, provider, server_id, dataset, **params) -> dict`
  - runs the matching provider method (`get_summary`, `get_jobs`, `get_sessions`,
    `get_repositories`, `get_job_stats`, `get_session_stats`,
    `get_job_stats_daily`, `get_license`, `get_capacity_tier`)
  - upserts the snapshot row (create or update `payload` + `collected_at`)
  - returns the payload dict
- `async def collect_all(db, provider, server_id) -> dict[str, dict]`
  - runs all 9 datasets sequentially (≈2–3 min, background, no request blocking)

Plugin lifecycle (`__init__.py`):

- Change `VeeamPluginConfig.sync_interval_seconds` default **300 → 3600**.
- Repurpose the existing `_background_sync` loop: each cycle calls
  `collect_all` for each enabled server instead of the current partial sync.
  Keep the event-bus publishing and `_mark_server_error` behavior.
- The existing relational sync classes (`JobSync`, `RepositorySync`, ...) and the
  `VeeamApiClient._sync` wrappers stay in the file but are no longer the
  scheduler's driver (snapshots supersede them for the live routes). Do not
  delete them yet — they still back the widget cache via `cache_manager`.

### 3. Routes serve cache, `refresh=1` forces live

Update `routes.py` live-data routes:

- Add optional `refresh: bool = False` query param to:
  `/overview`, `/jobs`, `/jobs/stats`, `/jobs/stats/daily`, `/sessions`,
  `/sessions/stats`, `/repositories`, `/license`, `/capacity-tier`.
- Helper `_serve(db, provider, server, dataset, method, refresh, **params)`:
  1. If `refresh` → call `collect_dataset` (live relay), return payload.
  2. Else read snapshot row for `(server.id, dataset)`; if present → return
     `payload` verbatim.
  3. Else (no snapshot yet) → call `collect_dataset` once (live), return payload.
  4. If live collection fails and a previous snapshot exists → return the stale
     snapshot with its `error` field replaced by a staleness note
     (e.g. `"Data may be stale — last collected <ts>"`) and `success` kept as
     stored (the stored payload always has `success: True` on success).
- Snapshot rows store the full response dict **including** `success`, so stale
  fallback just returns the stored dict unchanged.
- `/overview` uses dataset `summary` (the whole `get_summary` payload, which is
  itself a 3-relay composition + health — collected as one snapshot).
- `/health`, `/test`, `/servers`, `/restore-points` unchanged.

### 4. Frontend Refresh buttons

Add a "Refresh" button to the Veeam pages that re-fetches with `?refresh=1` and
shows a loading spinner during the live collection:

- `frontend/src/services/veeam.ts`: add `refresh` param to the API methods.
- Pages: `OverviewPage`, `JobsPage`, `SessionsPage`, `RepositoriesPage` (+ stats
  tabs), `HealthPage` (no change), `ServersPage` (no change).

### 5. Error handling

- `collect_dataset` must not raise on relay failure — returns the provider's
  `{success: False, error: ...}` dict and records it as the snapshot only if a
  previous snapshot does not exist (so pages never show empty on first tick).
- On failure with an existing snapshot, the old snapshot is preserved and the
  route reports staleness via `error`.

### 6. Concurrency

- The plugin's sync task is a single `asyncio.Task`; collections are sequential
  per server, servers sequential. No new concurrency primitives needed.
- `?refresh=1` requests and the hourly task could race on the same snapshot row;
  the upsert is atomic (single INSERT ... ON CONFLICT DO UPDATE or delete+insert
  in one transaction). Acceptable for a 1-row JSON write.

## Testing

- `tests/test_veeam_routes.py` (new cases):
  - snapshot hit returns cached payload without calling provider
  - `refresh=1` calls provider and stores snapshot
  - no snapshot → falls back to provider
  - provider failure with existing snapshot → returns stale snapshot + error
  - `/jobs/stats/daily?days=14` reads `job_stats_daily:14`, distinct from a
    cached `job_stats_daily:7`
  - response shapes still pass the existing `CANNED` equality assertions
- `tests/test_veeam_collector.py` (new): `collect_dataset` create + update
  upsert, `collect_all` runs all datasets, failure does not raise.
- `tests/test_veeam_provider.py` (extend): community `get_health` returns
  `healthy: True` when `db_available` is set.
- `tests/test_veeam_agent_executor.py` (extend): repository collector payload
  includes `capacityBytes` / `usedSpaceBytes` / `freeSpaceBytes` from the
  container join.
- Full suite must stay green (currently 1582 passed / 1 skipped), ruff clean.

## Deployment notes

- Backend code is baked into the docker image → `docker compose -f
  docker-compose.prod.yml build backend && up -d backend` after changes.
- Alembic migration must run (`alembic upgrade head`) inside the container/CI.
- Agent code IS touched (repository capacity query) → rebuild agent bundle via
  `build_bundle.py`; the agent auto-pulls within ~60s.
- After deploy, trigger one manual `/overview?refresh=1` to warm snapshots; the
  hourly task keeps them fresh afterwards.