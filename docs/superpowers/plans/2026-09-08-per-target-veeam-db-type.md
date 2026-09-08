# Per-Target Veeam Database Type Selection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let an admin select the Veeam backing-database type (`postgresql`/`mssql`) and MSSQL column case (`pascal`/`snake`) when enabling the Veeam plugin on an agent's remote target, persisting it per target and syncing it into `veeam_backup_servers` so the agent relay uses the correct SQL dialect.

**Architecture:** The selection is stored on `agent_remote_targets` (new `db_type` + `column_case` columns), exposed through the existing `RemoteTarget` schemas/router, and mirrored into `veeam_backup_servers` by `sync_target_to_server` in `official_veeam/bridge.py`. The agent already honors the server-passed `db_type`/`column_case` and only binary-probes as a fallback — no agent change is needed. The frontend reveals the selector only when the Veeam plugin checkbox is ticked.

**Tech Stack:** Python 3.11 / FastAPI / SQLAlchemy 2 / Alembic / Pydantic v2; React + TypeScript (tsc + vite build).

## Global Constraints

- Conventional commit messages (repo style): `feat(backend):`, `feat(frontend):`, `test(backend):`, `docs:`.
- Commit/push from the **server** repo (`/opt/MissionControl`), never from the local OneDrive/C:\Projects checkout.
- `db_type` values restricted to `^(postgresql|mssql)$`; `column_case` restricted to `^(pascal|snake)$` — enforced via Pydantic `Field(pattern=...)` matching `VeeamServerConfigBase` in `official_veeam/routes.py`.
- Migration revision id must be unique; head to attach under is **`f1d543c4ff24`**.
- Default values: `db_type = "postgresql"`, `column_case = "pascal"` (both in migration `server_default` and ORM column `default`).
- Backfill existing targets from their linked `veeam_backup_servers` row (match on `target_id`); targets with no linked server keep defaults.
- Backend tests run with `Base.metadata.create_all` (sqlite in-memory) — the migration does NOT run in unit tests, so backfill correctness is verified on the server with `alembic upgrade head` + SQL check (Task 1 verify step). CI runs `alembic upgrade head` before pytest (postgres), so the migration must be syntactically valid.
- Backend test/lint commands on server: `docker compose exec -T backend alembic upgrade head`; `/tmp/testvenv/bin/python -m pytest backend/tests -q --tb=short` (or `/tmp/venv/bin/ruff`). Frontend: `npx tsc --noEmit` and `npm run build` in `frontend/`.
- DB session import is `from app.db.database import SessionLocal` (NOT `app.core.database`).

---

### Task 1: Migration + ORM model columns

**Files:**
- Create: `backend/alembic/versions/e1f2a3b4c5d7_add_veeam_db_type_to_remote_targets.py`
- Modify: `backend/app/models/db/agent_remote_target.py`
- Verify (server, manual): `docker compose exec -T backend alembic upgrade head` then SQL check of backfilled rows.

**Interfaces:**
- Consumes: existing `agent_remote_targets` table and `veeam_backup_servers` table (already has `db_type`, `column_case`, `target_id`). Exists on `release/v3.0.0-rc1` at `f1d543c4ff24` head.
- Produces: `AgentRemoteTarget.db_type: str`, `AgentRemoteTarget.column_case: str` (used by Task 2–4 and frontend tasks).

- [ ] **Step 1: Create the migration file**

Create `backend/alembic/versions/e1f2a3b4c5d7_add_veeam_db_type_to_remote_targets.py`:

