"""
Remote Service Encryption Tests

Sprint 2.1.4 - Secure Credential Vault.

Tests that the service layer properly encrypts credentials at rest
and decrypts them before passing to providers.
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.core.security import CredentialCipher
from app.repositories.credential_profile_repository import (
    CredentialProfileRepository,
)
from app.schemas.credential_profile import (
    CredentialProfileCreate,
    CredentialProfileUpdate,
)


@pytest.mark.asyncio
class TestServiceEncryption:
    """Tests for credential encryption in the service layer."""

    async def test_create_credential_encrypts_password(
        self, db_session, mock_secret_key
    ):
        """Test that creating a credential encrypts the password."""
        from app.services.remote_service import RemoteService

        service = RemoteService()

        data = CredentialProfileCreate(
            name="Encrypted Password Test",
            authentication_type="password",
            username="testuser",
            password="my-secret-password",
        )

        result = await service.create_credential(db_session, data)

        # Verify database has encrypted value
        profile = CredentialProfileRepository.get_by_id(
            db_session, result.id
        )
        assert profile.password_encrypted is not None
        assert profile.password_encrypted != "my-secret-password"

        # Verify we can decrypt it
        cipher = CredentialCipher(mock_secret_key)
        decrypted = cipher.decrypt(profile.password_encrypted)
        assert decrypted == "my-secret-password"

    async def test_create_credential_encrypts_ssh_key(
        self, db_session, mock_secret_key
    ):
        """Test that creating a credential encrypts the SSH key."""
        from app.services.remote_service import RemoteService

        service = RemoteService()

        data = CredentialProfileCreate(
            name="Encrypted SSH Key Test",
            authentication_type="ssh_key",
            username="root",
            ssh_key=(
                "-----BEGIN RSA PRIVATE KEY-----\n"
                "fake-key\n"
                "-----END RSA PRIVATE KEY-----"
            ),
        )

        result = await service.create_credential(db_session, data)

        # Verify database has encrypted value
        profile = CredentialProfileRepository.get_by_id(
            db_session, result.id
        )
        assert profile.private_key_encrypted is not None
        assert profile.private_key_encrypted != data.ssh_key

        # Verify we can decrypt it
        cipher = CredentialCipher(mock_secret_key)
        decrypted = cipher.decrypt(profile.private_key_encrypted)
        assert decrypted == data.ssh_key

    async def test_create_credential_encrypts_passphrase(
        self, db_session, mock_secret_key
    ):
        """Test that creating a credential encrypts the passphrase."""
        from app.services.remote_service import RemoteService

        service = RemoteService()

        data = CredentialProfileCreate(
            name="Encrypted Passphrase Test",
            authentication_type="ssh_key",
            username="root",
            ssh_key=(
                "-----BEGIN RSA PRIVATE KEY-----\n"
                "fake-key\n"
                "-----END RSA PRIVATE KEY-----"
            ),
            passphrase="my-passphrase",
        )

        result = await service.create_credential(db_session, data)

        # Verify database has encrypted value
        profile = CredentialProfileRepository.get_by_id(
            db_session, result.id
        )
        assert profile.passphrase_encrypted is not None
        assert profile.passphrase_encrypted != "my-passphrase"

        # Verify we can decrypt it
        cipher = CredentialCipher(mock_secret_key)
        decrypted = cipher.decrypt(profile.passphrase_encrypted)
        assert decrypted == "my-passphrase"

    async def test_update_password_replaces_encrypted_value(
        self, db_session, mock_secret_key
    ):
        """Test that updating password replaces the encrypted value."""
        from app.services.remote_service import RemoteService

        service = RemoteService()

        data = CredentialProfileCreate(
            name="Update Password Test",
            authentication_type="password",
            username="testuser",
            password="old-password",
        )
        created = await service.create_credential(db_session, data)

        update_data = CredentialProfileUpdate(password="new-password")
        await service.update_credential(
            db_session, created.id, update_data
        )

        profile = CredentialProfileRepository.get_by_id(
            db_session, created.id
        )
        cipher = CredentialCipher(mock_secret_key)
        decrypted = cipher.decrypt(profile.password_encrypted)
        assert decrypted == "new-password"

    async def test_update_empty_password_preserves_existing(
        self, db_session, mock_secret_key
    ):
        """Test that updating with empty string preserves existing password."""
        from app.services.remote_service import RemoteService

        service = RemoteService()

        data = CredentialProfileCreate(
            name="Preserve Password Test",
            authentication_type="password",
            username="testuser",
            password="keep-this-password",
        )
        created = await service.create_credential(db_session, data)

        original_profile = CredentialProfileRepository.get_by_id(
            db_session, created.id
        )
        original_encrypted = original_profile.password_encrypted

        update_data = CredentialProfileUpdate(password="")
        await service.update_credential(
            db_session, created.id, update_data
        )

        profile = CredentialProfileRepository.get_by_id(
            db_session, created.id
        )
        assert profile.password_encrypted == original_encrypted

    async def test_provider_receives_decrypted_password(
        self, db_session, mock_secret_key
    ):
        """Test that providers receive decrypted credentials."""
        from app.repositories.remote_host_repository import (
            RemoteHostRepository,
        )
        from app.schemas.remote_command import RemoteTestConnectionRequest
        from app.schemas.remote_host import RemoteHostCreate
        from app.services.remote_service import RemoteService

        service = RemoteService()

        cred_data = CredentialProfileCreate(
            name="Provider Decryption Test",
            authentication_type="password",
            username="testuser",
            password="plaintext-password",
        )
        cred = await service.create_credential(db_session, cred_data)

        host_data = RemoteHostCreate(
            name="Test Host",
            hostname="test.local",
            connection_type="ssh",
            port=22,
            credential_profile_id=cred.id,
        )
        host = RemoteHostRepository.create(db_session, host_data)

        mock_provider = AsyncMock()
        mock_provider.test_connection.return_value = {
            "success": True,
            "latency_ms": 100,
            "message": "OK",
        }

        with patch(
            "app.services.remote_service.get_remote_provider",
            return_value=mock_provider,
        ):
            request = RemoteTestConnectionRequest(host_id=host.id)
            await service.test_connection(db_session, request)

        mock_provider.test_connection.assert_called_once()
        call_kwargs = mock_provider.test_connection.call_args[1]
        assert call_kwargs["password"] == "plaintext-password"
        assert call_kwargs["username"] == "testuser"

    async def test_provider_receives_decrypted_ssh_key(
        self, db_session, mock_secret_key
    ):
        """Test that providers receive decrypted SSH keys."""
        from app.repositories.remote_host_repository import (
            RemoteHostRepository,
        )
        from app.schemas.remote_command import RemoteTestConnectionRequest
        from app.schemas.remote_host import RemoteHostCreate
        from app.services.remote_service import RemoteService

        service = RemoteService()

        ssh_key_content = (
            "-----BEGIN RSA PRIVATE KEY-----\n"
            "fake\n"
            "-----END RSA PRIVATE KEY-----"
        )
        cred_data = CredentialProfileCreate(
            name="Provider SSH Key Test",
            authentication_type="ssh_key",
            username="root",
            ssh_key=ssh_key_content,
        )
        cred = await service.create_credential(db_session, cred_data)

        host_data = RemoteHostCreate(
            name="SSH Host",
            hostname="ssh.local",
            connection_type="ssh",
            credential_profile_id=cred.id,
        )
        host = RemoteHostRepository.create(db_session, host_data)

        mock_provider = AsyncMock()
        mock_provider.test_connection.return_value = {
            "success": True,
            "latency_ms": 50,
            "message": "OK",
        }

        with patch(
            "app.services.remote_service.get_remote_provider",
            return_value=mock_provider,
        ):
            request = RemoteTestConnectionRequest(host_id=host.id)
            await service.test_connection(db_session, request)

        call_kwargs = mock_provider.test_connection.call_args[1]
        assert call_kwargs["ssh_key"] == ssh_key_content
        assert call_kwargs["password"] is None

    async def test_plaintext_never_stored_in_database(
        self, db_session, mock_secret_key
    ):
        """Test that plaintext passwords are never stored in the database."""
        from sqlalchemy import text

        from app.services.remote_service import RemoteService

        service = RemoteService()

        data = CredentialProfileCreate(
            name="No Plaintext Test",
            authentication_type="password",
            username="testuser",
            password="super-secret",
        )
        await service.create_credential(db_session, data)

        result = db_session.execute(
            text(
                "SELECT password, password_encrypted "
                "FROM credential_profiles "
                "WHERE name = 'No Plaintext Test'"
            )
        )
        row = result.fetchone()

        assert row[0] is None
        assert row[1] is not None
        assert row[1] != "super-secret"

    async def test_create_credential_without_password(
        self, db_session, mock_secret_key
    ):
        """Test creating credential without password sets encrypted to None."""
        from app.services.remote_service import RemoteService

        service = RemoteService()

        data = CredentialProfileCreate(
            name="No Password Test",
            authentication_type="ssh_key",
            username="root",
        )
        result = await service.create_credential(db_session, data)

        profile = CredentialProfileRepository.get_by_id(
            db_session, result.id
        )
        assert profile.password_encrypted is None

    async def test_key_version_defaults_to_one(
        self, db_session, mock_secret_key
    ):
        """Test that key_version defaults to 1."""
        from app.services.remote_service import RemoteService

        service = RemoteService()

        data = CredentialProfileCreate(
            name="Key Version Test",
            authentication_type="password",
            username="testuser",
            password="test",
        )
        created = await service.create_credential(db_session, data)

        profile = CredentialProfileRepository.get_by_id(
            db_session, created.id
        )
        assert profile.key_version == 1
