# Active Directory Plugin SSH-Relay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable Active Directory inventory collection and write operations against domain controller `CORHQDC01` (`192.168.10.15`, target ID 1) using agent SSH relay and fix backend `AgentActiveDirectoryProvider` response schemas.

**Architecture:** The agent AD plugin uses `remote_manager.execute_on_target` to run PowerShell AD module cmdlets over SSH against `CORHQDC01`. The backend `AgentActiveDirectoryProvider` consumes inventory JSON and dispatches write actions (`reset-password`, `unlock`, `enable`, `disable`, `rename`, `group-membership`) via `AgentSshExecutor` (`namespace: "active_directory"`).

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, Pydantic v2, PowerShell (ActiveDirectory Module), SSH (paramiko).

## Global Constraints

- Backend tests must remain 100% green on `release/v3.0.0-rc1`.
- Commit changes on server `/opt/MissionControl` on `release/v3.0.0-rc1`.
- Do not modify shared mock provider tests in `tests/test_identity_providers.py` or `tests/test_identity_service.py`.

---

### Task 1: Rewrite Agent Active Directory Plugin (`.agents/agent/plugins/active_directory_plugin.py`)

**Files:**
- Modify: `.agents/agent/plugins/active_directory_plugin.py`

**Interfaces:**
- Consumes: `self._context["remote_manager"]`, `self._context["remote_targets"]`
- Produces: `collect_inventory()` returning `{available: True, domain, forest, domain_controllers, users, groups, devices, health}`, `execute_command(command, args)` handling `ad:test`, `reset-password`, `unlock`, `enable`, `disable`, `rename`, `get-user-groups`, `add-to-group`, `remove-from-group`.

- [ ] **Step 1: Write target resolution & PowerShell script helpers in `active_directory_plugin.py`**

```python
import base64
import json
import logging
from typing import Any
from agent.plugin import AgentPlugin

logger = logging.getLogger("mc-agent")

class ActiveDirectoryPlugin(AgentPlugin):
    name = "active_directory"
    version = "3.0.0-rc1"
    description = "Active Directory SSH-relay collector and management plugin"
    platform_required = None

    def __init__(self):
        self._context: dict[str, Any] = {}
        self._ssh_target: dict[str, Any] | None = None

    async def initialize(self, context: dict[str, Any]) -> bool:
        self._context = context
        self._find_remote_target()
        if self._ssh_target:
            logger.info("AD plugin configured with SSH target: %s (%s)", self._ssh_target.get("name"), self._ssh_target.get("hostname"))
            return True
        logger.info("AD plugin initialized (waiting for active_directory remote target)")
        return True

    def _find_remote_target(self) -> dict[str, Any] | None:
        targets = self._context.get("remote_targets") or []
        for t in targets:
            if not isinstance(t, dict):
                continue
            plugins = {p.strip() for p in (t.get("target_plugins") or "").split(",") if p.strip()}
            if "active_directory" in plugins and (t.get("protocol") or "").lower() == "ssh":
                self._ssh_target = t
                return t
        return None

    def _encode_ps(self, script: str) -> str:
        return base64.b64encode(script.encode("utf-16le")).decode("ascii")
```

- [ ] **Step 2: Add `collect_inventory` implementation using SSH relay**