```python
"""Add veeam db_type/column_case to agent_remote_targets

Revision ID: e1f2a3b4c5d7
Revises: f1d543c4ff24
Create Date: 2026-09-08
"""

import sqlalchemy as sa

from alembic import op

revision = "e1f2a3b4c5d7"
down_revision = "f1d543c4ff24"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "agent_remote_targets",
        sa.Column("db_type", sa.String(20), nullable=False, server_default="postgresql"),
    )
    op.add_column(
        "agent_remote_targets",
        sa.Column("column_case", sa.String(20), nullable=False, server_default="pascal"),
    )
    # Backfill from linked Veeam server rows (existing targets + their
    # auto-provisioned community server rows share target_id).
    op.execute(
        """
        UPDATE agent_remote_targets AS t
        SET db_type = v.db_type,
            column_case = v.column_case
        FROM veeam_backup_servers AS v
        WHERE v.target_id = t.id
        """
    )


def downgrade() -> None:
    op.drop_column("agent_remote_targets", "column_case")
    op.drop_column("agent_remote_targets", "db_type")
```

- [ ] **Step 2: Add the ORM columns**

In `backend/app/models/db/agent_remote_target.py`, after the `target_plugins` column (line ~104), add:

```python
    db_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="postgresql",
        comment="Veeam backing database: postgresql or mssql.",
    )

    column_case: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pascal",
        comment="Veeam SQL column case: pascal or snake (MSSQL).",
    )
```

- [ ] **Step 3: Run the migration on the server**

```bash
cd /opt/MissionControl
docker compose exec -T backend alembic upgrade head
docker compose exec -T backend alembic current
```

Expected: `alembic current` reports `e1f2a3b4c5d7 (head)`.

- [ ] **Step 4: Verify backfill**

Run a SQL check that `agent_remote_targets` rows linked to a `veeam_backup_servers` row copied the server's `db_type`/`column_case`. Expected production state: target_id 2 (CORHQVEEMA) → `postgresql`/`pascal`; target_id 12 (BPFHBDC01) → `mssql`/`snake`.

```bash
docker compose exec -T backend python - <<'PYEOF'
import sqlalchemy as sa
from app.db.database import SessionLocal
db = SessionLocal()
rows = db.execute(sa.text(
    "SELECT id, target_id, db_type, column_case FROM agent_remote_targets "
    "WHERE target_id IN (SELECT target_id FROM veeam_backup_servers WHERE target_id IS NOT NULL)"
)).fetchall()
for r in rows:
    print(r)
db.close()
PYEOF
```

Expected: two rows, matching each linked server's `db_type`/`column_case`.

- [ ] **Step 5: Quick import smoke test**

```bash
cd /opt/MissionControl
docker compose exec -T backend python -c "from app.models.db.agent_remote_target import AgentRemoteTarget; assert AgentRemoteTarget.__table__.c.db_type is not None; assert AgentRemoteTarget.__table__.c.column_case is not None; print('model OK')"
```

Expected: prints `model OK`.

- [ ] **Step 6: Commit**

```bash
cd /opt/MissionControl
git add backend/alembic/versions/e1f2a3b4c5d7_add_veeam_db_type_to_remote_targets.py backend/app/models/db/agent_remote_target.py
git commit -m "feat(backend): add veeam db_type/column_case to remote targets"
```

---

### Task 2: Schemas with validation

**Files:**
- Modify: `backend/app/schemas/agent_remote_target.py`
- Test: `backend/tests/test_agent_remote_target_plugins.py` (extend)

