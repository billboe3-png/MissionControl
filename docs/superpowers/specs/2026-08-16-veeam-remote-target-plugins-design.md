# Veeam via Remote-Target Plugins (Both paths) — Design

Date: 2026-08-16
Status: Approved
Branch: `release/v3.0.0-rc1`

## Problem

1. Remote Target "Plugins to collect on this host" checkboxes are not saved
   (root cause fixed separately: `target_plugins` column never applied to prod
   because the Alembic migration branched off an ancestor creating a second
   head; model also used an invalid `mapped_column(description=...)` kwarg).
2. Veeam Jobs screen shows no data.

## Job 1 (done, deployed)

- Rebased migration `20260814094746` onto `f1a2b3c4d5e6` (single head), applied
  to prod.
- Fixed model kwarg (`comment=`), cleaned duplicated schema line, added
  `target_plugins` to heartbeat payload, agent `remote.py` filters collectors by
  `target_plugins`.
- Bundle rebuilt to `v0.0.5`. Full suite 1563 passed / 1 skipped.

## Job 2 — this spec

The Jobs screen (`/api/v1/plugins/veeam/jobs`) reads the first enabled
`veeam_backup_servers` row. No row exists (no profile configured, and remote
targets never linked), and the agent-side `remote_execute` path never routed
`veeam:*` ops to the plugin. Both issues block Veeam job data.

## Data flow (community / agent-SSH mode)

1. Remote target with `veeam` in `target_plugins` persists → heartbeat delivers
   `target_plugins` to the agent (fixed).
2. Backend auto-registers a `veeam_backup_servers` row:
   `agent_id` + `target_id` linked, `edition=community`, `enabled` mirrors the
   target.
3. Jobs routes → `_first_server` → provider → `AgentSshExecutor` dispatches
   `veeam:jobs` via the agent command queue.
4. Agent `remote_execute` detects `namespace:"veeam"` → routes to
   `VeeamPlugin.execute_command(op, params)` → returns jobs JSON as stdout →
   server `_json_payload` parses → Jobs screen shows data.

Enterprise REST profile path remains unchanged: a `veeam` IntegrationProfile
with `base_url` registers a REST server row; `_first_server` prefers enterprise
rows so adding REST creds later takes precedence.

## Changes

### Backend — `app/plugins/installed/official_veeam/bridge.py`
- `sync_target_to_server(db, target)`: when `target.enabled` and `target_plugins`
  contains `veeam`, upsert `VeeamBackupServer`:
  - `name = f"[{target.name}]"` (unique; avoids profile name collision)
  - `edition="community"`, `data_source="both"`, `enabled=target.enabled`
  - `agent_id=target.agent_id`, `target_id=target.id`
  - `legacy_ssh_host=target.hostname`, `legacy_ssh_port=target.port`,
    `legacy_ssh_username=target.username`,
    `legacy_ssh_password_encrypted=target.password_encrypted`
  - `rest_url=None`, `status="unknown"`
- `remove_target_server(db, target_id)`: disable the row when `veeam` is removed,
  the target is disabled, or the target is deleted.
- `link_profile_to_target(db, profile)`: in `sync_profile_to_server`, when a
  profile has no `rest_url` and `agent_id`/`target_id` are null, link to the
  first enabled remote target whose hostname matches `profile.ssh_host` and whose
  plugins include `veeam`.

### Backend — `app/routers/agent_remote_target.py`
- Call `sync_target_to_server` after create and after update (when plugins or
  enabled changed), `remove_target_server` on delete, and on the enabled toggle.

### Backend — `app/plugins/installed/official_veeam/routes.py`
- `_first_server`: order by `edition` descending (enterprise first), then `id`
  ascending, so REST rows win when present.

### Agent — `.agents/agent/agent.py`
- In `_execute_command` `remote_execute`: after parsing the JSON payload, if
  `payload.get("namespace") == "veeam"`, call
  `self.plugin_manager.execute_plugin_command("veeam", payload.get("op",""),
  payload.get("params",{}))` and return
  `{"success": ok, "stdout": json.dumps(result), "stderr": "", "exit_code": 0/1}`.

### Agent — `.agents/agent/plugins/veeam_plugin.py`
- Ensure `execute_command` handles `veeam:jobs`, `veeam:sessions`,
  `veeam:job_stats`, `veeam:session_stats`, `veeam:job_stats_daily`,
  `veeam:repositories`, `veeam:managed_servers`, `veeam:license`,
  `veeam:capacity_tier`, `veeam:restore_points`, `veeam:test`,
  `veeam:start_job`, `veeam:stop_job` returning the JSON shapes the server
  `_json_payload`/provider expect (e.g. `{"jobs": [...]}`).

### Bundle
- Rebuild to `v0.0.6` so the Windows agent picks up the routing + plugin ops.

## Testing

- Backend unit tests:
  - creating a target with `target_plugins="veeam"` via the API creates the
    registry row (`agent_id`/`target_id`/`edition=community`).
  - updating target to remove `veeam` disables the row.
  - deleting a target removes/disables the row.
  - `_first_server` prefers enterprise over community.
  - profile bridge links a community profile to a matching target.
- Full backend suite (must stay green).
- Live verify on the server: registry row appears for `CORHQVEEMA` once saved
  with Veeam checked; `veeam_backup_servers` populated; Jobs route returns a
  provider response (job data depends on agent→target connectivity).

## Risks

- The agent→target Veeam relay collection against a real Windows Veeam server
  can only be fully verified live via `CORHQROBERTB` (needs agent online +
  target reachable + collectors working). Server-side wiring is fully
  testable/verified without it.