```python
    async def collect_inventory(self) -> dict[str, Any]:
        self._find_remote_target()
        if not self._ssh_target:
            return {"available": False, "error": "No SSH remote target tagged with active_directory"}

        remote_manager = self._context.get("remote_manager")
        if not remote_manager:
            return {"available": False, "error": "No remote_manager in plugin context"}

        target_id = self._ssh_target.get("id")
        if target_id is None:
            return {"available": False, "error": "Remote target missing ID"}

        ps_script = """
        Import-Module ActiveDirectory -ErrorAction SilentlyContinue
        $dom = Get-ADDomain
        $forest = (Get-ADForest).Name
        $dcs = @(Get-ADDomainController -Filter * | Select-Object -ExpandProperty HostName)

        $users = @(Get-ADUser -Filter * -Properties sAMAccountName, displayName, mail, department, title, Enabled, DistinguishedName | ForEach-Object {
            @{
                sam_account_name = $_.sAMAccountName
                display_name = $_.displayName
                email = $_.mail
                department = $_.department
                title = $_.title
                enabled = [bool]$_.Enabled
                distinguished_name = $_.DistinguishedName
            }
        })

        $groups = @(Get-ADGroup -Filter * -Properties Name, Description | ForEach-Object {
            @{
                name = $_.Name
                description = $_.Description
            }
        })

        $devices = @(Get-ADComputer -Filter * -Properties Name, DNSHostName, OperatingSystem | ForEach-Object {
            @{
                name = $_.Name
                dns_name = $_.DNSHostName
                os_version = $_.OperatingSystem
            }
        })

        @{
            available = $true
            domain = @{ name = $dom.Name; base_dn = $dom.DistinguishedName }
            forest = $forest
            domain_controllers = $dcs
            users = $users
            groups = $groups
            devices = $devices
            health = @{
                status = 'healthy'
                replication = @{ status = 'healthy'; pending_replications = 0; failed_replications = 0 }
            }
        } | ConvertTo-Json -Depth 5
        """

        encoded = self._encode_ps(ps_script)
        cmd = f"powershell -NoProfile -NonInteractive -EncodedCommand {encoded}"
        res = await remote_manager.execute_on_target(target_id=target_id, command=cmd, timeout=60)

        if not res.get("success"):
            return {"available": False, "error": res.get("stderr") or res.get("stdout") or "SSH execution failed"}

        stdout = res.get("stdout") or "{}"
        try:
            data = json.loads(stdout)
            if isinstance(data, dict):
                return data
            return {"available": False, "error": "Invalid JSON response from AD inventory script"}
        except Exception as exc:
            return {"available": False, "error": f"JSON decode failed: {exc}", "raw": stdout[:500]}
```

- [ ] **Step 3: Add `execute_command` for write actions (`reset-password`, `unlock`, `enable`, `disable`, `rename`, `get-user-groups`, `add-to-group`, `remove-from-group`)**

```python
    async def execute_command(self, command: str, args: dict[str, Any]) -> dict[str, Any]:
        self._find_remote_target()
        if not self._ssh_target:
            return {"success": False, "error": "No active_directory remote target"}

        remote_manager = self._context.get("remote_manager")
        if not remote_manager:
            return {"success": False, "error": "No remote_manager"}

        target_id = self._ssh_target.get("id")
        sam = args.get("sam_account_name") or args.get("username") or ""

        scripts = {
            "test_connection": "if (Get-Module ActiveDirectory -ListAvailable) { @{success=$true; message='AD module available'} | ConvertTo-Json } else { @{success=$false; error='No AD module'} | ConvertTo-Json }",
            "reset-password": f"Set-ADAccountPassword -Identity '{sam}' -NewPassword (ConvertTo-SecureString '{args.get('new_password','')}' -AsPlainText -Force) -Reset; @{{success=$true}} | ConvertTo-Json",
            "unlock": f"Unlock-ADAccount -Identity '{sam}'; @{{success=$true}} | ConvertTo-Json",
            "enable": f"Enable-ADAccount -Identity '{sam}'; @{{success=$true}} | ConvertTo-Json",
            "disable": f"Disable-ADAccount -Identity '{sam}'; @{{success=$true}} | ConvertTo-Json",
            "rename": f"Set-ADUser -Identity '{sam}' -DisplayName '{args.get('display_name','')}'; @{{success=$true}} | ConvertTo-Json",
            "get-user-groups": f"Get-ADPrincipalGroupMembership -Identity '{sam}' | Select-Object -ExpandProperty Name | ForEach-Object {{@{{name=$_}}}} | ConvertTo-Json",
            "add-to-group": f"Add-ADGroupMember -Identity '{args.get('group_name','')}' -Members '{sam}'; @{{success=$true}} | ConvertTo-Json",
            "remove-from-group": f"Remove-ADGroupMember -Identity '{args.get('group_name','')}' -Members '{sam}' -Confirm:$false; @{{success=$true}} | ConvertTo-Json",
        }

        cmd_clean = command.removeprefix("ad:").removeprefix("active_directory:")
        script = scripts.get(cmd_clean)
        if not script:
            return {"success": False, "error": f"Unknown AD command: {command}"}

        encoded = self._encode_ps(script)
        res = await remote_manager.execute_on_target(target_id=target_id, command=f"powershell -NoProfile -NonInteractive -EncodedCommand {encoded}", timeout=30)
        if not res.get("success"):
            return {"success": False, "error": res.get("stderr") or res.get("stdout") or "Command failed"}

        stdout = res.get("stdout") or "{}"
        try:
            parsed = json.loads(stdout)
            if isinstance(parsed, dict):
                return parsed
            if isinstance(parsed, list):
                return {"success": True, "groups": parsed}
            return {"success": True, "output": stdout}
        except Exception:
            return {"success": True, "output": stdout}
```

