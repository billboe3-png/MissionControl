# Plan: Agent Relay (Zabbix Proxy Model)

## Overview

Extend the Mission Control agent to act as a **network relay**, connecting to remote machines inside the agent's network that the server cannot reach directly. The server manages target configurations and pushes them to agents via heartbeat responses. The agent connects to targets via PowerShell Remoting, SSH, or WinRM, collects inventory data, and relays it back.

## Architecture

```
┌─────────────────────────────────────────────────┐
│           Mission Control Server (GCE)           │
│                                                  │
│  ┌──────────────┐    ┌────────────────────────┐  │
│  │ Agent Service │    │ Remote Target Service   │  │
│  │ (heartbeat,   │    │ (CRUD, target mgmt)    │  │
│  │  commands)    │    │                        │  │
│  └──────┬───────┘    └────────┬───────────────┘  │
│         │                     │                   │
│  ┌──────┴─────────────────────┴───────────────┐  │
│  │         agent_remote_targets table          │  │
│  └────────────────────────────────────────────┘  │
│                      │                           │
│         Heartbeat response includes targets      │
└──────────────────────┼───────────────────────────┘
                       │ HTTPS (outbound from agent)
┌──────────────────────┼───────────────────────────┐
│        Agent (inside customer network)           │
│                      │                           │
│  ┌───────────────────┴────────────────────────┐  │
│  │           RemoteManager                     │  │
│  │  ┌──────────┐ ┌────────┐ ┌──────────────┐  │  │
│  │  │PSRemoting│ │  SSH   │ │    WinRM     │  │  │
│  │  └────┬─────┘ └───┬────┘ └──────┬───────┘  │  │
│  └───────┼────────────┼─────────────┼──────────┘  │
│          │            │             │             │
└──────────┼────────────┼─────────────┼─────────────┘
           │            │             │
     ┌─────┴──┐   ┌─────┴──┐   ┌─────┴──┐
     │Win Svr │   │Linux   │   │Win Svr │
     │(HyperV)│   │Server  │   │(File)  │
     └────────┘   └────────┘   └────────┘
```

## Data Flow

1. **Admin** creates remote targets in Mission Control UI, assigning them to an agent
2. **Server** stores targets in `agent_remote_targets` table with encrypted credentials
3. **Agent heartbeat** → Server responds with `remote_targets` list (host, protocol, port, credentials)
4. **Agent** runs `_remote_inventory_loop()` every `remote_inventory_interval` (default 300s):
   - Connects to each target via appropriate protocol
   - Collects system inventory, Hyper-V VMs, services
   - Sends all data to `POST /api/v1/agents/{id}/inventory` under `remote_targets` key
5. **Server** stores remote target data in `agent.inventory_json` alongside local inventory
6. **Frontend** reads from a new endpoint or extends existing Hyper-V endpoints to include agent-relayed data

## Inventory Structure (remote_targets key)

```json
{
  "remote_targets": {
    "target-1": {
      "hostname": "HV-HOST01",
      "protocol": "psremoting",
      "collected_at": "2026-07-24T10:00:00Z",
      "status": "online",
      "error": null,
      "inventory": {
        "system": { "hostname": "...", "os": "...", "uptime": ... },
        "cpu": { "cores": ..., "percent": ... },
        "memory": { "total": ..., "used": ..., "percent": ... },
        "disks": [...],
        "network": { "interfaces": {...} },
        "services": [...],
        "hyperv": {
          "vm_count": 5,
          "vms": [...],
          "switches": [...]
        }
      }
    },
    "target-2": {
      "hostname": "web01.lan",
      "protocol": "ssh",
      "status": "online",
      "inventory": {
        "system": {...},
        "cpu": {...},
        "memory": {...},
        "disks": [...],
        "services": [...]
      }
    }
  }
}
```

---

## Implementation Steps

### Step 1: Database — `agent_remote_targets` table

**New file**: `backend/app/models/db/agent_remote_target.py`

