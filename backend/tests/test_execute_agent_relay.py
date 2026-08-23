"""Tests for agent-relayed command execution (execute stream).

The relay queues a ``remote_execute`` command for the edge agent's poll
loop and streams the reported result back as SSE chunks.
"""

import pytest

from app.models.db.agent import Agent
from app.models.db.agent_remote_target import AgentRemoteTarget
from app.repositories.agent_repository import AgentCommandRepository
from app.repositories.command_history_repository import (
    CommandHistoryRepository,
)
from app.repositories.remote_host_repository import RemoteHostRepository
from app.schemas.remote_command import RemoteExecuteRequest
from app.schemas.remote_host import RemoteHostCreate
from app.services.remote_service import RemoteService


async def _seed_relay(db_session, hostname="relay.local", host_hostname=None):
    """Create an online agent with a matching remote target and a host."""
    host = RemoteHostRepository.create(
        db_session,
        RemoteHostCreate(
            name="Relay Host",
            hostname=host_hostname or hostname,
            connection_type="ssh",
            port=22,
        ),
    )
    agent = Agent(
        name="Relay Agent",
        hostname="relay.agent.local",
        api_key="relay-agent-api-key",
        status="online",
        enabled=True,
    )
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)

    target = AgentRemoteTarget(
        agent_id=agent.id,
        name="veeam",
        hostname=hostname,
        protocol="ssh",
        port=22,
        username="root",
        enabled=True,
    )
    db_session.add(target)
    db_session.commit()
    db_session.refresh(target)
    return host, agent, target


def test_execute_request_agent_id_defaults_to_none():
    req = RemoteExecuteRequest(host_id=1, command="uptime")
    assert req.agent_id is None
    assert RemoteExecuteRequest(host_id=1, command="uptime", agent_id=5).agent_id == 5


@pytest.mark.asyncio
async def test_relay_streams_reported_result(db_session):
    host, agent, target = await _seed_relay(db_session)
    service = RemoteService()

    real_get = AgentCommandRepository.get_by_id

    def fake_get(db, command_id):
        cmd = real_get(db, command_id)
        if cmd is not None and cmd.status == "pending":
            cmd.status = "completed"
            cmd.stdout = "Linux relay 6.1.0"
            cmd.stderr = ""
            cmd.exit_code = 0
            cmd.success = True
            cmd.duration_ms = 42
            db.commit()
            db.refresh(cmd)
        return cmd

    request = RemoteExecuteRequest(
        host_id=host.id, command="uname -a", shell="bash", agent_id=agent.id
    )
    chunks = []
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(AgentCommandRepository, "get_by_id", staticmethod(fake_get))
        async for chunk in service.execute_command_stream(db_session, request):
            chunks.append(chunk)

    types = [c["type"] for c in chunks]
    assert types == ["stdout", "exit"]
    assert chunks[0]["data"] == "Linux relay 6.1.0"
    assert chunks[1]["exit_code"] == 0

    # The queued command used the edge agent's native remote_execute shape.
    cmds = [
        c for c in AgentCommandRepository.get_by_agent(db_session, agent.id)
        if c.command_type == "remote_execute"
    ]
    assert len(cmds) == 1
    payload = cmds[0].command
    assert f'"target_id": {target.id}' in payload
    assert '"command": "uname -a"' in payload

    history = CommandHistoryRepository.get_all(db_session)
    assert any(
        h.host_id == host.id and h.success and h.exit_code == 0 for h in history
    )


@pytest.mark.asyncio
async def test_relay_reports_failure_exit_code(db_session):
    host, agent, _target = await _seed_relay(db_session)
    service = RemoteService()

    real_get = AgentCommandRepository.get_by_id

    def fake_get(db, command_id):
        cmd = real_get(db, command_id)
        if cmd is not None and cmd.status == "pending":
            cmd.status = "failed"
            cmd.stdout = ""
            cmd.stderr = "command not found"
            cmd.exit_code = 127
            cmd.success = False
            db.commit()
            db.refresh(cmd)
        return cmd

    request = RemoteExecuteRequest(
        host_id=host.id, command="nope", shell="bash", agent_id=agent.id
    )
    chunks = []
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(AgentCommandRepository, "get_by_id", staticmethod(fake_get))
        async for chunk in service.execute_command_stream(db_session, request):
            chunks.append(chunk)

    types = [c["type"] for c in chunks]
    assert types == ["stderr", "exit"]
    assert chunks[0]["data"] == "command not found"
    assert chunks[1]["exit_code"] == 127


@pytest.mark.asyncio
async def test_relay_offline_agent_yields_error(db_session):
    host, agent, _target = await _seed_relay(db_session)
    agent.status = "offline"
    db_session.commit()
    service = RemoteService()

    request = RemoteExecuteRequest(
        host_id=host.id, command="uptime", shell="bash", agent_id=agent.id
    )
    chunks = [
        chunk async for chunk in service.execute_command_stream(db_session, request)
    ]
    assert len(chunks) == 1
    assert chunks[0]["type"] == "error"
    assert "offline" in chunks[0]["message"]


@pytest.mark.asyncio
async def test_relay_unknown_agent_yields_error(db_session):
    host, _agent, _target = await _seed_relay(db_session)
    service = RemoteService()

    request = RemoteExecuteRequest(
        host_id=host.id, command="uptime", shell="bash", agent_id=99999
    )
    chunks = [
        chunk async for chunk in service.execute_command_stream(db_session, request)
    ]
    assert chunks == [{"type": "error", "message": "Agent not found"}]


@pytest.mark.asyncio
async def test_relay_unlinked_host_yields_error(db_session):
    host, agent, _target = await _seed_relay(
        db_session, hostname="relay.local", host_hostname="other.lan"
    )
    service = RemoteService()

    request = RemoteExecuteRequest(
        host_id=host.id, command="uptime", shell="bash", agent_id=agent.id
    )
    chunks = [
        chunk async for chunk in service.execute_command_stream(db_session, request)
    ]
    assert len(chunks) == 1
    assert chunks[0]["type"] == "error"
    assert "not configured as a remote target" in chunks[0]["message"]
