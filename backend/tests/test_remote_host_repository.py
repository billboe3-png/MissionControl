"""
Remote Host Repository Tests
"""

from app.repositories.remote_host_repository import RemoteHostRepository
from app.schemas.remote_host import RemoteHostCreate, RemoteHostUpdate


def test_create_remote_host(db_session, sample_credential):
    """Test creating a new remote host."""
    data = RemoteHostCreate(
        name="New Server",
        hostname="new.server.local",
        ip_address="10.0.0.2",
        connection_type="ssh",
        port=22,
        enabled=True,
        credential_profile_id=sample_credential.id,
    )
    host = RemoteHostRepository.create(db_session, data)

    assert host.id is not None
    assert host.name == "New Server"
    assert host.hostname == "new.server.local"
    assert host.ip_address == "10.0.0.2"
    assert host.connection_type == "ssh"
    assert host.port == 22
    assert host.enabled is True
    assert host.credential_profile_id == sample_credential.id


def test_get_remote_host_by_id(db_session, sample_host):
    """Test retrieving a remote host by ID."""
    found = RemoteHostRepository.get_by_id(db_session, sample_host.id)

    assert found is not None
    assert found.id == sample_host.id
    assert found.name == "Test Server"
    assert found.hostname == "test.server.local"


def test_get_remote_host_by_id_not_found(db_session):
    """Test that None is returned for a nonexistent ID."""
    found = RemoteHostRepository.get_by_id(db_session, 9999)
    assert found is None


def test_get_all_remote_hosts(db_session, sample_host):
    """Test retrieving all remote hosts."""
    hosts = RemoteHostRepository.get_all(db_session)
    assert len(hosts) >= 1
    assert any(h.id == sample_host.id for h in hosts)


def test_update_remote_host(db_session, sample_host):
    """Test updating a remote host."""
    data = RemoteHostUpdate(name="Updated Server", port=2222)
    updated = RemoteHostRepository.update(db_session, sample_host.id, data)

    assert updated is not None
    assert updated.name == "Updated Server"
    assert updated.port == 2222
    assert updated.hostname == "test.server.local"


def test_update_remote_host_not_found(db_session):
    """Test updating a nonexistent host returns None."""
    data = RemoteHostUpdate(name="Ghost")
    result = RemoteHostRepository.update(db_session, 9999, data)
    assert result is None


def test_delete_remote_host(db_session, sample_host):
    """Test deleting a remote host."""
    deleted = RemoteHostRepository.delete(db_session, sample_host.id)
    assert deleted is True

    found = RemoteHostRepository.get_by_id(db_session, sample_host.id)
    assert found is None


def test_delete_remote_host_not_found(db_session):
    """Test deleting a nonexistent host returns False."""
    deleted = RemoteHostRepository.delete(db_session, 9999)
    assert deleted is False


def test_search_remote_hosts(db_session, sample_host):
    """Test searching remote hosts by name."""
    results = RemoteHostRepository.search(db_session, "Test")
    assert len(results) >= 1
    assert any(h.id == sample_host.id for h in results)


def test_search_remote_hosts_by_hostname(db_session, sample_host):
    """Test searching remote hosts by hostname."""
    results = RemoteHostRepository.search(db_session, "test.server")
    assert len(results) >= 1


def test_count_by_status(db_session, sample_host, sample_disabled_host):
    """Test counting hosts by enabled/disabled status."""
    counts = RemoteHostRepository.count_by_status(db_session)
    assert counts["enabled"] >= 1
    assert counts["disabled"] >= 1


def test_attach_credential_names(db_session, sample_host, sample_credential):
    """Test enriching hosts with credential profile names."""
    enriched = RemoteHostRepository.attach_credential_names(db_session, [sample_host])
    assert len(enriched) == 1
    assert enriched[0]["credential_profile_name"] == "Test SSH Key"
    assert enriched[0]["credential_profile_id"] == sample_credential.id
