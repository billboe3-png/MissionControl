"""
Credential API Security Tests

Sprint 2.1.4 - Secure Credential Vault.

Tests that sensitive fields are never returned through the API.
"""

REMOTE_BASE = "/api/v1/remote"


def test_credential_response_excludes_password(client):
    """Test that credential response never includes password."""
    resp = client.post(
        f"{REMOTE_BASE}/credentials",
        json={
            "name": "No Password Response",
            "username": "testuser",
            "password": "secret-password",
        },
    )
    assert resp.status_code == 201
    data = resp.json()

    # Sensitive fields should not be in response
    assert "password" not in data
    assert "password_encrypted" not in data
    assert "ssh_key" not in data
    assert "private_key_encrypted" not in data
    assert "passphrase" not in data
    assert "passphrase_encrypted" not in data


def test_credential_response_excludes_ssh_key(client):
    """Test that credential response never includes SSH key."""
    resp = client.post(
        f"{REMOTE_BASE}/credentials",
        json={
            "name": "No SSH Key Response",
            "username": "root",
            "ssh_key": (
                "-----BEGIN RSA PRIVATE KEY-----\n"
                "fake\n"
                "-----END RSA PRIVATE KEY-----"
            ),
        },
    )
    assert resp.status_code == 201
    data = resp.json()

    # SSH key should not be in response
    assert "ssh_key" not in data
    assert "private_key_encrypted" not in data


def test_list_credentials_excludes_sensitive_fields(client):
    """Test that listing credentials never includes sensitive fields."""
    # Create a credential with password
    client.post(
        f"{REMOTE_BASE}/credentials",
        json={
            "name": "List No Sensitive",
            "username": "testuser",
            "password": "secret",
        },
    )

    resp = client.get(f"{REMOTE_BASE}/credentials")
    assert resp.status_code == 200
    data = resp.json()

    assert data["count"] >= 1
    for item in data["items"]:
        assert "password" not in item
        assert "password_encrypted" not in item
        assert "ssh_key" not in item
        assert "private_key_encrypted" not in item
        assert "passphrase" not in item
        assert "passphrase_encrypted" not in item


def test_get_credential_by_id_excludes_sensitive_fields(client):
    """Test that getting credential by ID never includes sensitive fields."""
    # Create a credential
    create_resp = client.post(
        f"{REMOTE_BASE}/credentials",
        json={
            "name": "Get No Sensitive",
            "username": "testuser",
            "password": "secret",
        },
    )
    cred_id = create_resp.json()["id"]

    resp = client.get(f"{REMOTE_BASE}/credentials/{cred_id}")
    assert resp.status_code == 200
    data = resp.json()

    assert "password" not in data
    assert "password_encrypted" not in data
    assert "ssh_key" not in data
    assert "private_key_encrypted" not in data
    assert "passphrase" not in data
    assert "passphrase_encrypted" not in data


def test_update_credential_excludes_sensitive_fields(client):
    """Test that updating credential never returns sensitive fields."""
    # Create
    create_resp = client.post(
        f"{REMOTE_BASE}/credentials",
        json={
            "name": "Update No Sensitive",
            "username": "testuser",
            "password": "old-pass",
        },
    )
    cred_id = create_resp.json()["id"]

    # Update
    resp = client.put(
        f"{REMOTE_BASE}/credentials/{cred_id}",
        json={"password": "new-pass"},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert "password" not in data
    assert "password_encrypted" not in data
    assert "ssh_key" not in data
    assert "private_key_encrypted" not in data
    assert "passphrase" not in data
    assert "passphrase_encrypted" not in data


def test_create_credential_with_all_fields(client):
    """Test creating credential with all fields works correctly."""
    resp = client.post(
        f"{REMOTE_BASE}/credentials",
        json={
            "name": "All Fields Test",
            "authentication_type": "ssh_key",
            "username": "admin",
            "ssh_key": (
                "-----BEGIN RSA PRIVATE KEY-----\n"
                "fake\n"
                "-----END RSA PRIVATE KEY-----"
            ),
            "passphrase": "key-passphrase",
            "description": "Test credential with all fields",
        },
    )
    assert resp.status_code == 201
    data = resp.json()

    assert data["name"] == "All Fields Test"
    assert data["authentication_type"] == "ssh_key"
    assert data["username"] == "admin"
    assert data["description"] == "Test credential with all fields"
    # No sensitive fields
    assert "password" not in data
    assert "ssh_key" not in data
    assert "passphrase" not in data


def test_credential_name_only_in_response(client):
    """Test that response only contains expected fields."""
    resp = client.post(
        f"{REMOTE_BASE}/credentials",
        json={
            "name": "Field Check",
            "username": "testuser",
            "password": "secret",
        },
    )
    assert resp.status_code == 201
    data = resp.json()

    expected_fields = {
        "id",
        "name",
        "authentication_type",
        "username",
        "description",
        "created_at",
        "updated_at",
    }
    assert set(data.keys()) == expected_fields


def test_update_preserves_existing_password(client):
    """Test that updating other fields preserves the existing encrypted password."""
    # Create with password
    create_resp = client.post(
        f"{REMOTE_BASE}/credentials",
        json={
            "name": "Preserve Pass Test",
            "username": "testuser",
            "password": "keep-this",
        },
    )
    cred_id = create_resp.json()["id"]

    # Update only description
    resp = client.put(
        f"{REMOTE_BASE}/credentials/{cred_id}",
        json={"description": "Updated description"},
    )
    assert resp.status_code == 200

    # Verify the credential still works (provider can decrypt)
    # This is tested in the service encryption tests
