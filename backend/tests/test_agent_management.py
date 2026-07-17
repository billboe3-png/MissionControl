"""
Mission Control Agent Management Tests

Sprint 2.7 - Mission Control Agent.

Covers:
- Repository CRUD (Agent + AgentCommand)
- Service layer (registration, heartbeat, command dispatch, inventory)
- API endpoints (register, heartbeat, execute, CRUD)
- Authentication (API key validation)
- Command result reporting
"""


import pytest

from app.repositories.agent_repository import (
    AgentCommandRepository,
    AgentRepository,
)
from app.schemas.agent import (
    AgentCommandDispatchRequest,
    AgentCommandResultRequest,
    AgentHeartbeatRequest,
    AgentRegisterRequest,
    AgentUpdate,
)

# ------------------------------------------------------------------ #
# Fixtures                                                            #
# ------------------------------------------------------------------ #


@pytest.fixture
def sample_agent(db_session):
    """Create a sample agent for tests."""
    agent = AgentRepository.create(
        db_session,
        name="Test Agent",
        hostname="test.agent.local",
        api_key="mc_agent_testkey1234567890abcdef",
        operating_system="Linux",
        os_version="Ubuntu 22.04",
        ip_address="10.0.0.100",
        agent_version="1.0.0",
        status="online",
    )
    return agent


@pytest.fixture
def sample_offline_agent(db_session):
    """Create a sample offline agent for tests."""
    return AgentRepository.create(
        db_session,
        name="Offline Agent",
        hostname="offline.agent.local",
        api_key="mc_agent_offlinekey1234567890abcdef",
        status="offline",
    )


@pytest.fixture
def sample_command(db_session, sample_agent):
    """Create a sample pending command."""
    return AgentCommandRepository.create(
        db_session,
        agent_id=sample_agent.id,
        command_type="execute",
        command="ls -la",
        timeout=30,
    )


# ------------------------------------------------------------------ #
# Repository Tests                                                    #
# ------------------------------------------------------------------ #


class TestAgentRepository:
    def test_create_agent(self, db_session):
        agent = AgentRepository.create(
            db_session,
            name="New Agent",
            hostname="new.agent.local",
            api_key="mc_agent_newkey123",
        )
        assert agent.id is not None
        assert agent.name == "New Agent"
        assert agent.hostname == "new.agent.local"
        assert agent.status == "offline"

    def test_get_by_id(self, db_session, sample_agent):
        found = AgentRepository.get_by_id(db_session, sample_agent.id)
        assert found is not None
        assert found.name == "Test Agent"

    def test_get_by_id_not_found(self, db_session):
        found = AgentRepository.get_by_id(db_session, 99999)
        assert found is None

    def test_get_by_api_key(self, db_session, sample_agent):
        found = AgentRepository.get_by_api_key(
            db_session, "mc_agent_testkey1234567890abcdef"
        )
        assert found is not None
        assert found.id == sample_agent.id

    def test_get_by_hostname(self, db_session, sample_agent):
        found = AgentRepository.get_by_hostname(
            db_session, "test.agent.local"
        )
        assert found is not None

    def test_get_all(self, db_session, sample_agent, sample_offline_agent):
        agents = AgentRepository.get_all(db_session)
        assert len(agents) >= 2

    def test_count_all(self, db_session, sample_agent):
        count = AgentRepository.count_all(db_session)
        assert count >= 1

    def test_count_by_status(self, db_session, sample_agent):
        count = AgentRepository.count_by_status(db_session, "online")
        assert count >= 1

    def test_get_online_agents(self, db_session, sample_agent):
        online = AgentRepository.get_online_agents(db_session)
        assert len(online) >= 1
        assert all(a.status == "online" for a in online)

    def test_update_agent(self, db_session, sample_agent):
        updated = AgentRepository.update(
            db_session, sample_agent.id, name="Updated Agent"
        )
        assert updated is not None
        assert updated.name == "Updated Agent"

    def test_update_not_found(self, db_session):
        result = AgentRepository.update(db_session, 99999, name="X")
        assert result is None

    def test_delete_agent(self, db_session, sample_agent):
        deleted = AgentRepository.delete(db_session, sample_agent.id)
        assert deleted is True
        assert AgentRepository.get_by_id(db_session, sample_agent.id) is None

    def test_delete_not_found(self, db_session):
        deleted = AgentRepository.delete(db_session, 99999)
        assert deleted is False