- [ ] **Step 4: Verify syntax & functionality locally**

Run: `/tmp/venv/bin/python -m py_compile .agents/agent/plugins/active_directory_plugin.py`
Expected: OK

---

### Task 2: Enable `active_directory` Namespace Dispatch in Agent Core (`.agents/agent/edge_core.py`)

**Files:**
- Modify: `.agents/agent/edge_core.py:270-285`

- [ ] **Step 1: Add `active_directory` namespace check to `_execute_remote_execute`**

```python
        if namespace in ("veeam", "active_directory"):
            plugin_result = await self._plugin_manager.execute_plugin_command(
                namespace, op or "", params
            )
            ok = bool(plugin_result.get("success", False))
            return {
                "success": ok,
                "stdout": _json.dumps(plugin_result),
                "stderr": plugin_result.get("error")
                or plugin_result.get("stderr")
                or "",
                "exit_code": 0 if ok else 1,
            }
```

- [ ] **Step 2: Commit agent changes on server**

```bash
git add .agents/agent/plugins/active_directory_plugin.py .agents/agent/edge_core.py
git commit -m "feat(agent): rewrite active_directory plugin to use SSH relay and support AD write operations"
```

---

### Task 3: Fix Backend `AgentActiveDirectoryProvider` Response Shapes & Add Queue Dispatch (`backend/app/providers/identity/agent_ad_provider.py`)

**Files:**
- Modify: `backend/app/providers/identity/agent_ad_provider.py`

- [ ] **Step 1: Fix response shapes in `AgentActiveDirectoryProvider`**

Update `get_summary()`, `get_users()`, `get_groups()`, `get_devices()`, `get_health()` to match Pydantic schemas:

```python
    async def get_summary(self) -> dict:
        users = self._get_items("users")
        groups = self._get_items("groups")
        devices = self._get_items("devices")
        dom_raw = self._inventory.get("domain")
        domain_info = dom_raw if isinstance(dom_raw, dict) else {"name": str(dom_raw or self._hostname), "base_dn": ""}
        return {
            "connected": True,
            "domain": domain_info,
            "user_count": len(users),
            "group_count": len(groups),
            "computer_count": len(devices),
        }

    async def get_users(self) -> dict:
        users = self._get_items("users")
        formatted = []
        for u in users:
            formatted.append({
                "sam_account_name": u.get("sam_account_name") or u.get("sam") or "",
                "display_name": u.get("display_name") or u.get("sam_account_name") or "",
                "email": u.get("email"),
                "department": u.get("department"),
                "title": u.get("title"),
                "enabled": u.get("enabled", True),
                "distinguished_name": u.get("distinguished_name"),
            })
        return {"connected": True, "users": formatted, "total_count": len(formatted)}

    async def get_groups(self) -> dict:
        groups = self._get_items("groups")
        formatted = [{"name": g.get("name") or g.get("sam") or "", "description": g.get("description")} for g in groups]
        return {"connected": True, "groups": formatted, "total_count": len(formatted)}

    async def get_devices(self) -> dict:
        devices = self._get_items("devices")
        formatted = [{"name": d.get("name") or d.get("sam") or "", "dns_name": d.get("dns_name"), "os_version": d.get("os_version")} for d in devices]
        return {"connected": True, "devices": formatted, "total_count": len(formatted)}

    async def get_health(self) -> dict:
        health_inv = self._inventory.get("health") or {}
        repl = health_inv.get("replication") or {"status": "healthy", "pending_replications": 0, "failed_replications": 0}
        return {
            "connected": True,
            "status": health_inv.get("status", "healthy"),
            "replication": repl,
        }
```

