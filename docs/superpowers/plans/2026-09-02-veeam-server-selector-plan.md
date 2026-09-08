# Per-Server Veeam Dashboard Selection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an optional `server_id` query param to the Veeam dashboard data routes and a persistent server dropdown so BPFHBDC01 (and any future server) can be selected on the Veeam pages.

**Architecture:** Backend adds `_resolve_server(db, server_id)` and threads `server_id` through the 14 live routes (defaulting to `_first_server` when absent, so behavior is unchanged). Frontend adds a `VeeamServerContext` (config list + localStorage-persisted selection) and a `ServerSelector` dropdown rendered on Overview/Health/Jobs/Sessions/Repositories, with each `veeamApi.*` call appending `?server_id=`.

**Tech Stack:** FastAPI + SQLAlchemy (backend); React + TypeScript + Vite (frontend).

## Global Constraints
- Work lands on `release/v3.0.0-rc1` (commit on `develop` → cherry-pick pattern; `develop` may be ahead).
- Keep backend CI green: ruff (Python 3.12), pytest, frontend `tsc` + `vite build`.
- Tests run in backend container via `docker exec -e PYTHONPATH=/app -w /app missioncontrol-backend-1 sh -lc '...'`; remote in-place fixes via scp + script file (PowerShell mangles inline quoting).
- Do not touch cache routes (`/licenses`, `/summary`, `/repo-health`, `/jobs-by-status`, `/jobs-by-type`) or config CRUD (`/servers/config*`).
- `veeam_provider.py` is untracked in git at present — add with `git add` when committing.
- No emojis in code. No comments unless existing convention warrants.

---
## File Structure

**Backend (modify):**
- `backend/app/plugins/installed/official_veeam/routes.py` — add `_resolve_server`, thread `server_id`.

**Backend (test):**
- `backend/tests/api/test_veeam_routes_server_select.py` (new).

**Frontend (create):**
- `frontend/src/contexts/VeeamServerContext.tsx`
- `frontend/src/components/veeam/ServerSelector.tsx`

**Frontend (modify):**
- `frontend/src/App.tsx` — mount provider.
- `frontend/src/services/veeam.ts` — `VeeamServerConfig`, `listConfigs()`, `serverId` params.
- `frontend/src/pages/veeam/OverviewPage.tsx`
- `frontend/src/pages/veeam/HealthPage.tsx`
- `frontend/src/pages/veeam/JobsPage.tsx`
- `frontend/src/pages/veeam/SessionsPage.tsx`
- `frontend/src/pages/veeam/RepositoriesPage.tsx`

---
### Task 1: Backend `_resolve_server` helper + tests

**Files:**
- Modify: `backend/app/plugins/installed/official_veeam/routes.py` (add helper after `_first_server`, ~line 149)
- Test: `backend/tests/api/test_veeam_routes_server_select.py`

**Interfaces:**
- Produces: `def _resolve_server(db: Session, server_id: int | None) -> VeeamBackupServer | None` — returns the enabled server with matching id (raises `HTTPException(404)` if missing/disabled), else `_first_server(db)` when `server_id is None`.

- [ ] **Step 1: Write the failing test**

```python
"""Tests for _resolve_server and server_id route selection in the Veeam plugin."""
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.plugins.installed.official_veeam.routes import _resolve_server
from app.plugins.installed.official_veeam.models import VeeamBackupServer


def _ensure_server(db: Session) -> VeeamBackupServer:
    """Create (or return) an enabled VeeamBackupServer row for tests."""
    server = db.query(VeeamBackupServer).filter(VeeamBackupServer.enabled.is_(True)).first()
    if server is not None:
        return server
    server = VeeamBackupServer(
        name="test-veeam", url="", username="", password="",
        verify_ssl=True, timeout=30, enabled=True, data_source="ssh",
        db_type="postgresql", column_case="pascal",
    )
    db.add(server)
    db.commit()
    db.refresh(server)
    return server


def test_resolve_none_returns_first_enabled(db: Session) -> None:
    server = _ensure_server(db)
    found = _resolve_server(db, None)
    assert found is not None
    assert found.enabled is True


def test_resolve_explicit_returns_that_server(db: Session) -> None:
    server = _ensure_server(db)
    found = _resolve_server(db, server.id)
    assert found is not None
    assert found.id == server.id


def test_resolve_unknown_server_raises_404(db: Session) -> None:
    _ensure_server(db)
    with pytest.raises(HTTPException) as exc:
        _resolve_server(db, 999_999)
    assert exc.value.status_code == 404
```