class TestAgentCommandRepository:
    def test_create_command(self, db_session, sample_agent):
        cmd = AgentCommandRepository.create(
            db_session,
            agent_id=sample_agent.id,
            command_type="execute",
            command="whoami",
        )
        assert cmd.id is not None
        assert cmd.command == "whoami"
        assert cmd.status == "pending"

    def test_get_pending_for_agent(self, db_session, sample_command):
        pending = AgentCommandRepository.get_pending_for_agent(
            db_session, sample_command.agent_id
        )
        assert len(pending) >= 1

    def test_get_by_agent(self, db_session, sample_command):
        commands = AgentCommandRepository.get_by_agent(
            db_session, sample_command.agent_id
        )
        assert len(commands) >= 1

    def test_get_by_id(self, db_session, sample_command):
        found = AgentCommandRepository.get_by_id(
            db_session, sample_command.id
        )
        assert found is not None
        assert found.command == "ls -la"

    def test_update_command(self, db_session, sample_command):
        updated = AgentCommandRepository.update(
            db_session,
            sample_command.id,
            status="completed",
            stdout="total 0",
            exit_code=0,
            success=True,
        )
        assert updated is not None
        assert updated.status == "completed"
        assert updated.success is True

    def test_count_by_status(self, db_session, sample_command):
        count = AgentCommandRepository.count_by_status(
            db_session, sample_command.agent_id, "pending"
        )
        assert count >= 1


# ------------------------------------------------------------------ #
# Service Tests                                                       #
# ------------------------------------------------------------------ #


