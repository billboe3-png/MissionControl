"""
Remote Operations API Tests

Full CRUD and execution tests for the /api/v1/remote endpoints.
"""

from unittest.mock import AsyncMock, patch

REMOTE_BASE = "/api/v1/remote"


def _create_credential(client, name="Test Cred"):
    """Helper to create a credential profile and return its ID."""
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


def _create_host(client, credential_id, name="Test Host"):
    """Helper to create a remote host and return its full response."""
    resp = client.post(
        f"{REMOTE_BASE}/hosts",
        json={
            "name": name,
            "hostname": "test.server.local",
            "ip_address": "10.0.0.1",
            "operating_system": "Ubuntu 22.04",
            "connection_type": "ssh",
            "port": 22,
            "enabled": True,
            "credential_profile_id": credential_id,
        },
    )
    assert resp.status_code == 201
    return resp.json()


# ------------------------------------------------------------------ #
# Credential Profile CRUD                                             #
# ------------------------------------------------------------------ #


def test_create_credential_profile(client):
    """Test creating a new credential profile."""
    resp = client.post(
        f"{REMOTE_BASE}/credentials",
        json={
            "name": "My SSH Key",
            "authentication_type": "ssh_key",
            "username": "admin",
            "ssh_key": "fake-key-content",
            "description": "Test credential",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "My SSH Key"
    assert data["authentication_type"] == "ssh_key"
    assert data["username"] == "admin"
    assert data["id"] is not None


def test_create_credential_duplicate_name(client):
    """Test that creating a credential with duplicate name returns 409."""
    client.post(
        f"{REMOTE_BASE}/credentials",
        json={"name": "Dup Cred", "username": "user1"},
    )
    resp = client.post(
        f"{REMOTE_BASE}/credentials",
        json={"name": "Dup Cred", "username": "user2"},
    )
    assert resp.status_code == 409


def test_list_credentials(client):
    """Test listing credential profiles."""
    _create_credential(client, "List Cred 1")
    _create_credential(client, "List Cred 2")

    resp = client.get(f"{REMOTE_BASE}/credentials")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 2


def test_get_credential_by_id(client):
    """Test retrieving a single credential profile."""
    cred_id = _create_credential(client, "Get Cred")
    resp = client.get(f"{REMOTE_BASE}/credentials/{cred_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Get Cred"


def test_get_credential_not_found(client):
    """Test retrieving a nonexistent credential returns 404."""
    resp = client.get(f"{REMOTE_BASE}/credentials/9999")
    assert resp.status_code == 404


def test_update_credential_profile(client):
    """Test updating a credential profile."""
    cred_id = _create_credential(client, "Update Cred")
    resp = client.put(
        f"{REMOTE_BASE}/credentials/{cred_id}",
        json={"name": "Updated Cred", "username": "newuser"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Cred"
    assert resp.json()["username"] == "newuser"


def test_delete_credential_profile(client):
    """Test deleting a credential profile."""
    cred_id = _create_credential(client, "Delete Cred")
    resp = client.delete(f"{REMOTE_BASE}/credentials/{cred_id}")
    assert resp.status_code == 204

    resp = client.get(f"{REMOTE_BASE}/credentials/{cred_id}")
    assert resp.status_code == 404


# ------------------------------------------------------------------ #
# Host CRUD                                                           #
# ------------------------------------------------------------------ #


def test_create_remote_host(client):
    """Test creating a new remote host."""
    cred_id = _create_credential(client)
    resp = client.post(
        f"{REMOTE_BASE}/hosts",
        json={
            "name": "Web Server",
            "hostname": "web.local",
            "connection_type": "ssh",
            "port": 22,
            "credential_profile_id": cred_id,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Web Server"
    assert data["hostname"] == "web.local"
    assert data["credential_profile_name"] == "Test Cred"


def test_create_host_invalid_connection_type(client):
    """Test that invalid connection type returns 400."""
    resp = client.post(
        f"{REMOTE_BASE}/hosts",
        json={
            "name": "Bad Host",
            "hostname": "bad.local",
            "connection_type": "telnet",
        },
    )
    assert resp.status_code == 400


def test_create_host_nonexistent_credential(client):
    """Test that invalid credential profile ID returns 404."""
    resp = client.post(
        f"{REMOTE_BASE}/hosts",
        json={
            "name": "Bad Host",
            "hostname": "bad.local",
            "credential_profile_id": 9999,
        },
    )
    assert resp.status_code == 404


def test_list_remote_hosts(client):
    """Test listing remote hosts."""
    cred_id = _create_credential(client)
    _create_host(client, cred_id, "Host A")
    _create_host(client, cred_id, "Host B")

    resp = client.get(f"{REMOTE_BASE}/hosts")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] >= 2


def test_list_hosts_with_search(client):
    """Test listing remote hosts with search filter."""
    cred_id = _create_credential(client)
    _create_host(client, cred_id, "Alpha Server")
    _create_host(client, cred_id, "Beta Server")

    resp = client.get(f"{REMOTE_BASE}/hosts?search=Alpha")
    assert resp.status_code == 200
    names = [h["name"] for h in resp.json()["items"]]
    assert "Alpha Server" in names


def test_get_host_by_id(client):
    """Test retrieving a single remote host."""
    cred_id = _create_credential(client)
    host = _create_host(client, cred_id, "Fetch Host")

    resp = client.get(f"{REMOTE_BASE}/hosts/{host['id']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Fetch Host"


def test_get_host_not_found(client):
    """Test retrieving a nonexistent host returns 404."""
    resp = client.get(f"{REMOTE_BASE}/hosts/9999")
    assert resp.status_code == 404


def test_update_remote_host(client):
    """Test updating a remote host."""
    cred_id = _create_credential(client)
    host = _create_host(client, cred_id, "Old Name")

    resp = client.put(
        f"{REMOTE_BASE}/hosts/{host['id']}",
        json={"name": "New Name", "port": 2222},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"
    assert resp.json()["port"] == 2222


def test_delete_remote_host(client):
    """Test deleting a remote host."""
    cred_id = _create_credential(client)
    host = _create_host(client, cred_id, "Delete Host")

    resp = client.delete(f"{REMOTE_BASE}/hosts/{host['id']}")
    assert resp.status_code == 204

    resp = client.get(f"{REMOTE_BASE}/hosts/{host['id']}")
    assert resp.status_code == 404


# ------------------------------------------------------------------ #
# Connection Testing                                                  #
# ------------------------------------------------------------------ #


def test_test_connection(client):
    """Test the connection test endpoint."""
    cred_id = _create_credential(client)
    host = _create_host(client, cred_id)

    mock_result = {
        "success": True,
        "latency_ms": 120,
        "message": "SSH connection to 10.0.0.1:22 successful (120ms)",
    }

    mock_provider = AsyncMock()
    mock_provider.test_connection.return_value = mock_result

    with patch(
        "app.services.remote_service.get_remote_provider",
        return_value=mock_provider,
    ):
        resp = client.post(
            f"{REMOTE_BASE}/test",
            json={"host_id": host["id"]},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["latency_ms"] == 120
    assert data["host"] == "Test Host"


def test_test_connection_disabled_host(client):
    """Test connection test on disabled host returns 400."""
    cred_id = _create_credential(client)
    host = _create_host(client, cred_id)
    client.put(f"{REMOTE_BASE}/hosts/{host['id']}", json={"enabled": False})

    resp = client.post(
        f"{REMOTE_BASE}/test",
        json={"host_id": host["id"]},
    )
    assert resp.status_code == 400


def test_test_connection_not_found(client):
    """Test connection test on nonexistent host returns 404."""
    resp = client.post(
        f"{REMOTE_BASE}/test",
        json={"host_id": 9999},
    )
    assert resp.status_code == 404


# ------------------------------------------------------------------ #
# Command Execution                                                   #
# ------------------------------------------------------------------ #


def test_execute_command(client):
    """Test command execution endpoint."""
    cred_id = _create_credential(client)
    host = _create_host(client, cred_id)

    mock_result = {
        "success": True,
        "stdout": "root\n",
        "stderr": "",
        "exit_code": 0,
        "duration_ms": 250,
    }

    mock_provider = AsyncMock()
    mock_provider.execute_command.return_value = mock_result

    with patch(
        "app.services.remote_service.get_remote_provider",
        return_value=mock_provider,
    ):
        resp = client.post(
            f"{REMOTE_BASE}/execute",
            json={"host_id": host["id"], "command": "whoami", "shell": "bash"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["exit_code"] == 0
    assert data["host"] == "Test Host"
    assert data["stdout"] == "root\n"


def test_execute_command_invalid_shell(client):
    """Test command execution with invalid shell returns 400."""
    cred_id = _create_credential(client)
    host = _create_host(client, cred_id)

    resp = client.post(
        f"{REMOTE_BASE}/execute",
        json={"host_id": host["id"], "command": "ls", "shell": "zsh"},
    )
    assert resp.status_code == 400


def test_execute_command_not_found(client):
    """Test command execution on nonexistent host returns 404."""
    resp = client.post(
        f"{REMOTE_BASE}/execute",
        json={"host_id": 9999, "command": "ls"},
    )
    assert resp.status_code == 404


def test_execute_command_recorded_in_history(client):
    """Test that executed commands appear in history."""
    cred_id = _create_credential(client)
    host = _create_host(client, cred_id)

    mock_result = {
        "success": True,
        "stdout": "root\n",
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
            json={"host_id": host["id"], "command": "whoami"},
        )

    resp = client.get(f"{REMOTE_BASE}/history")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any(i["command"] == "whoami" for i in items)


# ------------------------------------------------------------------ #
# Command History                                                     #
# ------------------------------------------------------------------ #


def test_get_history(client):
    """Test retrieving command history."""
    cred_id = _create_credential(client)
    host = _create_host(client, cred_id)

    mock_result = {
        "success": True,
        "stdout": "test.server.local\n",
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
            json={"host_id": host["id"], "command": "hostname"},
        )

    resp = client.get(f"{REMOTE_BASE}/history")
    assert resp.status_code == 200
    assert resp.json()["count"] >= 1


def test_get_history_filtered_by_search(client):
    """Test history search filter."""
    cred_id = _create_credential(client)
    host = _create_host(client, cred_id)

    mock_hostname = {
        "success": True,
        "stdout": "test.server.local\n",
        "stderr": "",
        "exit_code": 0,
        "duration_ms": 100,
    }
    mock_uptime = {
        "success": True,
        "stdout": "up 42 days\n",
        "stderr": "",
        "exit_code": 0,
        "duration_ms": 100,
    }

    mock_provider = AsyncMock()
    mock_provider.execute_command.return_value = mock_hostname

    with patch(
        "app.services.remote_service.get_remote_provider",
        return_value=mock_provider,
    ):
        client.post(
            f"{REMOTE_BASE}/execute",
            json={"host_id": host["id"], "command": "hostname"},
        )
        mock_provider.execute_command.return_value = mock_uptime
        client.post(
            f"{REMOTE_BASE}/execute",
            json={"host_id": host["id"], "command": "uptime"},
        )

    resp = client.get(f"{REMOTE_BASE}/history?search=host")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert all("host" in i["command"].lower() for i in items)


def test_get_history_filtered_by_host(client):
    """Test history host filter."""
    cred_id = _create_credential(client)
    host = _create_host(client, cred_id, "Host A")

    mock_result = {
        "success": True,
        "stdout": "ok\n",
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
            json={"host_id": host["id"], "command": "test"},
        )

    resp = client.get(f"{REMOTE_BASE}/history?host_id={host['id']}")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert all(i["host_id"] == host["id"] for i in items)


def test_get_history_filtered_by_success(client):
    """Test history success filter."""
    cred_id = _create_credential(client)
    host = _create_host(client, cred_id)

    mock_result = {
        "success": True,
        "stdout": "test.server.local\n",
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
            json={"host_id": host["id"], "command": "hostname"},
        )

    resp = client.get(f"{REMOTE_BASE}/history?success=true")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert all(i["success"] is True for i in items)


# ------------------------------------------------------------------ #
# Dashboard Remote Section                                            #
# ------------------------------------------------------------------ #


def test_dashboard_returns_remote_section(client, db_session, mock_docker):
    """Verify dashboard response includes the remote section."""
    resp = client.get("/api/v1/dashboard")
    assert resp.status_code == 200
    remote = resp.json()["remote"]
    assert "totalHosts" in remote
    assert "enabledHosts" in remote
    assert "recentCommands" in remote