**Interfaces:**
- Consumes: `AgentRemoteTarget.db_type`/`.column_case` from Task 1.
- Produces: `RemoteTargetCreate.db_type: str = "postgresql"`, `column_case: str = "pascal"`; `RemoteTargetUpdate.db_type: str | None`, `column_case: str | None`; `RemoteTargetResponse.db_type: str`, `column_case: str` — consumed by router (Task 3), bridge (Task 4), frontend (Task 6).

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/test_agent_remote_target_plugins.py`:

```python
class TestRemoteTargetVeeamDbType:
    def test_create_defaults_to_postgresql(self, client):
        agent = _register_agent(client, "DbType Default Agent")
        target = _create_target(client, agent["agent_id"])
        assert target["db_type"] == "postgresql"
        assert target["column_case"] == "pascal"

    def test_create_with_mssql_round_trips(self, client):
        agent = _register_agent(client, "DbType Mssql Agent")
        target = _create_target(
            client, agent["agent_id"], db_type="mssql", column_case="snake"
        )
        assert target["db_type"] == "mssql"
        assert target["column_case"] == "snake"

        listed = client.get(f"/api/v1/agents/{agent['agent_id']}/remote-targets")
        assert listed.status_code == 200
        assert listed.json()["targets"][0]["db_type"] == "mssql"
        assert listed.json()["targets"][0]["column_case"] == "snake"

    def test_update_db_type_and_column_case(self, client):
        agent = _register_agent(client, "DbType Update Agent")
        target = _create_target(client, agent["agent_id"])

        resp = client.put(
            f"/api/v1/agents/{agent['agent_id']}/remote-targets/{target['id']}",
            json={"db_type": "mssql", "column_case": "snake"},
        )
        assert resp.status_code == 200
        assert resp.json()["db_type"] == "mssql"
        assert resp.json()["column_case"] == "snake"

    def test_invalid_db_type_rejected(self, client):
        agent = _register_agent(client, "DbType Bad Agent")
        resp = client.post(
            f"/api/v1/agents/{agent['agent_id']}/remote-targets",
            json={
                "name": "Bad DbType",
                "hostname": "192.168.10.49",
                "protocol": "ssh",
                "port": 22,
                "username": "kg\\administrator",
                "password": "secret",
                "db_type": "oracle",
            },
        )
        assert resp.status_code == 422

    def test_invalid_column_case_rejected(self, client):
        agent = _register_agent(client, "ColumnCase Bad Agent")
        resp = client.post(
            f"/api/v1/agents/{agent['agent_id']}/remote-targets",
            json={
                "name": "Bad ColumnCase",
                "hostname": "192.168.10.49",
                "protocol": "ssh",
                "port": 22,
                "username": "kg\\administrator",
                "password": "secret",
                "column_case": "camel",
            },
        )
        assert resp.status_code == 422
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd /opt/MissionControl/backend
MISSIONCONTROL_SECRET_KEY=abFXX2hk0HAUdJTgpf-pPCuJXrQi9B2ldfVSsM1GhVU= /tmp/testvenv/bin/python -m pytest tests/test_agent_remote_target_plugins.py -q --tb=short
```

Expected: the new `TestRemoteTargetVeeamDbType` tests fail (the schemas don't yet accept `db_type`/`column_case`, so `_create_target` payloads with those keys error 422 or the response omits them).

- [ ] **Step 3: Update the schemas**

In `backend/app/schemas/agent_remote_target.py`, add `Field` to the pydantic import and the three new fields:

```python
from pydantic import BaseModel, Field
```

In `RemoteTargetCreate`, after `target_plugins`:

```python
    db_type: str = Field("postgresql", pattern="^(postgresql|mssql)$")
    column_case: str = Field("pascal", pattern="^(pascal|snake)$")
```

In `RemoteTargetUpdate`, add:

```python
    db_type: str | None = Field(None, pattern="^(postgresql|mssql)$")
    column_case: str | None = Field(None, pattern="^(pascal|snake)$")
```

In `RemoteTargetResponse`, add:

```python
    db_type: str
    column_case: str
```

- [ ] **Step 4: Run the tests to verify they pass**

Run the same pytest command as Step 2 for `tests/test_agent_remote_target_plugins.py`. Expected: all tests in that file pass, including the new `TestRemoteTargetVeeamDbType` tests.

- [ ] **Step 5: Commit**

```bash
cd /opt/MissionControl
git add backend/app/schemas/agent_remote_target.py backend/tests/test_agent_remote_target_plugins.py
git commit -m "feat(backend): expose veeam db_type/column_case on remote target schemas"
```

---

### Task 3: Router passes db_type/column_case through

**Files:**
- Modify: `backend/app/routers/agent_remote_target.py`
- Test: covered by Task 2's API tests (create/update round-trips hit the router).

**Interfaces:**
- Consumes: `RemoteTargetCreate.db_type`/`.column_case` from Task 2.
- Produces: `AgentRemoteTarget` rows persisted with `db_type`/`column_case`; `sync_target_to_server(db, target)` continued to be called after create/update (already happens in router — no change to that call).

- [ ] **Step 1: Update the create kwargs**

In `create_remote_target` (around line 73), add `db_type` and `column_case` to the `kwargs` dict:

```python
        "target_plugins": payload.target_plugins,
        "db_type": payload.db_type,
        "column_case": payload.column_case,
