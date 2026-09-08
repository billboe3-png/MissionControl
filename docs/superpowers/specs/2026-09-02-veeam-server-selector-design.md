# Design: Per-Server Veeam Dashboard Selection

Date: 2026-09-02
Status: Approved (2026-09-02)
Branch target: `release/v3.0.0-rc1`

## Problem

Every Veeam dashboard data route resolves its server via `_first_server(db)` —
the lowest-enabled `veeam_backup_servers` row. With two configured servers
(11 `[CORHQVEEMA]`, 12 `[BPFHBDC01]`) the routes always serve CORHQVEEMA and
BPFHBDC01 is invisible in the UI, even though its collection layer now returns
real data through the agent relay (jobs 12, sessions 200, repositories 2,
job_stats 16, session_stats 200, job_stats_daily 12 jobs / 7 dates).

## Goals

- Make BPFH (and any future server) selectable from the Veeam pages.
- Default behavior unchanged: no `server_id` → current `_first_server` result.
- Selection persists across pages and reloads (per-browser localStorage).

## Non-Goals

- No multi-server aggregation or merging (each page shows one server at a time).
- No changes to the widget/cache routes used by the shared dashboard
  (`/licenses`, `/summary`, `/repo-health`, `/jobs-by-status`, `/jobs-by-type`),
  nor to the config CRUD (`/servers/config*`).
- Disabled servers are not selectable.

## Backend (`backend/app/plugins/installed/official_veeam/routes.py`)

### Helper

```python
def _resolve_server(db: Session, server_id: int | None) -> VeeamBackupServer | None:
    if server_id is not None:
        server = db.query(VeeamBackupServer).filter(
            VeeamBackupServer.id == server_id,
            VeeamBackupServer.enabled.is_(True),
        ).first()
        if server is None:
            raise HTTPException(status_code=404, detail="Veeam server not found")
        return server
    return _first_server(db)
```

### Route changes

Add `server_id: int | None = Query(None, description="Veeam server config id")`
and replace `_first_server(db)` with `_resolve_server(db, server_id)` on these
routes:

- `GET /overview`
- `GET /health`
- `GET /test`
- `GET /jobs`
- `GET /jobs/stats`
- `GET /jobs/stats/daily`
- `GET /jobs/{job_id}`
- `GET /sessions`
- `GET /sessions/stats`
- `GET /repositories`
- `GET /restore-points`
- `GET /license`
- `GET /capacity-tier`
- `GET /servers` (managed servers of the selected backup server)

Snapshot caching in `_serve` already keys by `server.id`, so per-server
snapshots and the forced-`refresh` path work without further changes.

## Frontend

### Context: `frontend/src/contexts/VeeamServerContext.tsx`

- Holds `servers: VeeamServerConfig[]`, `selectedServerId: number | null`,
  `setSelectedServerId(id)`, `loading`.
- On mount, fetches `/api/v1/plugins/veeam/servers/config`.
- Defaults selection to the first enabled config, then to
  `localStorage["veeam.selectedServerId"]` when present and still valid.
- Writes to localStorage on change.
- Exposes `useVeeamServer()` hook. Provider mounted in `App.tsx` (alongside the
  other providers) so selection survives navigation.

### Component: `frontend/src/components/veeam/ServerSelector.tsx`

- A `<select>` listing `servers` (label = server name). Shows a loading option
  while configs load; hidden entirely if zero/one server (single-server installs
  get no UI churn).
- Dispatches `setSelectedServerId` on change.

### Service (`frontend/src/services/veeam.ts`)

- Add `VeeamServerConfig` interface matching `VeeamServerConfigResponse`
  (name, url, username, verify_ssl, timeout, enabled, ssh_host, ssh_port,
  ssh_username, data_source, db_type, column_case) plus `id`.
- Add `listConfigs(): Promise<VeeamServerConfig[]>` hitting
  `/servers/config`.
- Every data function gains an optional trailing `serverId?: number | null`
  parameter, appended as `?server_id=<id>` when provided:
  `getSummary`, `getHealth`, `testConnection`, `listJobs`, `getJob`,
  `startJob`, `stopJob`, `listSessions`, `listRepositories`, `listServers`,
  `listRestorePoints`, `getLicense`, `getCapacityTier`, `getSessionStats`,
  `getJobStats`, `getJobStatsDaily`.

### Pages

`OverviewPage`, `HealthPage`, `JobsPage`, `SessionsPage`, `RepositoriesPage`:

- Consume `useVeeamServer()`; render `<ServerSelector/>` beneath `PageHeader`.
- Pass `selectedServerId` into every `veeamApi.*` call.
- Add `selectedServerId` to the `useEffect` dependency so data reloads when the
  server changes.
- PageHeader subtitle reflects the active server name.

## Error Handling

- Unknown or disabled `server_id` → backend 404 → context falls back to the
  first enabled server (and clears the stale localStorage value).
- Disconnected server → existing per-endpoint `success:false` payloads;
  Overview already renders the "Veeam server not connected" banner.
- `/servers/config` fetch failure → context keeps an empty list; pages render
  without the dropdown (previous behavior).

## Testing

- Backend (pytest, `backend/tests/plugins/...`): `_resolve_server` returns the
  requested enabled server; returns `_first_server` when `server_id` is `None`;
  raises 404 for unknown/disabled id. One route-level test that
  `/jobs?server_id=12` reaches the provider for server 12.
- Frontend: `tsc` + `vite build` green.
- Live probe (backend container): `/overview?server_id=12`,
  `/jobs?server_id=12`, `/jobs/stats?server_id=12` return real BPFH data.
- UI check on the deployed site: dropdown present on the five pages; selecting
  `[BPFHBDC01]` shows its jobs/sessions/repos; refresh keeps selection.

## Risks / Notes

- `get_db` and route signatures already use `Query`; adding a query param is
  backward compatible.
- The shared dashboard widget services in `cache_manager` are untouched and
  continue to use the first server — out of scope.