```python
class AgentRemoteTarget(Base):
    __tablename__ = "agent_remote_targets"

    id: int (PK)
    agent_id: int (FK -> agents.id, CASCADE)
    name: str (200)                    # Display name
    hostname: str (500)                # Target hostname or IP
    protocol: str (20)                 # "psremoting" | "ssh" | "winrm"
    port: int                          # 5985/5986 for WinRM/PSRemoting, 22 for SSH
    username: str (200)                # Auth username
    password_encrypted: str | None     # Encrypted password (Fernet)
    ssh_key_encrypted: str | None      # Encrypted SSH private key (Fernet)
    enabled: bool (default True)
    tags: str | None                   # Comma-separated tags
    notes: str | None
    last_collected_at: datetime | None # Last successful inventory collection
    last_status: str (20, default "unknown")  # "online" | "offline" | "error"
    last_error: str | None             # Last connection error message
    created_at: datetime
    updated_at: datetime
```

**New migration**: `backend/alembic/versions/<hash>_add_agent_remote_targets.py`

- Create table with all columns
- Index on `agent_id`
- FK to `agents.id` with CASCADE delete

**New file**: `backend/app/repositories/agent_remote_target_repository.py`

CRUD operations:
- `get_by_agent_id(db, agent_id)` → list of targets
- `get_by_id(db, target_id)` → single target
- `create(db, agent_id, **kwargs)` → target
- `update(db, target_id, **kwargs)` → target
- `delete(db, target_id)` → None
- `get_enabled_by_agent_id(db, agent_id)` → list of enabled targets

---

### Step 2: Backend API — Remote Target CRUD

**New file**: `backend/app/schemas/agent_remote_target.py`

```python
class RemoteTargetCreate(BaseModel):
    name: str
    hostname: str
    protocol: Literal["psremoting", "ssh", "winrm"]
    port: int | None = None           # Auto-filled by protocol
    username: str
    password: str | None = None       # Plaintext, encrypted before storage
    ssh_key: str | None = None        # Plaintext, encrypted before storage
    enabled: bool = True
    tags: str | None = None
    notes: str | None = None

class RemoteTargetUpdate(BaseModel):
    name: str | None = None
    hostname: str | None = None
    protocol: Literal["psremoting", "ssh", "winrm"] | None = None
    port: int | None = None
    username: str | None = None
    password: str | None = None
    ssh_key: str | None = None
    enabled: bool | None = None
    tags: str | None = None
    notes: str | None = None

class RemoteTargetResponse(BaseModel):
    id: int
    agent_id: int
    name: str
    hostname: str
    protocol: str
    port: int
    username: str
    enabled: bool
    tags: str | None
    notes: str | None
    last_collected_at: datetime | None
    last_status: str
    last_error: str | None
    created_at: datetime
    # NO password/ssh_key in response

class AgentRemoteTargetsResponse(BaseModel):
    agent_id: int
    agent_name: str
    targets: list[RemoteTargetResponse]
```

**New file**: `backend/app/routers/agent_remote_target.py`

Endpoints (all require auth):
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/agents/{agent_id}/remote-targets` | List targets for agent |
| `POST` | `/api/v1/agents/{agent_id}/remote-targets` | Create target |
| `GET` | `/api/v1/agents/{agent_id}/remote-targets/{target_id}` | Get single target |
| `PUT` | `/api/v1/agents/{agent_id}/remote-targets/{target_id}` | Update target |
| `DELETE` | `/api/v1/agents/{agent_id}/remote-targets/{target_id}` | Delete target |
| `POST` | `/api/v1/agents/{agent_id}/remote-targets/{target_id}/test` | Test connection |

**Modify**: `backend/app/main.py` — Register new router

---

### Step 3: Heartbeat — Push Targets to Agent

**Modify**: `backend/app/schemas/agent.py`

Add to `AgentHeartbeatResponse`:
```python
remote_targets: list[dict] | None = None  # Targets for agent to monitor
```

Each target dict in the response:
```python
{
    "id": 1,
    "name": "HV-HOST01",
    "hostname": "192.168.1.50",
    "protocol": "psremoting",
    "port": 5985,
    "username": "admin",
    "password": "decrypted_password",  # Decrypted by server before sending
    "ssh_key": None,
    "tags": "hyper-v,production",
}
```

**Modify**: `backend/app/services/agent_service.py`

In `process_heartbeat()`:
1. After fetching pending commands, also fetch enabled remote targets for this agent
2. Decrypt credentials using `CredentialCipher`
3. Add to heartbeat response as `remote_targets`

```python
# In process_heartbeat(), after fetching commands:
from app.repositories.agent_remote_target_repository import AgentRemoteTargetRepository
from app.core.security import CredentialCipher