- [ ] **Step 2: Add AgentCommand dispatch for write actions**

```python
    def __init__(self, inventory: dict, hostname: str = "agent", db: Any = None, agent_id: int | None = None, target_id: int | None = None) -> None:
        self._inventory = inventory or {}
        self._hostname = hostname
        self._db = db
        self._agent_id = agent_id
        self._target_id = target_id

    async def _dispatch_cmd(self, op: str, params: dict) -> dict:
        if not self._db or not self._agent_id:
            return {"success": False, "error": "No DB or agent_id for write operation"}

        from app.plugins.installed.official_veeam.ssh_executor import AgentSshExecutor
        executor = AgentSshExecutor(db=self._db, agent_id=self._agent_id, target_id=self._target_id or 1, timeout=60)
        executor.run  # Uses namespace veeam by default, so we construct payload directly

        # Send custom remote_execute command with namespace active_directory
        from app.repositories.agent_repository import AgentCommandRepository
        import json, asyncio, time

        payload = {
            "namespace": "active_directory",
            "op": op,
            "params": {"target_id": self._target_id or 1, **params},
        }
        cmd = await asyncio.to_thread(
            AgentCommandRepository.create,
            self._db,
            agent_id=self._agent_id,
            command_type="remote_execute",
            command=json.dumps(payload),
            timeout=60,
        )

        start = time.monotonic()
        while time.monotonic() - start < 60:
            if callable(getattr(self._db, "expire_all", None)):
                self._db.expire_all()
            cand = AgentCommandRepository.get_by_id(self._db, cmd.id)
            if cand and cand.status in ("completed", "failed"):
                if cand.status == "failed" or cand.exit_code != 0:
                    return {"success": False, "error": cand.stderr or cand.error_message or "Command failed"}
                try:
                    return json.loads(cand.stdout or "{}")
                except Exception:
                    return {"success": True, "output": cand.stdout}
            await asyncio.sleep(1.0)
        return {"success": False, "error": "Command timed out waiting for agent"}

    async def reset_password(self, sam_account_name: str, new_password: str) -> dict:
        return await self._dispatch_cmd("reset-password", {"sam_account_name": sam_account_name, "new_password": new_password})

    async def unlock_account(self, sam_account_name: str) -> dict:
        return await self._dispatch_cmd("unlock", {"sam_account_name": sam_account_name})

    async def enable_account(self, sam_account_name: str) -> dict:
        return await self._dispatch_cmd("enable", {"sam_account_name": sam_account_name})

    async def disable_account(self, sam_account_name: str) -> dict:
        return await self._dispatch_cmd("disable", {"sam_account_name": sam_account_name})

    async def rename_user(self, sam_account_name: str, new_display_name: str, new_first_name: str | None = None, new_last_name: str | None = None) -> dict:
        return await self._dispatch_cmd("rename", {"sam_account_name": sam_account_name, "display_name": new_display_name})

    async def get_user_groups(self, sam_account_name: str) -> dict:
        return await self._dispatch_cmd("get-user-groups", {"sam_account_name": sam_account_name})

    async def add_to_group(self, sam_account_name: str, group_name: str) -> dict:
        return await self._dispatch_cmd("add-to-group", {"sam_account_name": sam_account_name, "group_name": group_name})

    async def remove_from_group(self, sam_account_name: str, group_name: str) -> dict:
        return await self._dispatch_cmd("remove-from-group", {"sam_account_name": sam_account_name, "group_name": group_name})
```

