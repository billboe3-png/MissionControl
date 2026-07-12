"""
Credential Profile Repository Tests
"""

from app.repositories.credential_profile_repository import CredentialProfileRepository
from app.schemas.credential_profile import CredentialProfileCreate
from app.schemas.credential_profile import CredentialProfileUpdate


def test_create_credential_profile(db_session):
    """Test creating a new credential profile."""
    data = CredentialProfileCreate(
        name="Production SSH",
        authentication_type="ssh_key",
        username="admin",
        ssh_key="fake-private-key",
        description="Production server access",
    )
    profile = CredentialProfileRepository.create(db_session, data)

    assert profile.id is not None
    assert profile.name == "Production SSH"
    assert profile.authentication_type == "ssh_key"
    assert profile.username == "admin"
    assert profile.ssh_key == "fake-private-key"
    assert profile.description == "Production server access"


def test_get_credential_profile_by_id(db_session, sample_credential):
    """Test retrieving a credential profile by ID."""
    found = CredentialProfileRepository.get_by_id(db_session, sample_credential.id)

    assert found is not None
    assert found.id == sample_credential.id
    assert found.name == "Test SSH Key"


def test_get_credential_profile_by_id_not_found(db_session):
    """Test that None is returned for a nonexistent ID."""
    found = CredentialProfileRepository.get_by_id(db_session, 9999)
    assert found is None


def test_get_credential_profile_by_name(db_session, sample_credential):
    """Test retrieving a credential profile by name (case-insensitive)."""
    found = CredentialProfileRepository.get_by_name(db_session, "test ssh key")
    assert found is not None
    assert found.id == sample_credential.id


def test_get_credential_profile_by_name_not_found(db_session):
    """Test that None is returned for a nonexistent name."""
    found = CredentialProfileRepository.get_by_name(db_session, "nonexistent")
    assert found is None


def test_get_all_credential_profiles(db_session, sample_credential):
    """Test retrieving all credential profiles."""
    profiles = CredentialProfileRepository.get_all(db_session)
    assert len(profiles) >= 1
    assert any(p.id == sample_credential.id for p in profiles)


def test_update_credential_profile(db_session, sample_credential):
    """Test updating a credential profile."""
    data = CredentialProfileUpdate(name="Updated Key", username="newuser")
    updated = CredentialProfileRepository.update(db_session, sample_credential.id, data)

    assert updated is not None
    assert updated.name == "Updated Key"
    assert updated.username == "newuser"
    assert updated.ssh_key == "fake-key-content"


def test_update_credential_profile_not_found(db_session):
    """Test updating a nonexistent profile returns None."""
    data = CredentialProfileUpdate(name="Ghost")
    result = CredentialProfileRepository.update(db_session, 9999, data)
    assert result is None


def test_delete_credential_profile(db_session, sample_credential):
    """Test deleting a credential profile."""
    deleted = CredentialProfileRepository.delete(db_session, sample_credential.id)
    assert deleted is True

    found = CredentialProfileRepository.get_by_id(db_session, sample_credential.id)
    assert found is None


def test_delete_credential_profile_not_found(db_session):
    """Test deleting a nonexistent profile returns False."""
    deleted = CredentialProfileRepository.delete(db_session, 9999)
    assert deleted is False


def test_get_count(db_session, sample_credential):
    """Test counting credential profiles."""
    count = CredentialProfileRepository.get_count(db_session)
    assert count >= 1