cipher = CredentialCipher(settings.missioncontrol_secret_key)
targets = AgentRemoteTargetRepository.get_enabled_by_agent_id(db, agent_id)
remote_targets = []
for t in targets:
    remote_targets.append({
        "id": t.id,
        "name": t.name,
        "hostname": t.hostname,
        "protocol": t.protocol,
        "port": t.port,
        "username": t.username,
        "password": cipher.decrypt(t.password_encrypted) if t.password_encrypted else None,
        "ssh_key": cipher.decrypt(t.ssh_key_encrypted) if t.ssh_key_encrypted else None,
        "tags": t.tags,
    })
```

---

### Step 4: Agent — Remote Connection Manager

**New file**: `.agents/agent/remote.py`

Core class: `RemoteManager`

```python
class RemoteManager:
    """Manages connections to remote targets relayed through the agent."""

    def __init__(self):
        self._targets: dict[int, RemoteTarget] = {}
        self._connectors: dict[int, RemoteConnector] = {}

    def update_targets(self, targets: list[dict]) -> None:
        """Update target list from heartbeat response."""
        ...

    async def collect_inventory(self) -> dict[str, Any]:
        """Collect inventory from all targets concurrently."""
        ...

    async def execute_on_target(self, target_id: int, command: str, timeout: int) -> dict:
        """Execute a command on a specific target."""
        ...
```

**New file**: `.agents/agent/connectors/__init__.py`

**New file**: `.agents/agent/connectors/base.py`

```python
class RemoteConnector(ABC):
    """Base class for remote target connectors."""
    @abstractmethod
    async def connect(self) -> bool: ...
    @abstractmethod
    async def execute(self, command: str, timeout: int) -> dict: ...
    @abstractmethod
    async def collect_system_inventory(self) -> dict: ...
    @abstractmethod
    async def collect_hyperv_inventory(self) -> dict | None: ...
    @abstractmethod
    async def collect_services(self) -> list[dict]: ...
    @abstractmethod
    async def disconnect(self) -> None: ...
```

**New file**: `.agents/agent/connectors/psremoting.py`

PowerShell Remoting connector using `subprocess` + `powershell`:
- Uses `Invoke-Command -HostName` or `Enter-PSSession` equivalent
- Commands run via: `powershell -Command "Invoke-Command -ComputerName {host} -Credential $cred -ScriptBlock { ... }"`
- Inventory collection: runs CIM/WMI commands on remote host
- Hyper-V: runs `Get-VM` on remote host
- Dependencies: none (uses built-in Windows PS Remoting)

**New file**: `.agents/agent/connectors/ssh.py`

SSH connector using `paramiko` (synchronous, wrapped in `asyncio.to_thread`):
- Connects via paramiko SSHClient
- Runs commands via `exec_command()`
- Inventory: parses `/proc/`, `free`, `df`, `systemctl` output
- Dependencies: `paramiko`

**New file**: `.agents/agent/connectors/winrm_connector.py`

WinRM connector using `winrm` library:
- Connects via `winrm.Session`
- Runs commands via PowerShell over WinRM
- Inventory: same CIM/WMI commands as PSRemoting
- Dependencies: `pywinrm`

---

### Step 5: Agent — Remote Inventory Loop

**Modify**: `.agents/agent/agent.py`

Add `remote_manager: RemoteManager` to `MissionControlAgent.__init__()`.

Add new loop `_remote_inventory_loop()`:
```python
async def _remote_inventory_loop(self) -> None:
    """Periodic remote target inventory collection."""
    while self._running:
        try:
            await asyncio.sleep(self.config.remote_inventory_interval)
            if not self._running:
                break

            remote_data = await self.remote_manager.collect_inventory()
            if remote_data:
                # Store for next inventory upload
                self._remote_inventory_cache = remote_data
                logger.info("Remote inventory collected: %d targets",
                           len(remote_data.get("targets", {})))
        except Exception as e:
            logger.warning("Remote inventory cycle failed: %s", e)