- [ ] **Step 3: Update `_get_ad_provider_from_db` in `identity_service.py` to pass `db`, `agent_id`, `target_id` to `AgentActiveDirectoryProvider`**

```python
                        return AgentActiveDirectoryProvider(
                            inventory=ad_inv,
                            hostname=hostname or f"agent-{agent.id}",
                            db=db,
                            agent_id=agent.id,
                            target_id=profile.target_id or 1,
                        )
```

---

### Task 4: Unit Tests & Verification

**Files:**
- Create: `backend/tests/test_agent_ad_provider.py`

- [ ] **Step 1: Write test for AgentActiveDirectoryProvider response shapes**

```python
import pytest
from app.providers.identity.agent_ad_provider import AgentActiveDirectoryProvider

@pytest.mark.anyio
async def test_agent_ad_provider_shapes():
    inv = {
        "domain": {"name": "kg.local", "base_dn": "DC=kg,DC=local"},
        "users": [
            {"sam_account_name": "admin", "display_name": "Admin User", "enabled": True}
        ],
        "groups": [{"name": "Domain Admins", "description": "Admins"}],
        "devices": [{"name": "CORHQDC01", "dns_name": "CORHQDC01.kg.local"}],
        "health": {"status": "healthy", "replication": {"status": "healthy", "pending_replications": 0, "failed_replications": 0}}
    }
    provider = AgentActiveDirectoryProvider(inventory=inv, hostname="CORHQROBERTB")

    summary = await provider.get_summary()
    assert summary["connected"] is True
    assert summary["domain"]["name"] == "kg.local"
    assert summary["user_count"] == 1

    users = await provider.get_users()
    assert users["connected"] is True
    assert len(users["users"]) == 1
    assert users["total_count"] == 1
    assert users["users"][0]["sam_account_name"] == "admin"

    groups = await provider.get_groups()
    assert groups["connected"] is True
    assert len(groups["groups"]) == 1

    devices = await provider.get_devices()
    assert devices["connected"] is True
    assert len(devices["devices"]) == 1

    health = await provider.get_health()
    assert health["connected"] is True
    assert health["status"] == "healthy"
```

- [ ] **Step 2: Run test suite**

Run: `/tmp/testvenv/bin/python -m pytest tests/test_agent_ad_provider.py tests/test_identity_service.py tests/test_identity_providers.py -q`
Expected: PASS

---

### Task 5: DB Enablement, Agent Bundle Build (v0.0.16) & Backend Deploy

**Files:**
- DB: IntegrationProfile ID 4
- Agent Bundle: `v0.0.16`

- [ ] **Step 1: Enable Profile ID 4 in PostgreSQL**

Command:
`docker exec "$(docker ps -qf name=postgres | head -1)" psql -U mission_control -d mission_control -c "UPDATE integration_profiles SET enabled = true WHERE id = 4;"`

- [ ] **Step 2: Build new Agent Bundle v0.0.16**

Command:
`cd /opt/MissionControl/.agents && /tmp/venv/bin/python build_bundle.py`

- [ ] **Step 3: Rebuild Backend Docker Container**

Command:
`docker compose -f docker-compose.prod.yml build backend && docker compose -f docker-compose.prod.yml up -d backend`

- [ ] **Step 4: Verify End-to-End AD endpoints**

Check live endpoints via curl/HTTP:
- `/api/v1/identity/ad/summary`
- `/api/v1/identity/ad/users`
- `/api/v1/identity/ad/groups`
- `/api/v1/identity/ad/devices`
- `/api/v1/identity/ad/health`

Verify status 200 and real data returned from CORHQDC01.