> Requires a `db` fixture. Create one via the codebase's session fixture if none exists in the test module — use the shared `get_db`/`SessionLocal` pattern used by other plugin tests (e.g., `tests/api/test_veeam_provider.py`). If `_resolve_server` is tested through the HTTP layer instead, use FastAPI `TestClient` and assert 200/404 statuses — whichever matches existing route-test convention.

- [ ] **Step 2: Run test to verify it fails**

Run: `docker exec -e PYTHONPATH=/app -w /app missioncontrol-backend-1 sh -lc 'python -m pytest tests/api/test_veeam_routes_server_select.py -q --tb=short'`
Expected: FAIL — `ImportError: cannot import name '_resolve_server' from '...routes'`

- [ ] **Step 3: Implement `_resolve_server`**

Add immediately after the existing `_first_server` definition in `routes.py`:

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

- [ ] **Step 4: Run test to verify it passes**

Run: the command from Step 2.
Expected: PASS.

- [ ] **Step 5: Commit** (on server repo `/opt/MissionControl`, branch `develop`)

```bash
git add backend/app/plugins/installed/official_veeam/routes.py backend/tests/api/test_veeam_routes_server_select.py
git commit -m "feat(veeam): add _resolve_server for per-server route selection"
```
> Work on `develop`, cherry-pick to `release/v3.0.0-rc1` in Task 7. Do not push.

---
### Task 2: Thread `server_id` through the 14 live routes

**Files:**
- Modify: `backend/app/plugins/installed/official_veeam/routes.py` (routes ~lines 251–473)

**Interfaces:**
- Consumes: `_resolve_server(db, server_id)` from Task 1.
- Produces: each live data route accepts `server_id: int | None = Query(None, ...)` and passes it to `_resolve_server`.

- [ ] **Step 1: Add `server_id` query param + use `_resolve_server` on the 14 routes**

Affected route handlers (`kind` strings are used only for `_failed`):

| Route | handler | kind |
|---|---|---|
| `/overview` | `get_overview` | `overview` |
| `/health` | `get_health` | `health` |
| `/test` | `test_connection` | `test` |
| `/jobs` | `list_jobs` | `jobs` |
| `/jobs/stats` | `get_job_stats` | `job_stats` |
| `/jobs/stats/daily` | `get_job_stats_daily` | `job_stats_daily` |
| `/jobs/{job_id}` | `get_job_detail` | `job_detail` |
| `/sessions` | `list_sessions` | `sessions` |
| `/sessions/stats` | `get_session_stats` | `session_stats` |
| `/repositories` | `list_repositories` | `repositories` |
| `/restore-points` | `list_restore_points` | `restore_points` |
| `/license` | `get_license` | `license` |
| `/capacity-tier` | `get_capacity_tier` | `capacity_tier` |
| `/servers` | `list_managed_servers` | `servers` |

For each handler:
1. Add `server_id: int | None = Query(None, description="Veeam server config id"),` to the signature (before the `db: Session = Depends(get_db)` param).
2. Replace `server = _first_server(db)` with `server = _resolve_server(db, server_id)`.

Example (`list_jobs`):
```python
@router.get("/jobs")
async def list_jobs(
    refresh: bool = Query(False),
    server_id: int | None = Query(None, description="Veeam server config id"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    server = _resolve_server(db, server_id)
    if server is None:
        return _failed("jobs", _NO_SERVER)
    ...
```
> `get_job_detail` will now raise `HTTPException(404)` for unknown/disabled servers — the intended new behavior. Leave every other handler-body line untouched.

- [ ] **Step 2: Run backend tests**

Run: `docker exec -e PYTHONPATH=/app -w /app missioncontrol-backend-1 sh -lc 'python -m pytest tests/api/test_veeam_routes_server_select.py tests/api/test_dashboard.py -q --tb=short'`
Expected: PASS (dashboard suite unchanged; no regression).

- [ ] **Step 3: Lint changed file**

Run: `/tmp/venv/bin/ruff check backend/app/plugins/installed/official_veeam/routes.py`
Expected: no new errors.

- [ ] **Step 4: Commit**

```bash
cd /opt/MissionControl && git add backend/app/plugins/installed/official_veeam/routes.py
git commit -m "feat(veeam): accept server_id on live dashboard routes"
```

---
### Task 3: Live route validation probe