```

The `update_remote_target` path needs no change: `payload.model_dump(exclude_unset=True)` already collects `db_type`/`column_case`, and `AgentRemoteTargetRepository.update` writes non-None values onto the row.

- [ ] **Step 2: Verify with the Task 2 API tests**

Run `test_agent_remote_target_plugins.py` again. Expected: already green after Task 2 — these tests exercise `create_remote_target` and `update_remote_target`, proving the router passes the fields into the DB. Confirm `test_create_with_mssql_round_trips` and `test_update_db_type_and_column_case` pass.

- [ ] **Step 3: Commit**

```bash
cd /opt/MissionControl
git add backend/app/routers/agent_remote_target.py
git commit -m "feat(backend): pass veeam db_type/column_case through remote target router"
```

---

### Task 4: Bridge syncs db_type/column_case into veeam_backup_servers

**Files:**
- Modify: `backend/app/plugins/installed/official_veeam/bridge.py`
- Test: `backend/tests/test_veeam_target_bridge.py` (extend)

**Interfaces:**
- Consumes: `AgentRemoteTarget.db_type`/`.column_case` (Tasks 1), `VeeamBackupServer.db_type`/`.column_case` (already exist on model).
- Produces: `sync_target_to_server(db, target)` upserts `veeam_backup_servers.db_type`/`.column_case` from the target — this is the link that makes the agent relay (via `VeeamProvider._relay`) run the right dialect.

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/test_veeam_target_bridge.py`:

```python
def test_sync_carries_db_type_and_column_case(db_session):
    _, target = _make_target(
        db_session, plugins="veeam", db_type="mssql", column_case="snake"
    )
    sync_target_to_server(db_session, target)
    row = db_session.query(VeeamBackupServer).filter(
        VeeamBackupServer.target_id == target.id
    ).one()
    assert row.db_type == "mssql"
    assert row.column_case == "snake"


def test_sync_updates_db_type_and_column_case_on_resync(db_session):
    _, target = _make_target(db_session, plugins="veeam")
    sync_target_to_server(db_session, target)
    target.db_type = "mssql"
    target.column_case = "snake"
    db_session.commit()
    sync_target_to_server(db_session, target)
    row = db_session.query(VeeamBackupServer).filter(
        VeeamBackupServer.target_id == target.id
    ).one()
    assert row.db_type == "mssql"
    assert row.column_case == "snake"


def test_sync_defaults_db_type_for_plain_target(db_session):
    _, target = _make_target(db_session, plugins="veeam")
    sync_target_to_server(db_session, target)
    row = db_session.query(VeeamBackupServer).filter(
        VeeamBackupServer.target_id == target.id
    ).one()
    assert row.db_type == "postgresql"
    assert row.column_case == "pascal"
```

Note: `_make_target` accepts `**overrides`, so `db_type="mssql"` flows into `AgentRemoteTargetRepository.create` as a column value.

- [ ] **Step 2: Run the tests to verify they fail**

Run the backend test for `test_veeam_target_bridge.py`. Expected: `test_sync_carries_db_type_and_column_case` fails with `AssertionError` (row.db_type is `postgresql` default, not `mssql`). The other two may pass already since the model defaults match.

- [ ] **Step 3: Update the bridge**

In `sync_target_to_server`, on the **create** branch, add `db_type` and `column_case` to the `VeeamBackupServer(...)` constructor:

