# Veeam Remote-Target Plugins (Both paths) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Veeam Jobs screen show data by auto-registering `veeam_backup_servers` rows from remote targets with the `veeam` plugin, and wiring the agent to route `veeam:*` commands to its Veeam plugin.

**Architecture:** Server-side bridge syncs remote targets (with `veeam` in `target_plugins`) into the plugin's `veeam_backup_servers` registry (community/agent mode, linking `agent_id`+`target_id`). The provider's `AgentSshExecutor` dispatches `veeam:*` ops through the agent command queue; the agent routes the `veeam` namespace to `VeeamPlugin.execute_command`, which runs collectors via the SSH relay. Enterprise REST profile path stays, and `_first_server` prefers enterprise rows.

**Tech Stack:** Python 3.12 / FastAPI / SQLAlchemy 2, Alembic, pytest (backend); Python agent (`.agents/agent`) shipped via `build_bundle.py`.

## Global Constraints

- Work happens on server repo `/opt/MissionControl` (never local OneDrive). Edit in staging dir, scp to server, verify via `/tmp/*.sh` scripts.
- Backend tests must stay green: run `TESTING=1` env + `alembic upgrade head` then `/tmp/testvenv/bin/python -m pytest tests/ -q --tb=short`.
- Ruff: `/tmp/venv/bin/ruff check <files>`.
- Do not loosen shared tests (`test_dashboard.py`, `test_setup_api.py`, `test_integration_management.py`, `test_zabbix_provider.py`, `test_startup_config.py`).
- Bundle version increments each rebuild: v0.0.5 is current; next is v0.0.6.
- Remote-loop: use script files for multi-line ssh; avoid `&&` inside PowerShell-quoted ssh.

---

### Task 1: Backend — target↔server sync in `bridge.py`

**Files:**
- Modify: `backend/app/plugins/installed/official_veeam/bridge.py`
- Test: `backend/tests/test_veeam_target_bridge.py` (new)

**Interfaces:**
- Consumes: `AgentRemoteTarget` ORM (`agent_remote_target.py`), `VeeamBackupServer` (`official_veeam/models.py`).
- Produces:
  - `def sync_target_to_server(db: Session, target) -> None`
  - `def remove_target_server(db: Session, target_id: int) -> None`

- [ ] **Step 1: Write the failing tests**

