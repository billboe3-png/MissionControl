"""Tests for the Veeam SSH executor abstraction."""

import json

import pytest

from app.plugins.installed.official_veeam.ssh_executor import (
    AgentSshExecutor,
    DirectSshExecutor,
)


class FakeCommand:
    def __init__(self, status="pending", stdout="", stderr="", exit_code=None):
        self.id = 7
        self.status = status
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code


class FakeCommandRepo:
    def __init__(self, sequence):
        self.sequence = list(sequence)
        self.created = None

    def create(self, db, agent_id, command_type, command, timeout):
        self.created = {"agent_id": agent_id, "command_type": command_type,
                        "command": command, "timeout": timeout}
        return self.sequence[0]

    def get_by_id(self, db, command_id):
        if self.sequence:
            return self.sequence.pop(0)
        return FakeCommand("pending")


class FakeAgentRepo:
    def __init__(self, status="online"):
        self.status = status

    def get_by_id(self, db, agent_id):
        return type("A", (), {"status": self.status, "name": "a1"})()


@pytest.mark.anyio
async def test_agent_executor_dispatches_veeam_payload():
    payload = {"success": True, "edition": "enterprise", "error": None}
    repo = FakeCommandRepo([
        FakeCommand("pending"),
        FakeCommand("completed", stdout=json.dumps(payload)),
    ])
    executor = AgentSshExecutor(
        db=object(), agent_id=1, target_id=2,
        command_repo=repo, agent_repo=FakeAgentRepo(),
    )
    result = await executor.run("veeam:test")
    assert result["success"] is True
    assert result["output"] == json.dumps(payload)
    assert repo.created["command_type"] == "remote_execute"
    dispatched = json.loads(repo.created["command"])
    assert dispatched["namespace"] == "veeam"
    assert dispatched["op"] == "veeam:test"
    assert dispatched["params"]["target_id"] == 2


@pytest.mark.anyio
async def test_agent_executor_failed_status_returns_error():
    repo = FakeCommandRepo([
        FakeCommand("pending"),
        FakeCommand("failed", stderr="boom", exit_code=1),
    ])
    executor = AgentSshExecutor(
        db=object(), agent_id=1, target_id=2,
        command_repo=repo, agent_repo=FakeAgentRepo(),
    )
    result = await executor.run("veeam:jobs")
    assert result["success"] is False
    assert "boom" in result["error"]


@pytest.mark.anyio
async def test_agent_executor_times_out():
    repo = FakeCommandRepo([FakeCommand("pending")])
    executor = AgentSshExecutor(
        db=object(), agent_id=1, target_id=2,
        command_repo=repo, agent_repo=FakeAgentRepo(),
        poll_interval=0.01, timeout=0.05,
    )
    result = await executor.run("veeam:jobs")
    assert result["success"] is False
    assert "timed out" in result["error"].lower()


@pytest.mark.anyio
async def test_agent_executor_offline_agent():
    repo = FakeCommandRepo([])
    executor = AgentSshExecutor(
        db=object(), agent_id=1, target_id=2,
        command_repo=repo, agent_repo=FakeAgentRepo(status="offline"),
    )
    result = await executor.run("veeam:jobs")
    assert result["success"] is False
    assert "offline" in result["error"].lower()


def test_direct_executor_rejected_in_production():
    with pytest.raises(RuntimeError):
        DirectSshExecutor(
            host="v", port=22, username="u", password="p",
            environment="production",
        )
