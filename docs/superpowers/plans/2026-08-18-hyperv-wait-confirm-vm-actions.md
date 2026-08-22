# Hyper-V Wait-and-Confirm VM Actions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Hyper-V VM actions (Stop/Start/Restart/Pause/Resume) wait for Hyper-V to confirm the new VM state and reflect it in the UI within seconds instead of up to 5 minutes.

**Architecture:** The backend builds a composite PowerShell command that runs the cmdlet then polls `(Get-VM ...).State` until the expected state or a timeout, printing `MC_STATE=<state>`. The backend dispatches with a new `command_type="vm_action"` (local) or `remote_execute` with `refresh_inventory: true` (relay) and then polls the `agent_commands` row until the result is recorded. The agent bundle v0.0.8 pushes inventory immediately after a `vm_action` / flagged relay so the backend VM list is fresh. The frontend shows the in-place wait via the existing `LoadingButton` spinner plus a label.

**Tech Stack:** Python 3.12 / FastAPI / SQLAlchemy 2 (backend), PowerShell (agent command payloads), React + TypeScript + Vite (frontend), Python agent bundle.

## Global Constraints

- Authoritative repo is the server: `billboe3@34.35.177.209:/opt/MissionControl`, branch `release/v3.0.0-rc1`. Local OneDrive checkout is STALE — edit server copies (staged under `C:\Users\robert\AppData\Local\Temp\opencode\veeam-work\sdd-tools\deployed\`) and scp to the server; never edit/commit from the local checkout.
- Remote edit loop: edit staged copy → `scp` to server → run checks via a script file (`/tmp/<name>.sh`) over ssh. Avoid `&&`, `$()`, backticks, `!`, and complex quoting inside PowerShell-quoted ssh one-liners.
- Backend test env (top of every check script): `export TESTING=1`; `export MISSIONCONTROL_SECRET_KEY=$(/tmp/testvenv/bin/python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")`; `export POSTGRES_DB=mission_control POSTGRES_USER=mission_control POSTGRES_PASSWORD=mission_control POSTGRES_HOST=localhost POSTGRES_PORT=5432 REDIS_HOST=redis REDIS_PORT=6379`. pytest: `/tmp/testvenv/bin/python -m pytest` from `backend/`. ruff: `/tmp/venv/bin/ruff check app/ tests/`.
- `alembic upgrade head` already applied on the server; do NOT add migrations (no schema change in this plan).
- Scoring-important tests are never loosened: `tests/api/test_dashboard.py`, `tests/test_setup_api.py`, `tests/test_integration_management.py`, `tests/test_zabbix_provider.py`, `tests/test_startup_config.py`.
- Agent bundle source of truth: `.agents/reinstall-tmp/` (what `build_bundle.py` packages); mirror the same agent.py change into `deploy/corhqrobertb/agent/agent.py`. Bundle version bumps to v0.0.8.
- Never sweep WIP: `.agents/*`, `backend/alembic/*`, `frontend/dist/*`, `frontend/src` WIP files (`AgentRemoteTargetsTab.tsx`, `agentRemoteTarget.ts`).
- Frontend/backend containers are image copies (no source mounts); rebuild via `docker compose -f docker-compose.prod.yml up -d --build <svc>`.

---

### Task 1: Backend — composite wait-and-confirm command builder

**Files:**
- Modify: `backend/app/providers/hyperv/agent_provider.py` (add helpers next to `_vm_command`, ~line 113)
- Test: `backend/tests/test_hyperv.py` (append a class)

**Interfaces:**
- Consumes: `_GUID_RE` (already defined in `agent_provider.py`), `_vm_command`.
- Produces:
  - `_vm_ref(vm_id: str) -> str` — returns `(Get-VM -Id '<id>')` or `(Get-VM -Name '<name>')`.
  - `_vm_action_command(vm_id: str, cmdlet: str, expected_state: str, timeout_seconds: int, force: bool = False) -> str` — composite PowerShell string ending with `Write-Output "MC_STATE=$($state)"`.

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/test_hyperv.py`:

```python
class TestVmActionCommandBuilder:
    def test_stop_command_has_cmdlet_wait_loop_and_mc_state(self) -> None:
        from app.providers.hyperv.agent_provider import _vm_action_command

        cmd = _vm_action_command("Ubuntu server", "Stop-VM", "Off", 90, force=True)
        assert "Stop-VM -Name 'Ubuntu server' -Force" in cmd
        assert "-ne 'Off'" in cmd
        assert "AddSeconds(90)" in cmd
        assert 'MC_STATE=$($state)' in cmd

    def test_start_command_uses_guid_ref_and_running(self) -> None:
        from app.providers.hyperv.agent_provider import _vm_action_command

        cmd = _vm_action_command("f6d158f3-b277-45e3-b38d-c21b16ad4374", "Start-VM", "Running", 120)
        assert "Get-VM -Id 'f6d158f3-b277-45e3-b38d-c21b16ad4374' | Start-VM" in cmd
        assert "-ne 'Running'" in cmd
        assert "AddSeconds(120)" in cmd
```

- [ ] **Step 2: Run test to verify it fails**

Check script `/tmp/check_builder.sh`:
```bash
#!/bin/bash
export TESTING=1
export MISSIONCONTROL_SECRET_KEY=$(/tmp/testvenv/bin/python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
export POSTGRES_DB=mission_control POSTGRES_USER=mission_control POSTGRES_PASSWORD=mission_control
export POSTGRES_HOST=localhost POSTGRES_PORT=5432
export REDIS_HOST=redis REDIS_PORT=6379
cd /opt/MissionControl/backend
/tmp/testvenv/bin/python -m pytest tests/test_hyperv.py -k VmActionCommandBuilder -q --tb=short 2>&1 | tail -8
```
Expected: FAIL with `ImportError`/`AttributeError` (`_vm_action_command` undefined).

- [ ] **Step 3: Write minimal implementation**

In `backend/app/providers/hyperv/agent_provider.py`, after `_vm_command`:

```python
def _vm_ref(vm_id: str) -> str:
    if _GUID_RE.match(vm_id):
        return f"(Get-VM -Id '{vm_id}')"
    return f"(Get-VM -Name '{vm_id}')"


def _vm_action_command(
    vm_id: str,
    cmdlet: str,
    expected_state: str,
    timeout_seconds: int,
    force: bool = False,
) -> str:
    if _GUID_RE.match(vm_id):
        action = f"Get-VM -Id '{vm_id}' | {cmdlet}"
    else:
        action = f"{cmdlet} -Name '{vm_id}'"
    if force:
        action += " -Force"
    if cmdlet == "Suspend-VM":
        action += " -Confirm:$false"
    ref = _vm_ref(vm_id)
    return (
        f"{action};"
        f"$deadline=(Get-Date).AddSeconds({timeout_seconds});"
        "$state='Unknown';"
        f"try {{ $state = {ref}.State }} catch {{ }};"
        f"while(($state -ne '{expected_state}') -and ((Get-Date) -lt $deadline))"
        "{ Start-Sleep -Seconds 1;"
        f"try {{ $state = {ref}.State }} catch {{ }}; }};"
        'Write-Output "MC_STATE=$($state)"'
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `bash /tmp/check_builder.sh`
Expected: `2 passed`

- [ ] **Step 5: Commit**

```bash
cd /opt/MissionControl
git add backend/app/providers/hyperv/agent_provider.py backend/tests/test_hyperv.py
git commit -m "feat(hyperv): composite wait-and-confirm VM action command builder"
```

---

### Task 2: Backend — dispatch + wait for confirmed result

**Files:**
- Modify: `backend/app/providers/hyperv/provider_factory.py` (`_poll_command_result` helper + both `_dispatch_on_agent` closures + provider constructors)
- Modify: `backend/app/providers/hyperv/agent_provider.py` (add `wait_cmd` param + `_dispatch_and_wait` + update 5 action methods)
- Modify: `backend/app/providers/hyperv/local_agent_provider.py` (add `wait_cmd` param + `_dispatch_and_wait` + update 5 action methods)
- Test: `backend/tests/test_hyperv.py`

**Interfaces:**
- Consumes: `_vm_action_command` from Task 1.
- Produces:
  - `_poll_command_result(db, command_id: int, wait_s: int = 100) -> dict` — polls the `agent_commands` row; returns `{"success": bool, "state": str | None, "error_message": str | None, "stdout": str, "stderr": str}`; on deadline returns `{"success": False, "state": None, "error_message": "Timed out waiting for VM action result", "stdout": "", "stderr": ""}`.
  - Both providers accept `wait_cmd: Callable[[int], Awaitable[dict]] | None = None` and expose `async def _dispatch_and_wait(self, cmd: str) -> dict`.
  - Action methods return `{"success", "command_id", "state", "message"}` or `{"success": False, "command_id", "state", "error"}`.

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/test_hyperv.py`:

```python
class TestVmActionDispatchWait:
    @pytest.mark.asyncio
    async def test_stop_vm_returns_confirmed_state(self) -> None:
        from app.providers.hyperv.local_agent_provider import LocalAgentHyperVProvider

        async def fake_dispatch(cmd: str) -> dict:
            return {"success": True, "command_id": 42, "message": "dispatched"}

        async def fake_wait(cmd_id: int) -> dict:
            return {"success": True, "state": "Off", "error_message": None, "stdout": "MC_STATE=Off\n", "stderr": ""}

        inventory = {"vms": [{"name": "Jenkins", "state": 2, "computer_name": "H"}]}
        provider = LocalAgentHyperVProvider(
            inventory, hostname="H", dispatch_cmd=fake_dispatch, wait_cmd=fake_wait
        )
        result = await provider.stop_vm("Jenkins")
        assert result["success"] is True
        assert result["state"] == "Off"

    @pytest.mark.asyncio
    async def test_stop_vm_returns_timeout_error(self) -> None:
        from app.providers.hyperv.agent_provider import AgentHyperVProvider

        async def fake_dispatch(cmd: str) -> dict:
            return {"success": True, "command_id": 43, "message": "dispatched"}

        async def fake_wait(cmd_id: int) -> dict:
            return {"success": False, "state": "Running", "error_message": "timed out waiting for Off", "stdout": "MC_STATE=Running\n", "stderr": ""}

        inventory = {"vms": [{"name": "X", "state": 2}]}
        provider = AgentHyperVProvider(inventory, target_hostname="H", dispatch_cmd=fake_dispatch, wait_cmd=fake_wait)
        result = await provider.stop_vm("X", force=True)
        assert result["success"] is False
        assert "timed out" in result["error"]
```

- [ ] **Step 2: Run test to verify it fails**

Check script `/tmp/check_dispatch.sh` (same env as Task 1; `-k VmActionDispatchWait`).
Expected: FAIL (`wait_cmd`/`_dispatch_and_wait` undefined or constructors reject the kwarg).

- [ ] **Step 3: Implement `_poll_command_result` in `provider_factory.py`**

```python
import asyncio


async def _poll_command_result(db: Session, command_id: int, wait_s: int = 100) -> dict:
    from app.models.db.agent_command import AgentCommand

    deadline = time.monotonic() + wait_s
    while time.monotonic() < deadline:
        cmd = db.query(AgentCommand).filter(AgentCommand.id == command_id).first()
        if cmd is not None and cmd.status in ("completed", "failed"):
            stdout = cmd.stdout or ""
            state = None
            for line in stdout.splitlines():
                stripped = line.strip()
                if stripped.startswith("MC_STATE="):
                    state = stripped[len("MC_STATE="):]
            return {
                "success": bool(cmd.success),
                "state": state,
                "error_message": cmd.error_message,
                "stdout": stdout,
                "stderr": cmd.stderr or "",
            }
        await asyncio.sleep(2)
    return {
        "success": False,
        "state": None,
        "error_message": "Timed out waiting for VM action result",
        "stdout": "",
        "stderr": "",
    }
```
(`time` is already imported in `provider_factory.py`.)

- [ ] **Step 4: Wire `wait_cmd` into both provider constructors**

In `provider_factory.py`:
- Local closure: change `command_type="execute"` → `command_type="vm_action"`, keep `timeout=130`; after successful dispatch, pass the wait:
```python
        return LocalAgentHyperVProvider(
            hyperv,
            hostname=agent.name or full_inv.get("system", {}).get("hostname", ""),
            dispatch_cmd=_dispatch_on_agent,
            wait_cmd=lambda cid: _poll_command_result(db, cid, 100),
        )
```
- Remote closure: payload becomes
```python
        cmd_payload = json.dumps({
            "command": command_str,
            "target_id": target.id,
            "refresh_inventory": True,
        })
```
and the constructor gains `wait_cmd=lambda cid: _poll_command_result(db, cid, 100)`.

- [ ] **Step 5: Implement `wait_cmd` + `_dispatch_and_wait` in both providers**

In `agent_provider.py`, `class AgentHyperVProvider(HyperVProvider)` `__init__` add `wait_cmd: Callable[[int], Awaitable[dict]] | None = None` and store `self.wait_cmd = wait_cmd`. Add:

```python
    async def _dispatch_and_wait(self, cmd: str) -> dict:
        dispatch = await self._dispatch(cmd)
        command_id = dispatch.get("command_id")
        if not dispatch.get("success") or command_id is None or self.wait_cmd is None:
            return dispatch
        result = await self.wait_cmd(command_id)
        state = result.get("state")
        if result.get("success"):
            return {
                "success": True,
                "command_id": command_id,
                "state": state,
                "message": result.get("error_message") or (f"VM is {state}" if state else "Action completed"),
            }
        return {
            "success": False,
            "command_id": command_id,
            "state": state,
            "error": result.get("error_message") or "VM action failed",
        }
```

Update the 5 action methods (same pattern in both providers):
```python
    async def start_vm(self, vm_id: str) -> dict:
        return await self._dispatch_and_wait(_vm_action_command(vm_id, "Start-VM", "Running", 120))

    async def stop_vm(self, vm_id: str, force: bool = False) -> dict:
        return await self._dispatch_and_wait(_vm_action_command(vm_id, "Stop-VM", "Off", 90, force=force))

    async def restart_vm(self, vm_id: str) -> dict:
        return await self._dispatch_and_wait(_vm_action_command(vm_id, "Restart-VM", "Running", 120))

    async def pause_vm(self, vm_id: str) -> dict:
        return await self._dispatch_and_wait(_vm_action_command(vm_id, "Suspend-VM", "Paused", 30))

    async def resume_vm(self, vm_id: str) -> dict:
        return await self._dispatch_and_wait(_vm_action_command(vm_id, "Resume-VM", "Running", 60))
```
Do the identical `__init__`/`_dispatch_and_wait`/action-method updates in `local_agent_provider.py`. `Callable`/`Awaitable` already imported in both files (used by `dispatch_cmd`).

- [ ] **Step 6: Run tests to verify they pass**

Run: `bash /tmp/check_dispatch.sh`
Expected: `2 passed`

- [ ] **Step 7: Commit**

```bash
cd /opt/MissionControl
git add backend/app/providers/hyperv/agent_provider.py backend/app/providers/hyperv/local_agent_provider.py backend/app/providers/hyperv/provider_factory.py backend/tests/test_hyperv.py
git commit -m "feat(hyperv): dispatch VM actions with wait-and-confirm result"
```

---

### Task 3: Backend — full suite + ruff

**Files:** none (verification only)

- [ ] **Step 1: Run full suite + ruff**

`/tmp/check_full.sh`:
```bash
#!/bin/bash
export TESTING=1
export MISSIONCONTROL_SECRET_KEY=$(/tmp/testvenv/bin/python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
export POSTGRES_DB=mission_control POSTGRES_USER=mission_control POSTGRES_PASSWORD=mission_control
export POSTGRES_HOST=localhost POSTGRES_PORT=5432
export REDIS_HOST=redis REDIS_PORT=6379
cd /opt/MissionControl/backend
/tmp/testvenv/bin/python -m pytest tests/ -q --tb=short 2>&1 | tail -3
/tmp/venv/bin/ruff check app/ tests/ 2>&1 | tail -3
```
Expected: all tests pass (≥1580), ruff clean.

- [ ] **Step 2: Commit any lint fixes**

---

### Task 4: Agent bundle v0.0.8 — immediate inventory push

**Files:**
- Modify: `.agents/reinstall-tmp/agent.py` (`_execute_command`, `_inventory_loop`, new `_post_inventory_now`, new `_refresh_remote_inventory`)
- Modify: `deploy/corhqrobertb/agent/agent.py` (same edits)
- Modify: `.agents/build_bundle.py` (bump `VERSION` to `0.0.8`)

**Interfaces:**
- Consumes: `self.inventory_collector.collect()`, `self.plugin_manager.collect_all_inventory()`, `self.client.post(f"/api/v1/agents/{self._agent_id}/inventory", ...)`, `self.remote_manager` (all already exist).
- Produces: `_post_inventory_now()`, `_refresh_remote_inventory()`; `_execute_command` honors `command_type == "vm_action"` and `refresh_inventory: true` relay payloads.

- [ ] **Step 1: Edit `.agents/reinstall-tmp/agent.py`**

Extract the inventory-post body of `_inventory_loop` into:

```python
    async def _post_inventory_now(self) -> None:
        """Collect and post the full inventory immediately."""
        try:
            inventory = self.inventory_collector.collect()
            plugin_inventory = (
                await self.plugin_manager.collect_all_inventory()
            )
            if plugin_inventory:
                inventory["plugins"] = plugin_inventory

            if self._remote_inventory_cache:
                inventory["remote_targets"] = self._remote_inventory_cache

            await self.client.post(
                f"/api/v1/agents/{self._agent_id}/inventory",
                inventory,
            )
            logger.debug("Inventory reported to server (immediate)")
        except Exception as e:
            logger.warning("Immediate inventory report failed: %s", e)

    async def _refresh_remote_inventory(self) -> None:
        """Re-collect remote target inventory in the background and post it."""
        try:
            if self.remote_manager.target_count == 0:
                return
            self._remote_inventory_cache = (
                await self.remote_manager.collect_inventory()
            )
            await self._post_inventory_now()
        except Exception as e:
            logger.warning("Remote inventory refresh failed: %s", e)
```

In `_inventory_loop`, replace its body with `await self._post_inventory_now()` (keep the sleep/`_running` guard).

In `_execute_command`, in the dispatch branch:
```python
            if command_type == "remote_execute":
                target_id = cmd.get("target_id")
                command_text = cmd.get("command", "")
                refresh_inventory = False
                if target_id is None and command_text.startswith("{"):
                    try:
                        payload = json.loads(command_text)
                        target_id = payload.get("target_id")
                        command_text = payload.get("command", "")
                        refresh_inventory = bool(payload.get("refresh_inventory"))
                    except (json.JSONDecodeError, AttributeError):
                        pass
                if target_id is None:
                    result = {...unchanged...}
                else:
                    result = await self.remote_manager.execute_on_target(...)
            elif command_type == "vm_action":
                result = await self.command_executor.execute(
                    command=cmd.get("command", ""),
                    command_type="execute",
                    timeout=cmd.get("timeout", self.config.command_timeout),
                )
            else:
                result = await self.command_executor.execute(...)
```
After the command-result `report` is posted (inside the existing try, right after the `await self.client.post(... /command-result ...)` call), add:
```python
                if command_type == "vm_action":
                    await self._post_inventory_now()
                elif command_type == "remote_execute" and refresh_inventory:
                    asyncio.create_task(self._refresh_remote_inventory())
```
(`asyncio` is imported in agent.py.)

- [ ] **Step 2: Mirror the same edits into `deploy/corhqrobertb/agent/agent.py`**

Same `_post_inventory_now`, `_refresh_remote_inventory`, `_execute_command` changes.

- [ ] **Step 3: Bump bundle version**

In `.agents/build_bundle.py`, change the version constant to `"0.0.8"`.

- [ ] **Step 4: Build and verify the bundle**

Check script `/tmp/build_bundle.sh`:
```bash
#!/bin/bash
cd /opt/MissionControl/.agents
/tmp/venv/bin/python build_bundle.py 2>&1 | tail -6
python -c "import zipfile; z=zipfile.ZipFile('/opt/MissionControl/agent-bundle-live.zip'); names=z.namelist(); print('entries:', len(names)); print('agent.py:', 'agent.py' in names); import io; d=z.read('agent.py').decode(); print('vm_action:', 'vm_action' in d); print('post_inventory_now:', '_post_inventory_now' in d); print('refresh_inventory:', 'refresh_inventory' in d)"
```
Expected: bundle builds, contains the new code, version metadata shows 0.0.8.

- [ ] **Step 5: Commit**

```bash
cd /opt/MissionControl
git add .agents/reinstall-tmp/agent.py .agents/build_bundle.py deploy/corhqrobertb/agent/agent.py
git commit -m "feat(agent): immediate inventory push after VM actions (bundle 0.0.8)"
```

---

### Task 5: Frontend — action button labels

**Files:**
- Modify: `frontend/src/pages/hyperv/VirtualMachinesPage.tsx`

**Interfaces:** none (UI only)

- [ ] **Step 1: Edit the action buttons**

In `VirtualMachinesPage.tsx`, wrap each `LoadingButton`'s children so the label changes while the action is in flight, e.g.:
```tsx
<LoadingButton loading={actionId === vm.id} className="btn btn-primary btn-sm"
    onClick={() => doAction(vm.id, () => hypervApi.startVm(vm.id, selectedHostId))}>
    {actionId === vm.id ? "Starting…" : "Start"}
</LoadingButton>
```
Repeat for Stop → "Stopping…", Restart → "Restarting…", Pause → "Pausing…", Resume → "Resuming…". (`actionId` already holds the VM id of the action in flight.)

- [ ] **Step 2: Verify build on server**

Run `bash /tmp/build_frontend.sh` (runs `npm run build` = `tsc -b && vite build` inside a node env; on this server npm is only inside the Docker build, so instead rebuild the frontend image per Task 6 and confirm the image build succeeds).

---

### Task 6: Deploy and live-verify

**Files:** none (deployment)

- [ ] **Step 1: Rebuild backend container**

```bash
docker compose -f docker-compose.prod.yml up -d --build backend
```
Wait for healthy.

- [ ] **Step 2: Live-verify wait-and-confirm via API**

Script `/opt/MissionControl/backend/tests/live_verify_waitconfirm.py` (docker cp + exec with `-w /app -e PYTHONPATH=/app`): mint a token from `create_access_token`, POST `/api/v1/hyperv/vms/{id}/restart` for a running test VM (or stop on a disposable VM), and confirm the response contains `success: true` and the VM list reflects the new state. Expected: the action returns the confirmed state within the action timeout, and `/api/v1/hyperv/vms?host_id=-1001` shows the updated state within seconds.

- [ ] **Step 3: Deploy agent bundle v0.0.8**

Deploy `agent-bundle-live.zip` to the CORHQROBERTB agent using the same mechanism as v0.0.7 (bundle served via backend; agent pulls it on the next update check, or force via the deploy script under `.agents/deploy/`). Confirm the agent reports `agent_version` containing `0.0.8` in `/api/v1/agents`.

- [ ] **Step 4: Rebuild frontend image**

```bash
docker compose -f docker-compose.prod.yml up -d --build frontend
```
Confirm the new bundle is served and contains the "Stopping…" labels.

- [ ] **Step 5: End-to-end check**

From the VMs page, click Stop on a test VM and confirm: button shows "Stopping…", then flips to "stopped" within seconds (well under 1 minute), no dependence on the 300s inventory cycle.

---

### Task 7: Commit deployment artifacts

**Files:** none (git ops)

- [ ] **Step 1: Commit any remaining tracked changes**

```bash
cd /opt/MissionControl
git status --short
git add frontend/src/pages/hyperv/VirtualMachinesPage.tsx
git commit -m "feat(hyperv): wait-and-confirm action button labels"
```

- [ ] **Step 2: Verify clean scope**

`git status --short` shows only the known WIP files (`.agents/*`, `backend/alembic/*`, `frontend/dist/*`, `frontend/src` WIP files, `docs/superpowers/plans/*`, etc.). Remove any stray diagnostic scripts (e.g. `backend/tests/live_verify_waitconfirm.py`) if they are untracked and not intended for commit.

## Self-Review Notes

- Task 1 builds the composite command; Task 2 wires dispatch+wait; Task 3 gates the backend; Task 4 handles the agent push; Task 5 is UI labels; Task 6 deploys and verifies end-to-end; Task 7 closes out commits.
- The `HyperVVmActionResponse` Pydantic model ignores extra `state` fields, so the provider return shape is safe for the router.
- `command_type="vm_action"` passes through `dispatch_command` unchanged (no enum validation, no migration).
- The remote-target relay path keeps `remote_execute` and gains `refresh_inventory` in the payload; the composite PowerShell command runs on the remote Windows host over SSH.