**Files:** server/temp only (not committed): `/tmp/probe_server12.py`

- [ ] **Step 1: Write + run probe for server 12 (`/tmp/probe_server12.py`)**

```python
"""Verify ?server_id=12 returns BPFH data on the live routes."""
import json
import urllib.request

BASE = "http://localhost:8000/api/v1/plugins/veeam"


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=180) as r:
        return json.loads(r.read().decode())


for path in ["/overview", "/jobs", "/jobs/stats", "/jobs/stats/daily",
             "/sessions/stats", "/repositories"]:
    d = get(path + "?server_id=12")
    items = d.get("jobs") or d.get("stats") or d.get("repositories") or []
    print(path, "success=", d.get("success"), "count=", len(items),
          "err=", d.get("error"))
```

Copy in and run:
```bash
docker cp /tmp/probe_server12.py missioncontrol-backend-1:/tmp/probe_server12.py
docker exec -e PYTHONPATH=/app -w /app missioncontrol-backend-1 sh -lc 'python /tmp/probe_server12.py'
```
Expected: `success True` — `/overview` total_jobs 12+, `/jobs` 12, `/jobs/stats` 16, `/jobs/stats/daily` 12, `/sessions/stats` 200, `/repositories` 2.

- [ ] **Step 2: sanity — default (no `server_id`) still returns server 11**

Append and re-run:
```python
for path in ["/overview", "/jobs"]:
    d = get(path)
    print(path, "(default) success=", d.get("success"), "name=", d.get("name"))
```
Expected: `/overview` name is the CORHQVEEMA server (server 11).

- [ ] **Step 3:** no commit (probe is temp). Proceed.

---
### Task 4: Frontend service — `VeeamServerConfig`, `listConfigs()`, `serverId` params

**Files:**
- Modify: `frontend/src/services/veeam.ts`

**Interfaces:**
- Consumes: backend `/servers/config` response shape.
- Produces:
  - `export interface VeeamServerConfig { id: number; name: string; url: string; username: string; verify_ssl: boolean; timeout: number; enabled: boolean; ssh_host: string; ssh_port: number; ssh_username: string; data_source: string; db_type: string; column_case: string; }`
  - `async listConfigs(): Promise<VeeamServerConfig[]>`
  - Each data method gains trailing `serverId?: number | null`.

- [ ] **Step 1: Add helper + interface + `listConfigs()`**

Helper at top of file (after `const API = ...`):
```ts
function withServer(
    url: string,
    serverId: number | null | undefined,
): string {
    if (serverId == null) return url;
    const sep = url.includes("?") ? "&" : "?";
    return `${url}${sep}server_id=${serverId}`;
}
```

Interface (place with the other interfaces):
```ts
export interface VeeamServerConfig {
    id: number;
    name: string;
    url: string;
    username: string;
    verify_ssl: boolean;
    timeout: number;
    enabled: boolean;
    ssh_host: string;
    ssh_port: number;
    ssh_username: string;
    data_source: string;
    db_type: string;
    column_case: string;
}
```

Add near the end of the `veeamApi` object (before the closing `}`):
```ts
    async listConfigs(): Promise<VeeamServerConfig[]> {
        const data = await apiClient<VeeamServerConfig[]>(`${API}/servers/config`);
        return data ?? [];
    },
```

- [ ] **Step 2: Add `serverId` param to all data methods**

Replace each method to accept `serverId?: number | null` and wrap its URL with `withServer`:

```ts
    async getSummary(serverId?: number | null): Promise<VeeamSummary> {
        return apiClient<VeeamSummary>(withServer(`${API}/overview`, serverId));
    },

    async getHealth(serverId?: number | null): Promise<VeeamHealth> {
        return apiClient<VeeamHealth>(withServer(`${API}/health`, serverId));
    },

    async testConnection(serverId?: number | null): Promise<VeeamConnectionTest> {
        return apiClient<VeeamConnectionTest>(withServer(`${API}/test`, serverId));
    },

    async listJobs(serverId?: number | null): Promise<{ jobs: VeeamJob[]; totalCount: number }> {
        const data = await apiClient<{ jobs: VeeamJob[]; count: number }>(withServer(`${API}/jobs`, serverId));
        return { jobs: data.jobs ?? [], totalCount: data.count ?? 0 };
    },

    async getJob(jobId: string, serverId?: number | null): Promise<VeeamJob> {
        const data = await apiClient<{ job: VeeamJob }>(withServer(`${API}/jobs/${jobId}`, serverId));
        return data.job;
    },

    async startJob(jobId: string, serverId?: number | null): Promise<VeeamJobAction> {
        return apiClient<VeeamJobAction>(withServer(`${API}/jobs/${jobId}/start`, serverId), { method: "POST" });
    },

    async stopJob(jobId: string, serverId?: number | null): Promise<VeeamJobAction> {
        return apiClient<VeeamJobAction>(withServer(`${API}/jobs/${jobId}/stop`, serverId), { method: "POST" });
    },

    async listSessions(serverId?: number | null): Promise<VeeamSession[]> {
        const data = await apiClient<{ sessions: VeeamSession[] }>(withServer(`${API}/sessions`, serverId));
        return data.sessions ?? [];
    },

    async listRepositories(serverId?: number | null): Promise<VeeamRepository[]> {
        const data = await apiClient<{ repositories: VeeamRepository[] }>(withServer(`${API}/repositories`, serverId));
        return data.repositories ?? [];
    },

    async listServers(serverId?: number | null): Promise<VeeamManagedServer[]> {
        const data = await apiClient<{ servers: VeeamManagedServer[] }>(withServer(`${API}/servers`, serverId));
        return data.servers ?? [];
    },

    async listRestorePoints(vmId?: string, serverId?: number | null): Promise<VeeamRestorePoint[]> {
        let url = vmId ? `${API}/restore-points?vm_id=${vmId}` : `${API}/restore-points`;
        url = withServer(url, serverId);
        const data = await apiClient<{ restore_points: VeeamRestorePoint[] }>(url);
        return data.restore_points ?? [];
    },

    async getLicense(serverId?: number | null): Promise<VeeamLicense> {
        return apiClient<VeeamLicense>(withServer(`${API}/license`, serverId));
    },

    async getCapacityTier(serverId?: number | null): Promise<VeeamCapacityTier> {
        return apiClient<VeeamCapacityTier>(withServer(`${API}/capacity-tier`, serverId));
    },

    async getSessionStats(serverId?: number | null): Promise<VeeamSessionStatsResponse> {
        return apiClient<VeeamSessionStatsResponse>(withServer(`${API}/sessions/stats`, serverId));
    },

    async getJobStats(serverId?: number | null): Promise<VeeamJobStatsResponse> {
        return apiClient<VeeamJobStatsResponse>(withServer(`${API}/jobs/stats`, serverId));
    },

    async getJobStatsDaily(days: number = 7, serverId?: number | null): Promise<VeeamJobStatsDailyResponse> {
        return apiClient<VeeamJobStatsDailyResponse>(withServer(`${API}/jobs/stats/daily?days=${days}`, serverId));
    },
```

- [ ] **Step 3: Typecheck**

Run: `npx tsc --noEmit` (from `frontend/`)
Expected: PASS (check `package.json` for the exact typecheck script if it differs).

- [ ] **Step 4: Commit**

```bash
cd /opt/MissionControl && git add frontend/src/services/veeam.ts && git commit -m "feat(veeam): add serverId to frontend veeam service"
```

---
### Task 5: Frontend `VeeamServerContext` + `ServerSelector`

**Files:**
- Create: `frontend/src/contexts/VeeamServerContext.tsx`
- Create: `frontend/src/components/veeam/ServerSelector.tsx`
- Modify: `frontend/src/App.tsx` (wrap with provider)

**Interfaces:**
- Consumes: `veeamApi.listConfigs()`, `VeeamServerConfig` from Task 4.
- Produces:
  - `useVeeamServer(): { servers: VeeamServerConfig[]; selectedServerId: number | null; setSelectedServerId: (id: number) => void; loading: boolean }`
  - `<ServerSelector />` (no props).

- [ ] **Step 1: Create `frontend/src/contexts/VeeamServerContext.tsx`**

