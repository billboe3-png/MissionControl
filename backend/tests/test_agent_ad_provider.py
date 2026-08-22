"""
Mission Control Agent Active Directory Provider Tests

Validates response shapes produced by AgentActiveDirectoryProvider match
the Pydantic response schemas (ADSummaryResponse, ADUsersResponse,
ADGroupsResponse, ADDevicesResponse, ADHealthResponse), that write
operations dispatch correctly, that unavailable relay inventory is
honored by every read getter, and that dispatched command rows carrying
plaintext secrets are purged once the terminal result is read.
"""

import pytest

from app.providers.identity.agent_ad_provider import AgentActiveDirectoryProvider


@pytest.fixture()
def provider() -> AgentActiveDirectoryProvider:
    inv = {
        "domain": {"name": "kg.local", "base_dn": "DC=kg,DC=local"},
        "users": [
            {
                "sam_account_name": "admin",
                "display_name": "Admin User",
                "enabled": True,
            }
        ],
        "groups": [{"name": "Domain Admins", "description": "Admins"}],
        "devices": [
            {"name": "CORHQDC01", "dns_name": "CORHQDC01.kg.local"}
        ],
        "health": {
            "status": "healthy",
            "replication": {
                "status": "healthy",
                "pending_replications": 0,
                "failed_replications": 0,
            },
        },
    }
    return AgentActiveDirectoryProvider(inventory=inv, hostname="CORHQROBERTB")


@pytest.mark.anyio()
async def test_agent_ad_provider_shapes(
    provider: AgentActiveDirectoryProvider,
) -> None:
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
    assert groups["groups"][0]["name"] == "Domain Admins"

    devices = await provider.get_devices()
    assert devices["connected"] is True
    assert len(devices["devices"]) == 1
    assert devices["devices"][0]["name"] == "CORHQDC01"

    health = await provider.get_health()
    assert health["connected"] is True
    assert health["status"] == "healthy"
    assert health["replication"]["status"] == "healthy"


@pytest.mark.anyio()
async def test_agent_ad_provider_write_ops_require_db():
    provider = AgentActiveDirectoryProvider(inventory={}, hostname="agent")
    result = await provider.reset_password("admin", "NewPass123!")
    assert result["success"] is False
    assert "No DB or agent_id" in result["error"]


@pytest.mark.anyio()
async def test_agent_ad_provider_get_user_groups_shape():
    provider = AgentActiveDirectoryProvider(inventory={}, hostname="agent")
    result = await provider.get_user_groups("admin")
    assert result["connected"] is False
    assert result["groups"] == []
    assert result["error"] is not None


# ------------------------------------------------------------------ #
# I3: unavailable relay inventory must report connected=False         #
# ------------------------------------------------------------------ #


@pytest.mark.anyio()
async def test_agent_ad_provider_unavailable_inventory():
    inv = {"available": False, "error": "AD relay failure"}
    provider = AgentActiveDirectoryProvider(inventory=inv, hostname="agent")

    summary = await provider.get_summary()
    assert summary["connected"] is False
    assert summary["error"] == "AD relay failure"
    assert summary["domain"] == {"name": "", "base_dn": ""}
    assert summary["user_count"] == 0
    assert summary["group_count"] == 0
    assert summary["computer_count"] == 0

    users = await provider.get_users()
    assert users["connected"] is False
    assert users["users"] == []
    assert users["total_count"] == 0
    assert users["error"] == "AD relay failure"

    groups = await provider.get_groups()
    assert groups["connected"] is False
    assert groups["groups"] == []
    assert groups["total_count"] == 0

    devices = await provider.get_devices()
    assert devices["connected"] is False
    assert devices["devices"] == []
    assert devices["total_count"] == 0

    health = await provider.get_health()
    assert health["connected"] is False
    assert health["status"] == "unknown"
    assert health["replication"] == {
        "status": "unknown",
        "pending_replications": 0,
        "failed_replications": 0,
    }

    test_conn = await provider.test_connection()
    assert test_conn["connected"] is False
    assert test_conn["error"] == "AD relay failure"


@pytest.mark.anyio()
async def test_agent_ad_provider_unavailable_default_error():
    provider = AgentActiveDirectoryProvider(
        inventory={"available": False}, hostname="agent"
    )
    summary = await provider.get_summary()
    assert summary["connected"] is False
    assert summary["error"] == "AD relay unavailable"


# ------------------------------------------------------------------ #
# I4: dispatched command rows are purged after the result is read     #
# ------------------------------------------------------------------ #