class TestAgentService:
    @pytest.mark.asyncio
    async def test_register_agent(self, db_session):
        from app.services.agent_service import AgentService

        service = AgentService()
        data = AgentRegisterRequest(
            name="New Agent",
            hostname="new.agent.local",
            operating_system="Ubuntu 22.04",
            os_version="22.04 LTS",
            ip_address="192.168.1.50",
            agent_version="1.0.0",
        )
        result = await service.register_agent(db_session, data)
        assert result.agent_id is not None
        assert result.api_key.startswith("mc_agent_")
        assert result.heartbeat_interval == 30

    @pytest.mark.asyncio
    async def test_register_existing_hostname(self, db_session, sample_agent):
        from app.services.agent_service import AgentService

        service = AgentService()
        data = AgentRegisterRequest(
            name="Re-registered Agent",
            hostname="test.agent.local",
            agent_version="2.0.0",
        )
        result = await service.register_agent(db_session, data)
        assert result.agent_id == sample_agent.id
        assert "re-registered" in result.message.lower()

    @pytest.mark.asyncio
    async def test_list_agents(self, db_session, sample_agent):
        from app.services.agent_service import AgentService

        service = AgentService()
        result = await service.list_agents(db_session)
        assert result.count >= 1
        assert result.online >= 1

    @pytest.mark.asyncio
    async def test_get_agent(self, db_session, sample_agent):
        from app.services.agent_service import AgentService

        service = AgentService()
        result = await service.get_agent(db_session, sample_agent.id)
        assert result.name == "Test Agent"

    @pytest.mark.asyncio
    async def test_get_agent_not_found(self, db_session):
        from fastapi import HTTPException

        from app.services.agent_service import AgentService

        service = AgentService()
        with pytest.raises(HTTPException) as exc_info:
            await service.get_agent(db_session, 99999)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_agent(self, db_session, sample_agent):
        from app.services.agent_service import AgentService

        service = AgentService()
        data = AgentUpdate(name="Updated Agent", tags="linux,production")
        result = await service.update_agent(
            db_session, sample_agent.id, data
        )
        assert result.name == "Updated Agent"
        assert result.tags == "linux,production"

    @pytest.mark.asyncio
    async def test_enable_disable(self, db_session, sample_agent):
        from app.services.agent_service import AgentService

        service = AgentService()
        result = await service.disable_agent(db_session, sample_agent.id)
        assert result.enabled is False

        result = await service.enable_agent(db_session, sample_agent.id)
        assert result.enabled is True

    @pytest.mark.asyncio
    async def test_delete_agent(self, db_session, sample_agent):
        from app.services.agent_service import AgentService

        service = AgentService()
        await service.delete_agent(db_session, sample_agent.id)
        assert (
            AgentRepository.get_by_id(db_session, sample_agent.id) is None
        )

    @pytest.mark.asyncio
    async def test_delete_not_found(self, db_session):
        from fastapi import HTTPException

        from app.services.agent_service import AgentService

        service = AgentService()
        with pytest.raises(HTTPException) as exc_info:
            await service.delete_agent(db_session, 99999)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_process_heartbeat(self, db_session, sample_agent):
        from app.services.agent_service import AgentService

        service = AgentService()
        data = AgentHeartbeatRequest(
            agent_id=sample_agent.id,
            health="healthy",
            cpu_percent=25.0,
            memory_percent=60.0,
            disk_percent=45.0,
        )
        result = await service.process_heartbeat(
            db_session, data, sample_agent.api_key
        )
        assert result.heartbeat_interval == 30

    @pytest.mark.asyncio
    async def test_heartbeat_wrong_key(self, db_session, sample_agent):
        from fastapi import HTTPException

        from app.services.agent_service import AgentService

        service = AgentService()
        data = AgentHeartbeatRequest(agent_id=sample_agent.id)
        with pytest.raises(HTTPException) as exc_info:
            await service.process_heartbeat(
                db_session, data, "wrong_key"
            )
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_dispatch_command(self, db_session, sample_agent):
        from app.services.agent_service import AgentService

        service = AgentService()
        data = AgentCommandDispatchRequest(
            agent_id=sample_agent.id,
            command_type="execute",
            command="uname -a",
            timeout=30,
        )
        result = await service.dispatch_command(db_session, data)
        assert result.id is not None
        assert result.status == "pending"

    @pytest.mark.asyncio
    async def test_dispatch_to_offline_agent(
        self, db_session, sample_offline_agent
    ):
        from fastapi import HTTPException

        from app.services.agent_service import AgentService

        service = AgentService()
        data = AgentCommandDispatchRequest(
            agent_id=sample_offline_agent.id,
            command_type="execute",
            command="test",
        )
        with pytest.raises(HTTPException) as exc_info:
            await service.dispatch_command(db_session, data)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_report_command_result(
        self, db_session, sample_command, sample_agent
    ):
        from app.services.agent_service import AgentService

        service = AgentService()
        data = AgentCommandResultRequest(
            command_id=sample_command.id,
            exit_code=0,
            stdout="root",
            success=True,
            duration_ms=150,
        )
        result = await service.report_command_result(
            db_session, data, sample_agent.id
        )
        assert result.received is True

    @pytest.mark.asyncio
    async def test_update_inventory(self, db_session, sample_agent):
        from app.services.agent_service import AgentService

        service = AgentService()
        inventory = {"system": {"hostname": "test"}, "cpu": {"cores": 4}}
        result = await service.update_inventory(
            db_session, sample_agent.id, inventory, sample_agent.api_key
        )
        assert result["received"] is True

    @pytest.mark.asyncio
    async def test_get_inventory(self, db_session, sample_agent):
        from app.services.agent_service import AgentService

        service = AgentService()
        result = await service.get_inventory(db_session, sample_agent.id)
        assert result.agent_id == sample_agent.id
        assert result.agent_name == "Test Agent"