```

Modify `_inventory_loop()` to include cached remote data:
```python
# In _inventory_loop(), after collecting local + plugin inventory:
if hasattr(self, '_remote_inventory_cache') and self._remote_inventory_cache:
    inventory["remote_targets"] = self._remote_inventory_cache
```

Modify `_heartbeat_loop()` to pass remote targets to RemoteManager:
```python
# In _heartbeat_loop(), after receiving heartbeat response:
remote_targets = response.get("remote_targets")
if remote_targets:
    self.remote_manager.update_targets(remote_targets)
```

Launch `_remote_inventory_loop()` in `start()` alongside existing loops.

---

### Step 6: Agent — Remote Command Execution

**Modify**: `.agents/agent/executor.py`

Add new command type `"remote_execute"`:
```python
elif command_type == "remote_execute":
    target_id = args.get("target_id")
    command = args.get("command", "")
    timeout = args.get("timeout", self.timeout)
    result = await self.remote_manager.execute_on_target(target_id, command, timeout)
    return result
```

**Modify**: `.agents/agent/agent.py`

In `_execute_command()`, handle `remote_execute` by passing target context.

---

### Step 7: Agent — Config & Dependencies

**Modify**: `.agents/agent/config.py`

Add:
```python
remote_inventory_interval: int = 300  # MC_REMOTE_INVENTORY_INTERVAL
```

**Modify**: `.agents/agent/requirements.txt` (or `pyproject.toml`)

Add:
```
paramiko>=3.0.0
pywinrm>=0.5.0
```

**Modify**: `install-agent.ps1`

Update pip install to include new dependencies.

---

### Step 8: Backend — Expose Remote Target Data

**Modify**: `backend/app/routers/agent.py`

Add endpoint to get remote target inventory:
```python
@router.get("/{agent_id}/remote-inventory")
async def get_remote_inventory(agent_id: int, ...):
    """Get remote target inventory from agent's latest inventory data."""
