# Design: Wait-and-confirm Hyper-V VM actions

Date: 2026-08-18
Status: Approved

## Problem

When a user clicks Stop / Start / Restart / Pause / Resume on the Virtual
Machines page, the action command is dispatched to the agent, but the backend's
VM list only refreshes when the agent next posts inventory — every 300 seconds
by default. The page can therefore show a stale VM state for up to ~5 minutes
after an action. The user wants the UI to wait for Hyper-V to confirm the new
state and reflect it within seconds.

## Goals

- After any VM state-changing action, the agent executes the cmdlet, waits until
  Hyper-V reports the expected state, and reports the confirmed state back.
- The backend waits for that confirmation and returns it to the frontend, which
  shows an in-place "waiting" state on the action button.
- Inventory is refreshed immediately after the action so subsequent reads are
  accurate, not dependent on the 300s cycle.
- On timeout (VM does not reach the expected state in time), report an explicit
  error AND still refresh inventory so the page shows the real state.

## Current flow (unchanged parts)

- Frontend `doAction` calls `hypervApi.stopVm(...)` etc.; `LoadingButton`
  disables the button with a spinner while the request is in flight.
- Backend `LocalAgentHyperVProvider` / `AgentHyperVProvider` action methods build
  a PowerShell string via `_vm_command(vm_id, cmdlet)` and dispatch it through
  `_dispatch_on_agent` (in `provider_factory.py`).
- Local host (`host_id=-1001`) dispatches `command_type="execute"` with the raw
  PowerShell string. The agent runs it via `CommandExecutor._execute_shell`
  (raw `powershell -Command ...`).
- Remote target (`host_id=-1`) dispatches `command_type="remote_execute"` with a
  JSON payload `{"command": ..., "target_id": ...}`; the agent relays it over SSH
  to the target, where it runs as PowerShell.
- The agent posts results to `/api/v1/agents/{id}/command-result`, which updates
  the `agent_commands` row (status `completed`/`failed`, stdout, exit_code).
- Inventory is collected and posted by the agent's `_inventory_loop` every
  `inventory_interval` (default 300s).

## Design

### 1. Backend — composite wait-and-confirm command builder

Add a helper (in `agent_provider.py`, used by both providers) that builds a
single PowerShell command which:

1. Runs the cmdlet: e.g. `Stop-VM -Name 'X' [-Force]`.
2. Polls `(Get-VM -Name 'X').State` every ~1s until the expected state or a
   per-action deadline.
3. Writes a machine-readable line `MC_STATE=<state>` to stdout.

Expected states / timeouts:

| Action  | Cmdlet        | Expected state | Timeout |
|---------|---------------|----------------|---------|
| Stop    | Stop-VM       | Off            | 90s     |
| Start   | Start-VM      | Running        | 120s    |
| Restart | Restart-VM    | Running        | 120s    |
| Pause   | Suspend-VM    | Paused         | 30s     |
| Resume  | Resume-VM     | Running        | 60s     |

The composite command works identically when executed locally by the agent and
when relayed over SSH to a remote Windows target.

The VM name/GUID handling of the existing `_vm_command` is preserved (GUIDs use
`Get-VM -Id '<guid>' | <cmdlet>`, names are quoted).

### 2. Backend — dispatch + wait

`_dispatch_on_agent` in both providers changes from fire-and-forget to
dispatch-then-wait:

- Local host: dispatch with `command_type="vm_action"` (a new, unvalidated
  command type — no schema/migration change).
- Remote target: keep `command_type="remote_execute"`, but add
  `"refresh_inventory": true` to the relay payload.
- After dispatch, poll the `agent_commands` row (every ~2s) until status is
  `completed` or `failed`, with a backstop deadline (~100s, aligned to the
  dispatch `timeout`).
- Parse `MC_STATE=<state>` from the result stdout.
- Return `{"success": true, "command_id", "state": <confirmed>, "message"}` on
  success; on failure/timeout return the error plus the last-known state.

The action methods (`start_vm`, `stop_vm`, `restart_vm`, `pause_vm`, `resume_vm`)
on both providers use the composite builder and the new dispatch-wait, so their
return values now carry the confirmed state.

### 3. Agent bundle v0.0.8 — immediate inventory push

`agent.py`:

- Factor `_post_inventory_now()` from `_inventory_loop` (collect + post full
  inventory, including plugin inventory and remote_targets).
- In `_execute_command`, when the executed command has
  `command_type == "vm_action"`, call `_post_inventory_now()` after posting the
  command result.
- When the executed command is `remote_execute` whose payload contains
  `refresh_inventory: true`, trigger `remote_manager.collect_inventory()` in a
  background task and post the updated inventory once collected.

No change to the hyperv plugin is needed — the wait/confirm logic lives entirely
in the composite PowerShell command string.

### 4. Frontend

- Keep the existing 20s auto-refresh as a safety net.
- `doAction` already reloads VMs after the response; because the agent pushes
  inventory right before the backend returns, the reload shows the confirmed
  state.
- Add a short loading label to the action buttons ("Stopping…", "Starting…",
  "Restarting…", "Pausing…", "Resuming…") via the existing `LoadingButton`
  loading state.

### 5. Error / timeout behavior

If Hyper-V does not confirm within the per-action timeout, the command completes
with the actual state; the backend returns an error such as "timed out waiting
for Off — VM is <state>", and the agent still pushed inventory so the page shows
the real state. The button spinner stops and the error banner displays.

## Testing

- Unit tests (backend, `tests/test_hyperv.py`):
  - Composite builder emits the expected cmdlet, expected state, timeout, and
    force flag for each action.
  - Dispatch-wait returns the confirmed state when the `agent_commands` row
    reaches `completed`; returns an error on `failed`/timeout.
- Existing scoring-important tests are untouched.
- Full backend suite + ruff must stay green.
- Agent bundle: build v0.0.8, deploy to CORHQROBERTB, and run an end-to-end
  stop on a test VM confirming the returned state and immediate inventory
  refresh.

## Deployment

1. Rebuild backend container (`docker compose -f docker-compose.prod.yml up -d
   --build backend`).
2. Rebuild frontend image for the button labels.
3. Rebuild agent bundle v0.0.8 (`build_bundle.py`) and deploy to the agent
   (same mechanism as v0.0.7).
4. Live-verify: dispatch a Stop on a test VM and confirm the API returns the
   confirmed state and the VM list reflects it within seconds.