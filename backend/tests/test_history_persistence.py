"""
Command History Persistence and Duration Tests

Tests that verify history records are correctly saved and
retrieved with proper duration, timestamps, and filtering.
"""

from unittest.mock import AsyncMock, patch

from app.repositories.command_history_repository import CommandHistoryRepository

REMOTE_BASE = "/api/v1/remote"


def _create_credential(client, name="Hist Cred"):
    """Helper to create a credential profile."""
    resp = client.post(
        f"{REMOTE_BASE}/credentials",
        json={
            "name": name,
            "authentication_type": "ssh_key",
            "username": "testuser",
            "ssh_key": "fake-key",
        },
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def _create_host(client, credential_id, name="Hist Host"):
    """Helper to create a remote host."""
    resp = client.post(
        f"{REMOTE_BASE}/hosts",
        json={
            "name": name,
            "hostname": "hist.server.local",
            "ip_address": "10.0.0.50",
            "connection_type": "ssh",
            "port": 22,
            "enabled": True,
            "credential_profile_id": credential_id,
        },
    )
    assert resp.status_code == 201
    return resp.json()


# ------------------------------------------------------------------ #
# Duration and Timestamp Persistence                                  #
# ------------------------------------------------------------------ #


def test_history_records_duration_ms(client):
    """Test that duration_ms from provider is persisted to history."""
    cred_id = _create_credential(client)
    host = _create_host(client, cred_id)

    mock_result = {
        "success": True,
        "stdout": "ok\n",
        "stderr": "",
        "exit_code": 0,
        "duration_ms": 456,
    }

    mock_provider = AsyncMock()
    mock_provider.execute_command.return_value = mock_result

    with patch(
        "app.services.remote_service.get_remote_provider",
        return_value=mock_provider,
    ):
        resp = client.post(
            f"{REMOTE_BASE}/execute",
            json={
                "host_id": host["id"],
                "command": "echo ok",
                "shell": "bash",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["duration_ms"] == 456

    resp = client.get(f"{REMOTE_BASE}/history")
    items = resp.json()["items"]
    record = next(i for i in items if i["command"] == "echo ok")
    assert record["duration_ms"] == 456


def test_history_records_success_flag(client):
    """Test that success flag from provider is persisted."""
    cred_id = _create_credential(client)
    host = _create_host(client, cred_id)

    mock_result = {
        "success": False,
        "stdout": "",
        "stderr": "error",
        "exit_code": 1,
        "duration_ms": 100,
    }

    mock_provider = AsyncMock()
    mock_provider.execute_command.return_value = mock_result

    with patch(
        "app.services.remote_service.get_remote_provider",
        return_value=mock_provider,
    ):
        client.post(
            f"{REMOTE_BASE}/execute",
            json={
                "host_id": host["id"],
                "command": "failing_cmd",
                "shell": "bash",
            },
        )

    resp = client.get(f"{REMOTE_BASE}/history?success=false")
    items = resp.json()["items"]
    record = next(
        (i for i in items if i["command"] == "failing_cmd"), None
    )
    assert record is not None
    assert record["success"] is False
    assert record["exit_code"] == 1


def test_history_records_stdout_stderr(client):
    """Test that stdout and stderr from provider are persisted."""
    cred_id = _create_credential(client)
    host = _create_host(client, cred_id)

    mock_result = {
        "success": True,
        "stdout": "line1\nline2\n",
        "stderr": "warning: deprecated\n",
        "exit_code": 0,
        "duration_ms": 100,
    }

    mock_provider = AsyncMock()
    mock_provider.execute_command.return_value = mock_result

    with patch(
        "app.services.remote_service.get_remote_provider",
        return_value=mock_provider,
    ):
        client.post(
            f"{REMOTE_BASE}/execute",
            json={
                "host_id": host["id"],
                "command": "multi_output",
                "shell": "bash",
            },
        )

    resp = client.get(f"{REMOTE_BASE}/history")
    items = resp.json()["items"]
    record = next(
        (i for i in items if i["command"] == "multi_output"), None
    )
    assert record is not None
    assert record["stdout"] == "line1\nline2\n"
    assert record["stderr"] == "warning: deprecated\n"


def test_history_records_executed_by(client):
    """Test that executed_by username is persisted from credential."""
    cred_id = _create_credential(client)
    host = _create_host(client, cred_id)

    mock_result = {
        "success": True,
        "stdout": "ok",
        "stderr": "",
        "exit_code": 0,
        "duration_ms": 50,
    }

    mock_provider = AsyncMock()
    mock_provider.execute_command.return_value = mock_result

    with patch(
        "app.services.remote_service.get_remote_provider",
        return_value=mock_provider,
    ):
        client.post(
            f"{REMOTE_BASE}/execute",
            json={
                "host_id": host["id"],
                "command": "whoami",
                "shell": "bash",
            },
        )

    resp = client.get(f"{REMOTE_BASE}/history")
    items = resp.json()["items"]
    record = next(
        (i for i in items if i["command"] == "whoami"), None
    )
    assert record is not None
    assert record["executed_by"] == "testuser"


def test_history_records_shell_type(client):
    """Test that shell type is persisted to history."""
    cred_id = _create_credential(client)
    host = _create_host(client, cred_id)

    mock_result = {
        "success": True,
        "stdout": "ok",
        "stderr": "",
        "exit_code": 0,
        "duration_ms": 50,
    }

    mock_provider = AsyncMock()
    mock_provider.execute_command.return_value = mock_result

    with patch(
        "app.services.remote_service.get_remote_provider",
        return_value=mock_provider,
    ):
        client.post(
            f"{REMOTE_BASE}/execute",
            json={
                "host_id": host["id"],
                "command": "dir",
                "shell": "powershell",
            },
        )

    resp = client.get(f"{REMOTE_BASE}/history")
    items = resp.json()["items"]
    record = next(
        (i for i in items if i["command"] == "dir"), None
    )
    assert record is not None
    assert record["shell"] == "powershell"


# ------------------------------------------------------------------ #
# History Filtering                                                   #
# ------------------------------------------------------------------ #


def test_history_filter_by_multiple_hosts(client):
    """Test filtering history by different host IDs."""
    cred_id = _create_credential(client)
    host_a = _create_host(client, cred_id, "Host A")
    host_b = _create_host(client, cred_id, "Host B")

    mock_result = {
        "success": True,
        "stdout": "ok",
        "stderr": "",
        "exit_code": 0,
        "duration_ms": 100,
    }

    mock_provider = AsyncMock()
    mock_provider.execute_command.return_value = mock_result

    with patch(
        "app.services.remote_service.get_remote_provider",
        return_value=mock_provider,
    ):
        client.post(
            f"{REMOTE_BASE}/execute",
            json={
                "host_id": host_a["id"],
                "command": "cmd_a",
            },
        )
        client.post(
            f"{REMOTE_BASE}/execute",
            json={
                "host_id": host_b["id"],
                "command": "cmd_b",
            },
        )

    resp = client.get(f"{REMOTE_BASE}/history?host_id={host_a['id']}")
    items = resp.json()["items"]
    assert all(i["host_id"] == host_a["id"] for i in items)
    commands = [i["command"] for i in items]
    assert "cmd_a" in commands
    assert "cmd_b" not in commands


def test_history_limit(client):
    """Test that history respects limit parameter."""
    cred_id = _create_credential(client)
    host = _create_host(client, cred_id)

    mock_result = {
        "success": True,
        "stdout": "ok",
        "stderr": "",
        "exit_code": 0,
        "duration_ms": 10,
    }

    mock_provider = AsyncMock()
    mock_provider.execute_command.return_value = mock_result

    with patch(
        "app.services.remote_service.get_remote_provider",
        return_value=mock_provider,
    ):
        for i in range(5):
            client.post(
                f"{REMOTE_BASE}/execute",
                json={
                    "host_id": host["id"],
                    "command": f"cmd_{i}",
                },
            )

    resp = client.get(f"{REMOTE_BASE}/history?limit=2")
    assert resp.json()["count"] <= 2


def test_history_empty_when_no_commands(client):
    """Test history returns empty when no commands executed."""
    resp = client.get(f"{REMOTE_BASE}/history")
    assert resp.status_code == 200
    assert resp.json()["count"] == 0
    assert resp.json()["items"] == []


# ------------------------------------------------------------------ #
# History via Repository Directly                                     #
# ------------------------------------------------------------------ #


def test_repository_create_with_duration(db_session, sample_host):
    """Test repository persists duration_ms correctly."""
    record = CommandHistoryRepository.create(
        db=db_session,
        host_id=sample_host.id,
        command="perf_test",
        shell="bash",
        stdout="output",
        stderr="",
        exit_code=0,
        success=True,
        duration_ms=2345,
        executed_by="admin",
    )

    assert record.duration_ms == 2345

    found = CommandHistoryRepository.get_by_id(db_session, record.id)
    assert found.duration_ms == 2345


def test_repository_create_with_failure(db_session, sample_host):
    """Test repository persists failed command correctly."""
    record = CommandHistoryRepository.create(
        db=db_session,
        host_id=sample_host.id,
        command="bad_cmd",
        shell="bash",
        stdout="",
        stderr="error occurred",
        exit_code=127,
        success=False,
        duration_ms=50,
    )

    assert record.success is False
    assert record.exit_code == 127
    assert record.stderr == "error occurred"


def test_repository_filters_by_success(db_session, sample_host):
    """Test repository filters correctly by success status."""
    CommandHistoryRepository.create(
        db=db_session,
        host_id=sample_host.id,
        command="good_cmd",
        shell="bash",
        stdout="ok",
        stderr="",
        exit_code=0,
        success=True,
        duration_ms=100,
    )
    CommandHistoryRepository.create(
        db=db_session,
        host_id=sample_host.id,
        command="bad_cmd",
        shell="bash",
        stdout="",
        stderr="error",
        exit_code=1,
        success=False,
        duration_ms=50,
    )

    success_items = CommandHistoryRepository.get_filtered(
        db_session, success=True
    )
    failure_items = CommandHistoryRepository.get_filtered(
        db_session, success=False
    )

    assert all(r.success is True for r in success_items)
    assert all(r.success is False for r in failure_items)
    assert any(r.command == "good_cmd" for r in success_items)
    assert any(r.command == "bad_cmd" for r in failure_items)