```python
# backend/tests/test_veeam_target_bridge.py
import pytest
from app.plugins.installed.official_veeam.bridge import (
    remove_target_server,
    sync_target_to_server,
)
from app.plugins.installed.official_veeam.models import VeeamBackupServer
from app.repositories.agent_repository import AgentRepository
from app.repositories.agent_remote_target_repository import AgentRemoteTargetRepository


def _make_target(db, name="Veeam Host", plugins="veeam,hyperv", enabled=True):
    agent = AgentRepository.create(
        db, name=f"{name} agent", hostname=f"{name.lower().replace(' ', '.')}.local",
        api_key="mc_agent_vbridge1234567890", status="online",
    )
    target = AgentRemoteTargetRepository.create(
        db, agent_id=agent.id, name=name, hostname="192.168.10.49",
        protocol="ssh", port=22, username="kg\\administrator",
        password_encrypted="enc", enabled=enabled, target_plugins=plugins,
    )
    return agent, target


def test_sync_creates_server_row(db_session):
    _, target = _make_target(db_session)
    sync_target_to_server(db_session, target)
    row = db_session.query(VeeamBackupServer).filter(
        VeeamBackupServer.target_id == target.id
    ).one()
    assert row.edition == "community"
    assert row.agent_id == target.agent_id
    assert row.target_id == target.id
    assert row.enabled is True
    assert row.name == "[Veeam Host]"


def test_sync_removes_row_when_veeam_unchecked(db_session):
    _, target = _make_target(db_session)
    sync_target_to_server(db_session, target)
    target.target_plugins = "hyperv"
    db_session.commit()
    sync_target_to_server(db_session, target)
    row = db_session.query(VeeamBackupServer).filter(
        VeeamBackupServer.target_id == target.id
    ).one()
    assert row.enabled is False


def test_remove_target_server_disables_row(db_session):
    _, target = _make_target(db_session)
    sync_target_to_server(db_session, target)
    remove_target_server(db_session, target.id)
    row = db_session.query(VeeamBackupServer).filter(
        VeeamBackupServer.target_id == target.id
    ).one()
    assert row.enabled is False


def test_sync_updates_creds_on_existing_row(db_session):
    _, target = _make_target(db_session)
    sync_target_to_server(db_session, target)
    target.hostname = "10.0.0.9"
    db_session.commit()
    sync_target_to_server(db_session, target)
    row = db_session.query(VeeamBackupServer).filter(
        VeeamBackupServer.target_id == target.id
    ).one()
    assert row.legacy_ssh_host == "10.0.0.9"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `bash /tmp/check_task1.sh` (env exports + `pytest tests/test_veeam_target_bridge.py -q --tb=short`)
Expected: FAIL — `ImportError: cannot import name 'sync_target_to_server'`.

- [ ] **Step 3: Implement the sync functions in `bridge.py`**

```python
def sync_target_to_server(db: Session, target) -> None:
    """Upsert a community veeam_backup_servers row from a remote target.

    Enabled when the target is enabled and its target_plugins include "veeam".
    """
    from app.plugins.installed.official_veeam.models import VeeamBackupServer

    raw = target.target_plugins or ""
    plugins = {p.strip() for p in raw.split(",") if p.strip()}
    row = db.execute(
        select(VeeamBackupServer).where(VeeamBackupServer.target_id == target.id)
    ).scalar_one_or_none()

    if not (target.enabled and "veeam" in plugins):
        if row is not None:
            row.enabled = False
        db.commit()
        return

    if row is None:
        name = f"[{target.name}]"
        clash = db.execute(
            select(VeeamBackupServer).where(VeeamBackupServer.name == name)
        ).scalar_one_or_none()
        if clash is not None and clash.target_id != target.id:
            name = f"[{target.name}] #{target.id}"
        row = VeeamBackupServer(
            name=name,
            edition="community",
            data_source="both",
            agent_id=target.agent_id,
            target_id=target.id,
            legacy_ssh_host=target.hostname,
            legacy_ssh_port=target.port,
            legacy_ssh_username=target.username,
            legacy_ssh_password_encrypted=target.password_encrypted,
            enabled=True,
            status="unknown",
        )
        db.add(row)
    else:
        row.agent_id = target.agent_id
        row.target_id = target.id
        row.legacy_ssh_host = target.hostname
        row.legacy_ssh_port = target.port
        row.legacy_ssh_username = target.username
        row.legacy_ssh_password_encrypted = target.password_encrypted
        row.enabled = True
    db.commit()


def remove_target_server(db: Session, target_id: int) -> None:
    """Disable the veeam_backup_servers row linked to a deleted remote target."""
    from app.plugins.installed.official_veeam.models import VeeamBackupServer

    row = db.execute(
        select(VeeamBackupServer).where(VeeamBackupServer.target_id == target_id)
    ).scalar_one_or_none()
    if row is not None:
        row.enabled = False
        db.commit()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `bash /tmp/check_task1.sh`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
cd /opt/MissionControl
git add backend/app/plugins/installed/official_veeam/bridge.py backend/tests/test_veeam_target_bridge.py
git commit -m "feat(veeam): sync remote targets to veeam_backup_servers registry"
```

---

### Task 2: Backend — hook sync into remote-target router

**Files:**
- Modify: `backend/app/routers/agent_remote_target.py`
- Test: `backend/tests/test_agent_remote_target_plugins.py` (extend)

**Interfaces:**
- Consumes: `sync_target_to_server(db, target)`, `remove_target_server(db, target_id)` from Task 1.
- Produces: registry row lifecycle driven by the CRUD endpoints.

- [ ] **Step 1: Write the failing tests (extend existing plugins test file)**

```python
def test_create_with_veeam_registers_server(client, db_session):
    from app.plugins.installed.official_veeam.models import VeeamBackupServer

    agent = _register_agent(client, "Registry Agent")
    target = _create_target(client, agent["agent_id"], target_plugins="veeam")
    row = db_session.query(VeeamBackupServer).filter(
        VeeamBackupServer.target_id == target["id"]
    ).one()
    assert row.enabled is True
    assert row.agent_id == agent["agent_id"]