```python
        row = VeeamBackupServer(
            name=name,
            edition="community",
            data_source="both",
            db_type=target.db_type,
            column_case=target.column_case,
            agent_id=target.agent_id,
            target_id=target.id,
            legacy_ssh_host=target.hostname,
            legacy_ssh_port=target.port,
            legacy_ssh_username=target.username,
            legacy_ssh_password_encrypted=target.password_encrypted,
            enabled=True,
            status="unknown",
        )
```

On the **update** (resync) branch, after `row.enabled = True` add:

```python
        row.db_type = target.db_type
        row.column_case = target.column_case
```

- [ ] **Step 4: Run the tests to verify they pass**

Run `test_veeam_target_bridge.py` again. Expected: all bridge tests pass, including the three new ones and the existing nine.

- [ ] **Step 5: Commit**

```bash
cd /opt/MissionControl
git add backend/app/plugins/installed/official_veeam/bridge.py backend/tests/test_veeam_target_bridge.py
git commit -m "feat(backend): sync veeam db_type/column_case from remote targets"
```

---

### Task 5: Frontend types

**Files:**
- Modify: `frontend/src/services/agentRemoteTarget.ts`
- Test: `npx tsc --noEmit` in `frontend/`.

**Interfaces:**
- Consumes: `RemoteTargetResponse` fields `db_type`/`column_case` from Task 2.
- Produces: `RemoteTarget.db_type: string`, `RemoteTarget.column_case: string`; `RemoteTargetCreate.db_type?: string`, `column_case?: string`; `RemoteTargetUpdate` same optional fields — consumed by `AgentRemoteTargetsTab.tsx` (Task 6).

- [ ] **Step 1: Update the interfaces**

In `frontend/src/services/agentRemoteTarget.ts`:

- `RemoteTarget`: add

```ts
    db_type: string;
    column_case: string;
```

- `RemoteTargetCreate`: add

```ts
    db_type?: string;
    column_case?: string;
```

- `RemoteTargetUpdate`: add

```ts
    db_type?: string;
    column_case?: string;
```

- [ ] **Step 2: Verify with tsc**

```bash
cd /opt/MissionControl/frontend
npx tsc --noEmit
```

Expected: exits 0.

- [ ] **Step 3: Commit**

```bash
cd /opt/MissionControl
git add frontend/src/services/agentRemoteTarget.ts
git commit -m "feat(frontend): add veeam db_type/column_case to remote target types"
```

---

### Task 6: Frontend form UI

**Files:**
- Modify: `frontend/src/pages/agents/AgentRemoteTargetsTab.tsx`
- Test: `npx tsc --noEmit` + `npm run build` in `frontend/`.

**Interfaces:**
- Consumes: `RemoteTargetCreate.db_type?`/`column_case?`, `RemoteTarget.db_type`/`.column_case` from Task 5.
- Produces: form state carrying `db_type`/`column_case`; a conditional "Veeam Database Type" + (for mssql) "Column Case" selector visible only when the Veeam checkbox is ticked; plugin cell rendering `veeam (mssql)`.

- [ ] **Step 1: Extend the form state and reset payloads**

In `AgentRemoteTargetsTab.tsx`:

1. Initial form state (line ~47): add to the object:

```ts
        db_type: "postgresql",
        column_case: "pascal",
```

2. After-save reset (in `handleSave`, line ~105): add the same two keys to the reset object.

3. "+ Add Target" reset (line ~175): add the same two keys.

4. `handleEdit` (line ~120): add

```ts
            db_type: target.db_type,
            column_case: target.column_case,
```

- [ ] **Step 2: Add the conditional DB-type selectors**

In the Plugins `form-row` block, after the plugin checkboxes `</div>` and before the `</div>` closing the row (currently after the `.form-hint`), insert:

```tsx
                        {selectedPlugins(form.target_plugins).includes("veeam") && (
                            <>
                                <div className="form-row">
                                    <label>Veeam Database Type</label>
                                    <select
                                        value={form.db_type}
                                        onChange={(e) =>
                                            setForm((f) => ({ ...f, db_type: e.target.value }))
                                        }
                                    >
                                        <option value="postgresql">PostgreSQL</option>
                                        <option value="mssql">Microsoft SQL</option>
                                    </select>
                                </div>
                                {form.db_type === "mssql" && (
                                    <div className="form-row">
                                        <label>MSSQL Column Case</label>
                                        <select
                                            value={form.column_case}
                                            onChange={(e) =>
                                                setForm((f) => ({ ...f, column_case: e.target.value }))
                                            }
                                        >
                                            <option value="pascal">PascalCase</option>
                                            <option value="snake">snake_case</option>
                                        </select>
                                    </div>
                                )}
                            </>
                        )}
```

- [ ] **Step 3: Show the DB type in the plugin cell**

Replace the plugins `<td>` body (currently `selectedPlugins(t.target_plugins).join(", ") || "—"`) with:

```tsx
                                            {selectedPlugins(t.target_plugins)
                                                .map((p) =>
                                                    p === "veeam"
                                                        ? `veeam (${t.db_type})`
                                                        : p
                                                )
                                                .join(", ") || "—"}
```

- [ ] **Step 4: Verify with tsc + build**

```bash
cd /opt/MissionControl/frontend
npx tsc --noEmit
npm run build
```

Expected: tsc exits 0; vite build completes.

- [ ] **Step 5: Commit**

```bash
cd /opt/MissionControl
git add frontend/src/pages/agents/AgentRemoteTargetsTab.tsx
git commit -m "feat(frontend): veeam db type selector on remote target form"
```

---

### Task 7: Full verification + push

**Files:**
- None new.

- [ ] **Step 1: Run the full backend test suite on the server**

```bash
cd /opt/MissionControl/backend
MISSIONCONTROL_SECRET_KEY=abFXX2hk0HAUdJTgpf-pPCuJXrQi9B2ldfVSsM1GhVU= /tmp/testvenv/bin/python -m pytest tests/ -q --tb=short
```

Expected: **no new failures**. Note there are exactly 3 KNOWN pre-existing failures at the current baseline `b2dcb1a`, unrelated to this work and not to be fixed here:
- `test_veeam_target_bridge.py::test_first_server_prefers_enterprise`
- `test_veeam_target_bridge.py::test_profile_linked_to_matching_target`
- `test_veeam_target_bridge.py::test_profile_with_non_matching_ssh_host_does_not_link`
These fail because `VeeamBackupServer` (models.py:36-38) now maps attributes `url`/`username`/`encrypted_password` to DB columns `rest_url`/`rest_username`/`rest_password_encrypted`, but the bridge (`sync_profile_to_server`) and the tests still pass `rest_url=` kwargs. They are a separate pre-existing cleanup item, out of scope for this feature plan.

- [ ] **Step 2: Run ruff on changed backend files**

```bash
cd /opt/MissionControl
/tmp/venv/bin/ruff check backend/app/models/db/agent_remote_target.py backend/app/schemas/agent_remote_target.py backend/app/routers/agent_remote_target.py backend/app/plugins/installed/official_veeam/bridge.py backend/tests/test_agent_remote_target_plugins.py backend/tests/test_veeam_target_bridge.py
```

Expected: no errors on these files. (Pre-existing errors in `official_dlink/relay.py` are out of scope and must not be touched.)

- [ ] **Step 3: Frontend tsc + build**

```bash
cd /opt/MissionControl/frontend
npx tsc --noEmit
npm run build
```

Expected: both pass.

- [ ] **Step 4: Confirm migration history is linear**

```bash
cd /opt/MissionControl
docker compose exec -T backend alembic heads
```

Expected: single head `e1f2a3b4c5d7 (head)`.

- [ ] **Step 5: Push to origin**

```bash
cd /opt/MissionControl
git push origin release/v3.0.0-rc1
```

Expected: pushed without force (linear branch); confirm GitHub shows the new commits.

- [ ] **Step 6: Update AGENTS.md current-status note**

Modify the "Current status" section of `AGENTS.md` to reflect the new feature commit range and the last full test run result. Commit with `docs: update AGENTS.md current status` and push.