```

This reads `agent.inventory_json`, extracts `remote_targets` key, returns it.

**Optionally modify**: `backend/app/providers/hyperv/provider_factory.py`

Add `AgentHyperVProvider` that reads Hyper-V data from agent inventory:
- When `list_hyperv_hosts()` is called, also include agents with hyperv remote target data
- `AgentHyperVProvider.get_vms()` reads from `agent.inventory_json["remote_targets"][target]["inventory"]["hyperv"]`
- This makes agent-relayed Hyper-V data appear in the existing Hyper-V pages

---

### Step 9: Frontend — Agent Remote Targets UI

**New file**: `frontend/src/pages/agents/AgentRemoteTargetsPage.tsx`

- Table listing remote targets for an agent
- Add/edit/delete target dialogs (name, hostname, protocol, port, username, password)
- "Test Connection" button per target
- Status indicator (online/offline/error) with last collected time
- View collected inventory per target

**New file**: `frontend/src/services/agentRemoteTarget.ts`

API client for `/api/v1/agents/{id}/remote-targets` endpoints.

**Modify**: `frontend/src/pages/agents/AgentDetailPage.tsx`

Add "Remote Targets" tab to agent detail page.

---

### Step 10: Tests

**Backend tests**:
- `tests/test_agent_remote_target_api.py` — CRUD endpoint tests
- `tests/test_agent_service_remote_targets.py` — Heartbeat with remote targets
- `tests/test_agent_remote_target_model.py` — Model/repository tests

**Agent tests**:
- `tests/test_remote_manager.py` — RemoteManager unit tests
- `tests/test_connectors.py` — Connector tests (mocked)
- `tests/test_executor_remote.py` — Remote execute command tests

---

## File Change Summary

### New files (backend)
| File | Purpose |
|------|---------|
| `backend/app/models/db/agent_remote_target.py` | ORM model |
| `backend/app/repositories/agent_remote_target_repository.py` | CRUD repository |
| `backend/app/schemas/agent_remote_target.py` | Pydantic schemas |
| `backend/app/routers/agent_remote_target.py` | API endpoints |
| `backend/alembic/versions/<hash>_add_agent_remote_targets.py` | Migration |
| `backend/tests/test_agent_remote_target_api.py` | API tests |

### New files (agent)
| File | Purpose |
|------|---------|
| `.agents/agent/remote.py` | RemoteManager class |
| `.agents/agent/connectors/__init__.py` | Package init |
| `.agents/agent/connectors/base.py` | Abstract connector |
| `.agents/agent/connectors/psremoting.py` | PowerShell Remoting |
| `.agents/agent/connectors/ssh.py` | SSH via paramiko |
| `.agents/agent/connectors/winrm_connector.py` | WinRM via pywinrm |

### New files (frontend)
| File | Purpose |
|------|---------|
| `frontend/src/pages/agents/AgentRemoteTargetsPage.tsx` | Targets management UI |
| `frontend/src/services/agentRemoteTarget.ts` | API client |

### Modified files (backend)
| File | Change |
|------|--------|
| `backend/app/main.py` | Register remote target router |
| `backend/app/schemas/agent.py` | Add `remote_targets` to heartbeat response |
| `backend/app/services/agent_service.py` | Push targets in heartbeat, decrypt credentials |

### Modified files (agent)
| File | Change |
|------|--------|
| `.agents/agent/agent.py` | Add RemoteManager, remote inventory loop, heartbeat target passing |
| `.agents/agent/executor.py` | Add `remote_execute` command type |
| `.agents/agent/config.py` | Add `remote_inventory_interval` |
| `install-agent.ps1` | Add paramiko/pywinrm to pip install |

### Modified files (frontend)
| File | Change |
|------|--------|
| `frontend/src/pages/agents/AgentDetailPage.tsx` | Add Remote Targets tab |
| `frontend/src/App.tsx` | Add route for remote targets page |

---

## Dependencies

### Agent Python packages (new)
```
paramiko>=3.0.0      # SSH connector
pywinrm>=0.5.0       # WinRM connector
```

PS Remoting requires no new dependencies (uses built-in Windows PowerShell).

---

## Security Considerations

1. **Credentials encrypted at rest**: `password_encrypted` and `ssh_key_encrypted` use Fernet (AES-128-CBC + HMAC-SHA256) via existing `CredentialCipher`
2. **Credentials decrypted only in transit**: Server decrypts credentials only when building heartbeat response, sent over HTTPS to agent
3. **Agent stores targets in memory only**: Targets are not persisted on agent disk — they come from heartbeat response and live in RAM
4. **No credential logging**: All connector code must avoid logging passwords/keys
5. **API key authentication**: Remote target CRUD endpoints require user auth (JWT), agent endpoints require agent API key

---

## Implementation Order

1. Database model + migration (Step 1)
2. Repository + schemas (Step 1)
3. Backend API endpoints (Step 2)
4. Heartbeat modification (Step 3)
5. Agent RemoteManager + connectors (Step 4)
6. Agent inventory loop (Step 5)
7. Agent command execution (Step 6)
8. Agent config + dependencies (Step 7)
9. Backend expose remote data (Step 8)
10. Frontend UI (Step 9)
11. Tests (Step 10)