```tsx
import {
    createContext,
    useCallback,
    useContext,
    useEffect,
    useMemo,
    useState,
} from "react";
import { veeamApi, VeeamServerConfig } from "../services/veeam";

const STORAGE_KEY = "veeam.selectedServerId";

interface VeeamServerContextValue {
    servers: VeeamServerConfig[];
    selectedServerId: number | null;
    setSelectedServerId: (id: number) => void;
    loading: boolean;
}

const VeeamServerContext = createContext<VeeamServerContextValue>({
    servers: [],
    selectedServerId: null,
    setSelectedServerId: () => {},
    loading: true,
});

export function VeeamServerProvider({ children }: { children: React.ReactNode }) {
    const [servers, setServers] = useState<VeeamServerConfig[]>([]);
    const [selectedServerId, setSelectedServerIdState] = useState<number | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let active = true;
        veeamApi
            .listConfigs()
            .then((configs) => {
                if (!active) return;
                const enabled = configs.filter((c) => c.enabled);
                setServers(enabled);
                const stored = Number(localStorage.getItem(STORAGE_KEY));
                const valid = enabled.some((c) => c.id === stored);
                const initial = valid ? stored : enabled[0]?.id ?? null;
                setSelectedServerIdState(initial);
            })
            .catch(() => {
                if (active) setServers([]);
            })
            .finally(() => {
                if (active) setLoading(false);
            });
        return () => {
            active = false;
        };
    }, []);

    const setSelectedServerId = useCallback((id: number) => {
        setSelectedServerIdState(id);
        localStorage.setItem(STORAGE_KEY, String(id));
    }, []);

    const value = useMemo(
        () => ({ servers, selectedServerId, setSelectedServerId, loading }),
        [servers, selectedServerId, setSelectedServerId, loading],
    );

    return <VeeamServerContext.Provider value={value}>{children}</VeeamServerContext.Provider>;
}

export function useVeeamServer(): VeeamServerContextValue {
    return useContext(VeeamServerContext);
}
```

- [ ] **Step 2: Create `frontend/src/components/veeam/ServerSelector.tsx`**

```tsx
import { useVeeamServer } from "../../contexts/VeeamServerContext";

export default function ServerSelector() {
    const { servers, selectedServerId, setSelectedServerId, loading } = useVeeamServer();

    if (loading) return <span className="veeam-server-selector">Loading servers…</span>;
    if (servers.length <= 1) return null;

    return (
        <div className="veeam-server-selector">
            <label htmlFor="veeam-server-select">Veeam server</label>
            <select
                id="veeam-server-select"
                value={selectedServerId ?? servers[0].id}
                onChange={(e) => setSelectedServerId(Number(e.target.value))}
            >
                {servers.map((s) => (
                    <option key={s.id} value={s.id}>
                        {s.name}
                    </option>
                ))}
            </select>
        </div>
    );
}
```

- [ ] **Step 3: Wrap with provider in `App.tsx`**

Add `import { VeeamServerProvider } from "./contexts/VeeamServerContext";`, then wrap the `Routes` (or the Veeam route group) with `<VeeamServerProvider>` so it sits above the 5 Veeam pages. Match the existing provider nesting style in `App.tsx`.

- [ ] **Step 4: Typecheck**

