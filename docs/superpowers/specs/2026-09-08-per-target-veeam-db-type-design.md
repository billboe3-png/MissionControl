# Per-Target Veeam Database Type Selection

## Problem

When a user ticks the **Veeam** plugin on a remote target in the Agent →
Remote Targets UI, there is no way to specify which backing database the target
uses. The server currently defaults the Veeam DB bridge to `postgresql` and
`pascal` column case unless the target's linked `veeam_backup_servers` row was
configured separately.

The relay chain *already* honors a per-server `db_type`/`column_case`:

1. `VeeamBackupServer.db_type` / `.column_case` are passed by the server-side
   provider into the agent relay (`veeam_provider.py::_relay`, which does
   `payload.setdefault("db_type", self.db_type)`).
2. The agent's `veeam:job_stats_daily` / `veeam:jobs` / `veeam:sessions`
   handlers use the passed `db_type` and only fall back to binary probing
   (`_db_detect`) when the value is `None`/empty/`auto`.

The missing piece is the *registration* path: `agent_remote_targets` has no
`db_type`/`column_case` columns, the Remote Targets form cannot set them, and
the bridge (`official_veeam/bridge.py::sync_target_to_server`) does not copy
them onto the `veeam_backup_servers` row it upserts.

## Goal

Let an admin explicitly select the Veeam backing-database type (and MSSQL
column case) when enabling the Veeam plugin **per remote target**, flowing it
through to the live `veeam_backup_servers` row so the relay runs the correct
query dialect without relying on binary auto-detection.

## Scope

Strictly per remote target. The Veeam Config modal (`VeeamConfigModal.tsx`) is
explicitly out of scope for this change (it already persists `db_type`/
`column_case` on `veeam_backup_servers` when used).

## Design

### 1. Migration

New Alembic migration on branch head `f1d543c4ff24` (hex-style revision id,
matching the recent `471bafbbdcd7`/`286fb97c4a3c` family).

Adds to `agent_remote_targets`:

- `db_type` — `sa.String(20)`, `nullable=False`, `server_default='postgresql'`
- `column_case` — `sa.String(20)`, `nullable=False`, `server_default='pascal'`

**Backfill**: for each existing row, copy `db_type`/`column_case` from its
linked `veeam_backup_servers` row (match on `target_id`). Rows with no linked
server keep the defaults. This gives CORHQVEEMA → `postgresql`/`pascal` and
BPFHBDC01 → `mssql`/`snake` without manual re-selection.

### 2. ORM model

`backend/app/models/db/agent_remote_target.py` — add `db_type` and
`column_case` mapped columns with the same defaults, mirroring the existing
column style (no CHECK constraints; validation lives in the schema).

### 3. Schemas

`backend/app/schemas/agent_remote_target.py`:

- `RemoteTargetCreate`: add `db_type: str = "postgresql"` and
  `column_case: str = "pascal"` with `pattern="^(postgresql|mssql)$"` and
  `pattern="^(pascal|snake)$"`.
- `RemoteTargetUpdate`: same two fields as `str | None`.
- `RemoteTargetResponse`: same two fields (from model attributes).

Mirrors the existing `VeeamServerConfig*` validation in
`official_veeam/routes.py`.

### 4. Router

`backend/app/routers/agent_remote_target.py`:

- `create_remote_target`: add `"db_type": payload.db_type` and
  `"column_case": payload.column_case` to the repository `kwargs`.
- `update_remote_target`: no change needed — `update_data = payload.model_dump(
  exclude_unset=True)` already picks up new fields via the repository's generic
  `update(**kwargs)`.

### 5. Bridge

`backend/app/plugins/installed/official_veeam/bridge.py::sync_target_to_server`:

- On create: pass `db_type=target.db_type`, `column_case=target.column_case`
  into the `VeeamBackupServer(...)` constructor.
- On update: set `row.db_type = target.db_type`, `row.column_case =
  target.column_case`.

### 6. Frontend

`frontend/src/services/agentRemoteTarget.ts` — add `db_type`/`column_case` to
`RemoteTarget`, `RemoteTargetCreate`, `RemoteTargetUpdate`.

`frontend/src/pages/agents/AgentRemoteTargetsTab.tsx`:

- Add `db_type: "postgresql"` and `column_case: "pascal"` to the initial form
  state and to the reset payloads after save/cancel.
- In the Plugins field, when the Veeam checkbox is checked, render two inline
  selects:
  - **Database Type**: PostgreSQL / Microsoft SQL (values `postgresql`/`mssql`)
  - **Column Case** (only when DB type is `mssql`): PascalCase / snake_case
- `handleEdit`: initialize from `target.db_type` / `target.column_case`.
- Table row: append the DB type to the Plugins cell for veeam targets, e.g.
  `veeam (mssql)`.

### 7. Agent

No change. The agent already honors the server-passed `db_type` and `column_case`
and probes only as a fallback.

## Data Flow

```
Remote Targets form (Veeam ticked + DB type selected)
  → agent_remote_targets.db_type / column_case
  → official_veeam/bridge.py::sync_target_to_server
  → veeam_backup_servers.db_type / column_case
  → provider._relay (payload.setdefault("db_type", self.db_type))
  → agent relay handler (uses db_type; probes only if auto)
```

## Error Handling

- Schema regex patterns reject invalid `db_type`/`column_case` values at the
  API boundary (400 response, matching existing Veeam config behavior).
- Bridge copies values verbatim; regex-validated inputs cannot reach the DB
  with unexpected values.

## Testing

- **Schema validation**: invalid `db_type`/`column_case` values are rejected by
  `RemoteTargetCreate`/`RemoteTargetUpdate`.
- **Bridge propagation**: creating/updating a remote target with
  `target_plugins` containing `veeam` writes `db_type`/`column_case` into the
  linked `VeeamBackupServer` row; the row is disabled when the target is
  disabled or has Veeam unchecked.
- **Migration**: backfill copies `db_type`/`column_case` from linked server
  rows into existing targets.
- Existing tests in `backend/tests/test_veeam_routes.py` and the veeam plugin
  test suite remain green.

## Files

- `backend/alembic/versions/<new-hex-revision>_add_veeam_db_type_to_remote_targets.py` (new; revision id assigned at implementation time)
- `backend/app/models/db/agent_remote_target.py`
- `backend/app/schemas/agent_remote_target.py`
- `backend/app/routers/agent_remote_target.py`
- `backend/app/plugins/installed/official_veeam/bridge.py`
- `frontend/src/services/agentRemoteTarget.ts`
- `frontend/src/pages/agents/AgentRemoteTargetsTab.tsx`
- `backend/tests/test_veeam_routes.py` (extend)