# ------------------------------------------------------------------ #
# API Tests                                                           #
# ------------------------------------------------------------------ #


class TestAgentAPI:
    def test_register_agent(self, client):
        resp = client.post(
            "/api/v1/agents/register",
            json={
                "name": "API Agent",
                "hostname": "api.agent.local",
                "operating_system": "Linux",
                "agent_version": "1.0.0",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["agent_id"] is not None
        assert data["api_key"].startswith("mc_agent_")

    def test_list_agents(self, client):
        resp = client.get("/api/v1/agents")
        assert resp.status_code == 200
        data = resp.json()
        assert "count" in data
        assert "items" in data
        assert "online" in data
        assert "offline" in data

    def test_get_agent(self, client):
        reg_resp = client.post(
            "/api/v1/agents/register",
            json={
                "name": "Get Agent",
                "hostname": "get.agent.local",
            },
        )
        agent_id = reg_resp.json()["agent_id"]
        resp = client.get(f"/api/v1/agents/{agent_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Get Agent"

    def test_get_agent_not_found(self, client):
        resp = client.get("/api/v1/agents/99999")
        assert resp.status_code == 404

    def test_update_agent(self, client):
        reg_resp = client.post(
            "/api/v1/agents/register",
            json={
                "name": "Upd Agent",
                "hostname": "upd.agent.local",
            },
        )
        agent_id = reg_resp.json()["agent_id"]
        resp = client.put(
            f"/api/v1/agents/{agent_id}",
            json={"name": "Updated Agent", "tags": "test"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Agent"

    def test_delete_agent(self, client):
        reg_resp = client.post(
            "/api/v1/agents/register",
            json={
                "name": "Del Agent",
                "hostname": "del.agent.local",
            },
        )
        agent_id = reg_resp.json()["agent_id"]
        resp = client.delete(f"/api/v1/agents/{agent_id}")
        assert resp.status_code == 204

    def test_delete_agent_not_found(self, client):
        resp = client.delete("/api/v1/agents/99999")
        assert resp.status_code == 404

    def test_enable_disable_agent(self, client):
        reg_resp = client.post(
            "/api/v1/agents/register",
            json={
                "name": "Toggle Agent",
                "hostname": "toggle.agent.local",
            },
        )
        agent_id = reg_resp.json()["agent_id"]

        resp = client.post(f"/api/v1/agents/{agent_id}/disable")
        assert resp.status_code == 200
        assert resp.json()["enabled"] is False

        resp = client.post(f"/api/v1/agents/{agent_id}/enable")
        assert resp.status_code == 200
        assert resp.json()["enabled"] is True

    def test_heartbeat(self, client):
        reg_resp = client.post(
            "/api/v1/agents/register",
            json={
                "name": "HB Agent",
                "hostname": "hb.agent.local",
            },
        )
        data = reg_resp.json()
        agent_id = data["agent_id"]
        api_key = data["api_key"]

        resp = client.post(
            "/api/v1/agents/heartbeat",
            json={
                "agent_id": agent_id,
                "health": "healthy",
                "cpu_percent": 50.0,
            },
            headers={"X-Agent-API-Key": api_key},
        )
        assert resp.status_code == 200
        assert "commands" in resp.json()

    def test_heartbeat_invalid_key(self, client):
        resp = client.post(
            "/api/v1/agents/heartbeat",
            json={"agent_id": 1, "health": "healthy"},
            headers={"X-Agent-API-Key": "invalid_key"},
        )
        assert resp.status_code in [401, 422]

    def test_dispatch_command(self, client):
        reg_resp = client.post(
            "/api/v1/agents/register",
            json={
                "name": "Exec Agent",
                "hostname": "exec.agent.local",
            },
        )
        agent_id = reg_resp.json()["agent_id"]

        resp = client.post(
            f"/api/v1/agents/{agent_id}/execute",
            json={
                "command_type": "execute",
                "command": "echo hello",
                "timeout": 30,
            },
        )
        assert resp.status_code == 201
        assert resp.json()["command_type"] == "execute"

    def test_get_agent_commands(self, client):
        reg_resp = client.post(
            "/api/v1/agents/register",
            json={
                "name": "Cmd Agent",
                "hostname": "cmd.agent.local",
            },
        )
        agent_id = reg_resp.json()["agent_id"]

        resp = client.get(f"/api/v1/agents/{agent_id}/commands")
        assert resp.status_code == 200
        assert "items" in resp.json()

    def test_get_all_commands(self, client):
        resp = client.get("/api/v1/agents/commands/all")
        assert resp.status_code == 200
        assert "items" in resp.json()

    def test_get_inventory(self, client):
        reg_resp = client.post(
            "/api/v1/agents/register",
            json={
                "name": "Inv Agent",
                "hostname": "inv.agent.local",
            },
        )
        agent_id = reg_resp.json()["agent_id"]

        resp = client.get(f"/api/v1/agents/{agent_id}/inventory")
        assert resp.status_code == 200
        assert resp.json()["agent_id"] == agent_id

    def test_version_endpoint(self, client):
        resp = client.get("/api/v1/agents/version")
        assert resp.status_code == 200
        assert "version" in resp.json()

    def test_command_result_reporting(self, client):
        reg_resp = client.post(
            "/api/v1/agents/register",
            json={
                "name": "Result Agent",
                "hostname": "result.agent.local",
            },
        )
        data = reg_resp.json()
        agent_id = data["agent_id"]
        api_key = data["api_key"]

        exec_resp = client.post(
            f"/api/v1/agents/{agent_id}/execute",
            json={
                "command_type": "execute",
                "command": "echo test",
                "timeout": 10,
            },
        )
        cmd_id = exec_resp.json()["id"]

        resp = client.post(
            f"/api/v1/agents/{agent_id}/command-result",
            json={
                "command_id": cmd_id,
                "exit_code": 0,
                "stdout": "test\n",
                "stderr": "",
                "success": True,
                "duration_ms": 100,
            },
            headers={"X-Agent-API-Key": api_key},
        )
        assert resp.status_code == 200
        assert resp.json()["received"] is True

    def test_inventory_update(self, client):
        reg_resp = client.post(
            "/api/v1/agents/register",
            json={
                "name": "InvPush Agent",
                "hostname": "invpush.agent.local",
            },
        )
        data = reg_resp.json()
        agent_id = data["agent_id"]
        api_key = data["api_key"]

        resp = client.post(
            f"/api/v1/agents/{agent_id}/inventory",
            json={"system": {"hostname": "test"}, "cpu": {"cores": 4}},
            headers={"X-Agent-API-Key": api_key},
        )
        assert resp.status_code == 200
        assert resp.json()["received"] is True

    @pytest.mark.asyncio
    async def test_mark_stale_agents_offline(self, db_session):
        from datetime import UTC, datetime, timedelta

        from app.services.agent_service import AgentService

        agent = AgentRepository.create(
            db_session,
            name="Stale Agent",
            hostname="stale.agent.local",
            api_key="mc_agent_stalekey1234567890abcdef",
            status="online",
        )
        agent.last_heartbeat = datetime.now(UTC) - timedelta(seconds=200)
        db_session.commit()

        service = AgentService()
        await service.mark_stale_agents_offline(db_session)

        db_session.refresh(agent)
        assert agent.status == "offline"

    def test_get_commands_with_status_filter(self, client):
        reg_resp = client.post(
            "/api/v1/agents/register",
            json={
                "name": "Filter Agent",
                "hostname": "filter.agent.local",
            },
        )
        agent_id = reg_resp.json()["agent_id"]

        client.post(
            f"/api/v1/agents/{agent_id}/execute",
            json={
                "command_type": "execute",
                "command": "echo filter",
                "timeout": 10,
            },
        )

        resp = client.get(
            "/api/v1/agents/commands/all?status=pending"
        )
        assert resp.status_code == 200
        assert "items" in resp.json()