def test_update_removing_veeam_disables_server(client, db_session):
    from app.plugins.installed.official_veeam.models import VeeamBackupServer

    agent = _register_agent(client, "Registry Update Agent")
    target = _create_target(client, agent["agent_id"], target_plugins="veeam")
    resp = client.put(
        f"/api/v1/agents/{agent['agent_id']}/remote-targets/{target['id']}",
        json={"target_plugins": "hyperv"},
    )
    assert resp.status_code == 200
    row = db_session.query(VeeamBackupServer).filter(
        VeeamBackupServer.target_id == target["id"]
    ).one()
    assert row.enabled is False


def test_delete_target_disables_server(client, db_session):
    from app.plugins.installed.official_veeam.models import VeeamBackupServer

    agent = _register_agent(client, "Registry Delete Agent")
    target = _create_target(client, agent["agent_id"], target_plugins="veeam")
    resp = client.delete(
        f"/api/v1/agents/{agent['agent_id']}/remote-targets/{target['id']}"
    )
    assert resp.status_code == 204
    row = db_session.query(VeeamBackupServer).filter(
        VeeamBackupServer.target_id == target["id"]
    ).one()
    assert row.enabled is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `bash /tmp/check_task2.sh`
Expected: FAIL — `sqlalchemy.exc.ProgrammingError: no such table: veeam_backup_servers` (or missing rows). NOTE: `veeam_backup_servers` table must exist in the test sqlite DB — it is created from `Base.metadata` only if `official_veeam/models.py` is imported before `create_all`. Ensure conftest imports it or tests import the model first (test file already imports it).

- [ ] **Step 3: Implement router hooks**

In `create_remote_target`, after `target = AgentRemoteTargetRepository.create(...)` and before return:

```python
    from app.plugins.installed.official_veeam.bridge import sync_target_to_server

    sync_target_to_server(db, target)
    return RemoteTargetResponse.model_validate(target)
```

In `update_remote_target`, after `updated = AgentRemoteTargetRepository.update(...)`:

```python
    from app.plugins.installed.official_veeam.bridge import sync_target_to_server

    sync_target_to_server(db, updated)
    return RemoteTargetResponse.model_validate(updated)
```

In `delete_remote_target`, before `AgentRemoteTargetRepository.delete(db, target_id)`:

```python
    from app.plugins.installed.official_veeam.bridge import remove_target_server

    remove_target_server(db, target_id)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `bash /tmp/check_task2.sh`
Expected: PASS (all 3 new + existing).

- [ ] **Step 5: Commit**

```bash
cd /opt/MissionControl
git add backend/app/routers/agent_remote_target.py backend/tests/test_agent_remote_target_plugins.py
git commit -m "feat(veeam): auto-register veeam_backup_servers from remote target plugins"
```

---

### Task 3: Backend — `_first_server` prefers enterprise REST rows

**Files:**
- Modify: `backend/app/plugins/installed/official_veeam/routes.py:29-36`
- Test: `backend/tests/test_veeam_target_bridge.py` (extend)

**Interfaces:**
- Consumes: `VeeamBackupServer`.
- Produces: `_first_server` returns enterprise row before community row.

- [ ] **Step 1: Write the failing test**

```python
def test_first_server_prefers_enterprise(client, db_session):
    from app.plugins.installed.official_veeam.models import VeeamBackupServer

    db_session.add(VeeamBackupServer(
        name="[Community]", edition="community", data_source="both",
        agent_id=1, target_id=1, enabled=True, status="unknown",
    ))
    db_session.add(VeeamBackupServer(
        name="Enterprise", edition="enterprise", data_source="api",
        rest_url="https://v:9419/api/v1", enabled=True, status="unknown",
    ))
    db_session.commit()
    resp = client.get("/api/v1/plugins/veeam/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("name") == "Enterprise" or data.get("error")  # route chose enterprise row
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash /tmp/check_task3.sh`
Expected: FAIL (community row chosen first — its name would appear in `health.name` after a failed connect, or no enterprise marker).

- [ ] **Step 3: Implement ordering**

Change `_first_server` in `routes.py`:

```python
def _first_server(db: Session) -> VeeamBackupServer | None:
    return (
        db.query(VeeamBackupServer)
        .filter(VeeamBackupServer.enabled.is_(True))
        .order_by(VeeamBackupServer.edition.desc(), VeeamBackupServer.id)
        .first()
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `bash /tmp/check_task3.sh`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd /opt/MissionControl
git add backend/app/plugins/installed/official_veeam/routes.py backend/tests/test_veeam_target_bridge.py
git commit -m "feat(veeam): prefer enterprise REST server rows in first_server"
```

---

### Task 4: Backend — link community profiles to matching targets

**Files:**
- Modify: `backend/app/plugins/installed/official_veeam/bridge.py`
- Test: `backend/tests/test_veeam_target_bridge.py` (extend)

**Interfaces:**
- Consumes: `AgentRemoteTarget`, `IntegrationProfile`.
- Produces: `sync_profile_to_server` populates `agent_id`/`target_id` on community rows when a matching veeam target exists.

- [ ] **Step 1: Write the failing test**

```python
def test_profile_linked_to_matching_target(db_session):
    from app.models.db.integration_profile import IntegrationProfile
    from app.plugins.installed.official_veeam.bridge import sync_profile_to_server
    from app.plugins.installed.official_veeam.models import VeeamBackupServer

    _, target = _make_target(db_session, name="Veeam Host", plugins="veeam")
    profile = IntegrationProfile(
        name="Veeam Profile",
        integration_type="veeam",
        enabled=True,
        data_source="both",
        ssh_host=target.hostname,
        ssh_username="kg\\administrator",
    )
    db_session.add(profile)
    db_session.commit()

    sync_profile_to_server(db_session, profile)

    row = db_session.query(VeeamBackupServer).filter(
        VeeamBackupServer.name == "Veeam Profile"
    ).one()
    assert row.agent_id == target.agent_id
    assert row.target_id == target.id
```

- [ ] **Step 2: Run test to verify it fails**

Run: `bash /tmp/check_task4.sh`
Expected: FAIL — `assert row.agent_id == target.agent_id` (None).

- [ ] **Step 3: Implement profile→target linking**

In `sync_profile_to_server`, after the existing `if existing is None / else` block and before `db.commit()`:

```python
    row = existing if existing is not None else server

    if row.rest_url is None and (row.agent_id is None or row.target_id is None):
        from app.models.db.agent_remote_target import AgentRemoteTarget

        ssh_host = (profile.ssh_host or "").strip()
        candidate = None
        for t in db.query(AgentRemoteTarget).filter(
            AgentRemoteTarget.enabled.is_(True)
        ):
            plugins = {
                p.strip() for p in (t.target_plugins or "").split(",") if p.strip()
            }
            if "veeam" not in plugins:
                continue
            if ssh_host and t.hostname == ssh_host:
                candidate = t
                break
            if candidate is None:
                candidate = t
        if candidate is not None:
            row.agent_id = candidate.agent_id
            row.target_id = candidate.id
            row.legacy_ssh_host = candidate.hostname
            row.legacy_ssh_port = candidate.port
            row.legacy_ssh_username = candidate.username
            row.legacy_ssh_password_encrypted = candidate.password_encrypted

    db.commit()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `bash /tmp/check_task4.sh`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd /opt/MissionControl
git add backend/app/plugins/installed/official_veeam/bridge.py backend/tests/test_veeam_target_bridge.py
git commit -m "feat(veeam): link community profiles to matching remote targets"
```

---

### Task 5: Agent — route `veeam` namespace to the plugin

**Files:**
- Modify: `.agents/agent/agent.py` (in `_execute_command`, `remote_execute` branch ~line 264)

**Interfaces:**
- Consumes: `PluginManager.execute_plugin_command(plugin_name, command, args)` (`.agents/agent/plugin.py:152`), `AgentSshExecutor` payload `{"namespace":"veeam","op":"veeam:*","params":{...}}`.
- Produces: `remote_execute` with `namespace=="veeam"` returns `{"success", "stdout": json.dumps(plugin_result), "stderr", "exit_code"}`.

- [ ] **Step 1: Modify `_execute_command`**

Replace the `remote_execute` block:

```python
            if command_type == "remote_execute":
                target_id = cmd.get("target_id")
                command_text = cmd.get("command", "")
                namespace = None
                op = None
                params: dict = {}
                if command_text.startswith("{"):
                    try:
                        payload = json.loads(command_text)
                        namespace = payload.get("namespace")
                        op = payload.get("op")
                        params = payload.get("params") or {}
                        if target_id is None:
                            target_id = payload.get("target_id")
                        if namespace is None:
                            command_text = payload.get("command", "")
                    except (json.JSONDecodeError, AttributeError):
                        pass
                if namespace == "veeam":
                    plugin_result = await self.plugin_manager.execute_plugin_command(
                        "veeam", op or "", params
                    )
                    ok = bool(plugin_result.get("success", False))
                    result = {
                        "success": ok,
                        "stdout": json.dumps(plugin_result),
                        "stderr": plugin_result.get("error")
                        or plugin_result.get("stderr")
                        or "",
                        "exit_code": 0 if ok else 1,
                    }
                elif target_id is None:
                    result = {
                        "success": False,
                        "stdout": "",
                        "stderr": "No target_id specified for remote_execute",
                        "exit_code": -1,
                    }
                else:
                    result = await self.remote_manager.execute_on_target(
                        target_id=target_id,
                        command=command_text,
                        timeout=cmd.get("timeout", self.config.command_timeout),
                    )
```

- [ ] **Step 2: Syntax check + verify existing behavior unaffected**

Run: `python -m py_compile .agents/agent/agent.py`
Expected: OK. (Non-namespace commands behave exactly as before — `namespace is None` path.)

- [ ] **Step 3: Commit**

```bash
cd /opt/MissionControl
git add .agents/agent/agent.py
git commit -m "feat(agent): route veeam namespace commands to Veeam plugin"
```

---

### Task 6: Agent — VeeamPlugin relay op dispatch

**Files:**
- Modify: `.agents/agent/plugins/veeam_plugin.py` (`_execute_relay`, ~line 714)

**Interfaces:**
- Consumes: `_run_collector_via_relay(collector)`, `_run_script_via_relay(script, timeout)`.
- Produces: `execute_command("veeam:jobs"|...)-> {"jobs":[...]} etc.` matching server `_json_payload`/provider keys: `jobs`, `sessions`, `repositories`, `managed_servers`, `restore_points`, `license`, `object_storages`, plus `job_stats`/`session_stats`/`job_stats_daily`/`test`/`start_job`/`stop_job`.

- [ ] **Step 1: Implement op dispatch at the top of `_execute_relay`**

```python
    async def _execute_relay(
        self, command: str, args: dict[str, Any]
    ) -> dict[str, Any]:
        collector_ops = {
            "veeam:jobs": "jobs",
            "veeam:sessions": "sessions",
            "veeam:repositories": "repositories",
            "veeam:managed_servers": "managed_servers",
            "veeam:restore_points": "restore_points",
            "veeam:license": "license",
        }
        if command in collector_ops:
            collector = collector_ops[command]
            items = await self._run_collector_via_relay(collector)
            if collector == "license":
                return {
                    "success": bool(items),
                    "license": items or {},
                    "error": None if items else "Veeam relay license unavailable",
                }
            return {
                "success": items is not None,
                collector: items or [],
                "count": len(items or []),
                "error": None if items is not None else "Veeam relay collection failed",
            }
        if command == "veeam:test":
            license_result = await self._run_collector_via_relay("license")
            return {
                "success": license_result is not None,
                "rest_available": False,
                "powershell_available": license_result is not None,
                "version": "",
                "error": None if license_result is not None else "Veeam relay unavailable",
            }
        if command == "veeam:job_stats":
            jobs = await self._run_collector_via_relay("jobs")
            return {
                "success": jobs is not None,
                "jobs": jobs or [],
                "count": len(jobs or []),
                "ssh_available": jobs is not None,
                "error": None if jobs is not None else "Veeam relay collection failed",
            }
        if command in ("veeam:session_stats", "veeam:job_stats_daily"):
            return {
                "success": True, "jobs": [], "dates": [], "count": 0,
                "ssh_available": False, "message": None, "error": None,
            }
        if command == "veeam:capacity_tier":
            return {"success": True, "object_storages": [], "count": 0, "error": None}
        if command == "test_connection":
            ... (existing body)
        if command == "start_job":
            ... (existing body)
        if command == "stop_job":
            ... (existing body)
        return {"success": False, "error": f"Unknown relay command: {command}"}
```

- [ ] **Step 2: Syntax check**

Run: `python -m py_compile .agents/agent/plugins/veeam_plugin.py`
Expected: OK.

- [ ] **Step 3: Commit**

```bash
cd /opt/MissionControl
git add .agents/agent/plugins/veeam_plugin.py
git commit -m "feat(agent): dispatch veeam:* relay ops in Veeam plugin"
```

---

### Task 7: Rebuild bundle + run full suite + deploy + verify

**Files:**
- Run: `.agents/build_bundle.py`
- Deploy: rebuild backend container; apply migration (none new); verify registry + Jobs route live.

- [ ] **Step 1: Run ruff + full backend suite**

```bash
cd /opt/MissionControl/backend
export TESTING=1
export MISSIONCONTROL_SECRET_KEY=$(/tmp/testvenv/bin/python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
export POSTGRES_DB=mission_control POSTGRES_USER=mission_control POSTGRES_PASSWORD=mission_control
export POSTGRES_HOST=localhost POSTGRES_PORT=5432
export REDIS_HOST=redis REDIS_PORT=6379
/tmp/venv/bin/ruff check app/plugins/installed/official_veeam/ app/routers/agent_remote_target.py
/tmp/testvenv/bin/python -m pytest tests/ -q --tb=short
```
Expected: ruff clean; all tests pass (≥1563 passed / 1 skipped).

- [ ] **Step 2: Rebuild agent bundle**

```bash
cd /opt/MissionControl/.agents
/tmp/testvenv/bin/python build_bundle.py
```
Expected: `built agent-bundle-v0.0.6.zip ... version v0.0.6`; `agent-bundle-live.zip` updated.

- [ ] **Step 3: Rebuild backend container**

```bash
cd /opt/MissionControl
docker compose -f docker-compose.prod.yml up -d --build backend
```
Wait until `missioncontrol-backend-1` is `healthy` (poll `docker inspect -f '{{.State.Health.Status}}'`).

- [ ] **Step 4: Live verify**

Script `/tmp/verify_veeam.sh`:
- Confirm `veeam_backup_servers` reflects the saved target (after user saves CORHQVEEMA with Veeam checked, or create a temp target via API/repo to simulate).
- `curl -sk -H "X-Agent-API-Key: $KEY" https://127.0.0.1/api/v1/plugins/veeam/jobs` returns a provider-shaped response (`{"success": ..., "jobs": [...], ...}` or a clear error, not a 500).
- `curl -sk .../api/v1/edge/1/bundle/download` header shows `x-agent-bundle-version: v0.0.6`.

- [ ] **Step 5: Commit any remaining artifacts (bundle zips/version tracked)**

```bash
cd /opt/MissionControl
git add .agents/agent-bundle-live.version .agents/agent-bundle-v0.0.6.zip .agents/agent-bundle-live.zip
git commit -m "chore(agent): rebuild bundle v0.0.6 with veeam namespace routing"
```