Run: `npx tsc --noEmit` (from `frontend/`)
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd /opt/MissionControl && git add frontend/src/contexts/VeeamServerContext.tsx frontend/src/components/veeam/ServerSelector.tsx frontend/src/App.tsx
git commit -m "feat(veeam): server selector context and dropdown component"
```

---
### Task 6: Wire `ServerSelector` into the 5 Veeam pages

**Files:**
- Modify: `frontend/src/pages/veeam/OverviewPage.tsx`
- Modify: `frontend/src/pages/veeam/HealthPage.tsx`
- Modify: `frontend/src/pages/veeam/JobsPage.tsx`
- Modify: `frontend/src/pages/veeam/SessionsPage.tsx`
- Modify: `frontend/src/pages/veeam/RepositoriesPage.tsx`

**Interfaces:**
- Consumes: `useVeeamServer()` and `<ServerSelector/>` from Task 5; service `serverId` params from Task 4.

- [ ] **Step 1: OverviewPage**

- Import `useVeeamServer` and `ServerSelector`.
- Add `const { servers, selectedServerId } = useVeeamServer();`.
- Update service calls: `getSummary(selectedServerId)`, `getHealth(selectedServerId)`, `listJobs(selectedServerId)`, `listRepositories(selectedServerId)`; add `selectedServerId` to the effect dependency array.
- Render `<ServerSelector />` just below `<PageHeader ... />`.
- Subtitle: use active server name:
  `subtitle={`${servers.find((s) => s.id === selectedServerId)?.name ?? summary.name ?? "Veeam Server"} v${summary.version ?? "?"}`}`

- [ ] **Step 2: HealthPage**

- Import `useVeeamServer`, `ServerSelector`.
- Add `const { selectedServerId } = useVeeamServer();`.
- `getHealth(selectedServerId)` + add `selectedServerId` to effect deps.
- Render `<ServerSelector />` under `PageHeader`.

- [ ] **Step 3: JobsPage**

- Import `useVeeamServer`, `ServerSelector`.
- Add `const { selectedServerId } = useVeeamServer();`.
- Pass `selectedServerId` to `listJobs`/`getJobStats`/`getJobStatsDaily`/`getJob`/`startJob`/`stopJob`; add `selectedServerId` to effect deps (and refresh-handler deps).
- Render `<ServerSelector />` under `PageHeader`.

- [ ] **Step 4: SessionsPage**

- Import `useVeeamServer`, `ServerSelector`.
- Add `const { selectedServerId } = useVeeamServer();`.
- `listSessions(selectedServerId)` and `getSessionStats(selectedServerId)` (keep the `.catch` fallback); add `selectedServerId` to effect deps.
- Render `<ServerSelector />` under `PageHeader`.

- [ ] **Step 5: RepositoriesPage**

- Import `useVeeamServer`, `ServerSelector`.
- Add `const { selectedServerId } = useVeeamServer();`.
- `listRepositories(selectedServerId)` + add `selectedServerId` to effect deps.
- Render `<ServerSelector />` under `PageHeader`.

- [ ] **Step 6: Typecheck + build**

Run: `cd /opt/MissionControl/frontend && npx tsc --noEmit && npm run build`
Expected: both PASS.

- [ ] **Step 7: Commit**

```bash
cd /opt/MissionControl && git add frontend/src/pages/veeam/
git commit -m "feat(veeam): add server dropdown to veeam dashboard pages"
```

---
### Task 7: Integration review — CI green, cherry-pick to release branch

**Files:** none (orchestration).

**Interfaces:** consumes all prior tasks.

- [ ] **Step 1: Run full backend suite**

Run (backend container, env per AGENTS.md):
```bash
export TESTING=1
export MISSIONCONTROL_SECRET_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
export POSTGRES_DB=mission_control POSTGRES_USER=mission_control POSTGRES_PASSWORD=mission_control
export POSTGRES_HOST=localhost POSTGRES_PORT=5432
export REDIS_HOST=redis REDIS_PORT=6379
alembic upgrade head
python -m pytest tests/ -q --tb=short
```
Expected: all pass (dashboard/management/startup tests shared with `main` stay green).

- [ ] **Step 2: ruff on changed files**

Run: `/tmp/venv/bin/ruff check backend/app/plugins/installed/official_veeam/routes.py backend/tests/api/test_veeam_routes_server_select.py`
Expected: clean.

- [ ] **Step 3: frontend build**

Run: `npm run build` (from `frontend/`)
Expected: PASS.

- [ ] **Step 4: Cherry-pick commits develop → release/v3.0.0-rc1**

```bash
cd /opt/MissionControl
git checkout release/v3.0.0-rc1
git cherry-pick <sha-Task1> <sha-Task2> <sha-Task4> <sha-Task5> <sha-Task6>
git checkout develop
```
Expected: clean cherry-pick. Resolve conflicts if any; the design-doc commit (`df01aae`) need not be carried.

- [ ] **Step 5: Final verification on release branch**

Re-run Steps 1–3 on `release/v3.0.0-rc1`. Expected: green.

- [ ] **Step 6: Close**

If cherry-pick needed fixups, add `fix(veeam): resolve cherry-pick conflicts for server selector`. Push only when the user asks.

---
## Self-Review Notes

- **Backend coverage:** `_resolve_server` (Task 1), `server_id` on all 14 routes (Task 2), 404 for unknown/disabled (Task 1), default unchanged (Task 3 Step 2), per-server snapshot via existing `server.id` cache key (no code change needed — noted).
- **Frontend coverage:** context + localStorage (Task 5), dropdown on all 5 pages (Task 6), service `serverId` params (Task 4), disabled servers filtered (Task 5), single-server hides dropdown (Task 5 Step 2).
- **Type consistency:** `_resolve_server(db, server_id) -> VeeamBackupServer | None` consistent (Tasks 1–2); `useVeeamServer()`/`ServerSelector` consistent (Tasks 5–6); `withServer` used in all Task 4 methods; `VeeamServerConfig.id: number` throughout (backend `id: int` → JSON number).
- **Placeholders:** none — all steps carry real code/paths/commands.
- **Out-of-scope respected:** cache routes and `/servers/config*` are not modified.