class _FakeCommand:
    def __init__(
        self,
        command_id: int,
        status: str,
        exit_code: int | None,
        stdout: str = "",
        stderr: str = "",
        error_message: str | None = None,
    ) -> None:
        self.id = command_id
        self.status = status
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.error_message = error_message


class _FakeDb:
    def __init__(self) -> None:
        self.deleted = []
        self.commits = 0

    def delete(self, obj) -> None:
        self.deleted.append(obj)

    def commit(self) -> None:
        self.commits += 1


@pytest.mark.anyio()
async def test_agent_ad_provider_dispatch_happy_path_purges_command(monkeypatch):
    import app.repositories.agent_repository as agent_repo

    fake_db = _FakeDb()
    provider = AgentActiveDirectoryProvider(
        inventory={}, hostname="agent", db=fake_db, agent_id=7, target_id=3
    )

    completed = _FakeCommand(
        command_id=42,
        status="completed",
        exit_code=0,
        stdout='{"success": true, "groups": [{"name": "Domain Users"}]}',
    )

    def fake_create(db, agent_id, command_type, command, **kwargs):
        return _FakeCommand(command_id=42, status="pending", exit_code=None)

    def fake_get_by_id(db, command_id):
        return completed

    monkeypatch.setattr(
        agent_repo.AgentCommandRepository, "create", staticmethod(fake_create)
    )
    monkeypatch.setattr(
        agent_repo.AgentCommandRepository, "get_by_id", staticmethod(fake_get_by_id)
    )

    result = await provider.get_user_groups("administrator")

    assert result["connected"] is True
    assert len(result["groups"]) == 1
    assert result["groups"][0]["name"] == "Domain Users"
    assert fake_db.deleted == [completed]
    assert fake_db.commits >= 1


@pytest.mark.anyio()
async def test_agent_ad_provider_dispatch_failure_purges_command(monkeypatch):
    import app.repositories.agent_repository as agent_repo

    fake_db = _FakeDb()
    provider = AgentActiveDirectoryProvider(
        inventory={}, hostname="agent", db=fake_db, agent_id=7, target_id=3
    )

    failed = _FakeCommand(
        command_id=43,
        status="completed",
        exit_code=1,
        stderr="Access denied",
        error_message="boom",
    )

    def fake_create(db, agent_id, command_type, command, **kwargs):
        return _FakeCommand(command_id=43, status="pending", exit_code=None)

    def fake_get_by_id(db, command_id):
        return failed

    monkeypatch.setattr(
        agent_repo.AgentCommandRepository, "create", staticmethod(fake_create)
    )
    monkeypatch.setattr(
        agent_repo.AgentCommandRepository, "get_by_id", staticmethod(fake_get_by_id)
    )

    result = await provider.reset_password("admin", "Secret123!")

    assert result["success"] is False
    assert "Access denied" in result["error"]
    assert fake_db.deleted == [failed]
    assert fake_db.commits >= 1


# ------------------------------------------------------------------ #
# I2: get_user_groups single-group shape normalization                #
# ------------------------------------------------------------------ #


@pytest.mark.anyio()
async def test_agent_ad_provider_get_user_groups_single_group_direct(monkeypatch):
    provider = AgentActiveDirectoryProvider(
        inventory={}, hostname="agent", db=_FakeDb(), agent_id=7, target_id=3
    )

    async def fake_dispatch(op, params):
        return {"success": True, "groups": [{"name": "Domain Users"}]}

    monkeypatch.setattr(provider, "_dispatch_cmd", fake_dispatch)

    result = await provider.get_user_groups("administrator")

    assert result["connected"] is True
    assert len(result["groups"]) == 1
    assert result["groups"][0]["name"] == "Domain Users"
    assert result["error"] is None


@pytest.mark.anyio()
async def test_agent_ad_provider_get_user_groups_single_group_normalization(
    monkeypatch,
):
    provider = AgentActiveDirectoryProvider(
        inventory={}, hostname="agent", db=_FakeDb(), agent_id=7, target_id=3
    )

    async def fake_dispatch(op, params):
        return {"success": True, "output": '[{"name": "Domain Users"}]'}

    monkeypatch.setattr(provider, "_dispatch_cmd", fake_dispatch)

    result = await provider.get_user_groups("administrator")

    assert result["connected"] is True
    assert len(result["groups"]) == 1
    assert result["groups"][0]["name"] == "Domain Users"
    assert result["error"] is None