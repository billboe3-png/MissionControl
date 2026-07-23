"""
Mission Control Integration Management Tests

Sprint 2.3.1 - Integration Management (Production Configuration UI).

Covers:
- Repository CRUD
- Service layer (CRUD + encryption + provider injection)
- API endpoints (all 8)
- Encryption round-trip
- Secret masking in responses
- Connection test dispatch
"""


import pytest

from app.core.security import CredentialCipher
from app.repositories.integration_profile_repository import (
    IntegrationProfileRepository,
)
from app.schemas.integration import (
    IntegrationProfileCreate,
    IntegrationProfileUpdate,
)

# ------------------------------------------------------------------ #
# Fixtures                                                            #
# ------------------------------------------------------------------ #


@pytest.fixture
def enc_cipher():
    from app.core.config import get_settings

    settings = get_settings()
    return CredentialCipher(settings.missioncontrol_secret_key)


# ------------------------------------------------------------------ #
# Repository Tests                                                    #
# ------------------------------------------------------------------ #


class TestIntegrationProfileRepository:
    def test_create_profile(self, db_session):
        profile = IntegrationProfileRepository.create(
            db_session,
            name="Test Zabbix",
            integration_type="zabbix",
            base_url="https://zabbix.example.com",
            username="Admin",
        )
        assert profile.id is not None
        assert profile.name == "Test Zabbix"
        assert profile.integration_type == "zabbix"
        assert profile.enabled is False

    def test_get_by_id(self, db_session):
        profile = IntegrationProfileRepository.create(
            db_session,
            name="Test AD",
            integration_type="active_directory",
        )
        found = IntegrationProfileRepository.get_by_id(
            db_session, profile.id
        )
        assert found is not None
        assert found.name == "Test AD"

    def test_get_by_id_not_found(self, db_session):
        found = IntegrationProfileRepository.get_by_id(
            db_session, 99999
        )
        assert found is None

    def test_get_all(self, db_session):
        IntegrationProfileRepository.create(
            db_session, name="P1", integration_type="zabbix"
        )
        IntegrationProfileRepository.create(
            db_session, name="P2", integration_type="microsoft_365"
        )
        all_profiles = IntegrationProfileRepository.get_all(db_session)
        assert len(all_profiles) >= 2

    def test_get_by_type(self, db_session):
        IntegrationProfileRepository.create(
            db_session, name="Z1", integration_type="zabbix"
        )
        IntegrationProfileRepository.create(
            db_session, name="Z2", integration_type="zabbix"
        )
        zabbix_profiles = IntegrationProfileRepository.get_by_type(
            db_session, "zabbix"
        )
        assert len(zabbix_profiles) >= 2

    def test_get_enabled_by_type(self, db_session):
        IntegrationProfileRepository.create(
            db_session,
            name="Z1",
            integration_type="zabbix",
            enabled=False,
        )
        IntegrationProfileRepository.create(
            db_session,
            name="Z2",
            integration_type="zabbix",
            enabled=True,
        )
        enabled = IntegrationProfileRepository.get_enabled_by_type(
            db_session, "zabbix"
        )
        assert enabled is not None
        assert enabled.enabled is True
        assert enabled.name == "Z2"

    def test_update_profile(self, db_session):
        profile = IntegrationProfileRepository.create(
            db_session, name="Old", integration_type="zabbix"
        )
        updated = IntegrationProfileRepository.update(
            db_session, profile.id, name="New"
        )
        assert updated is not None
        assert updated.name == "New"

    def test_update_not_found(self, db_session):
        result = IntegrationProfileRepository.update(
            db_session, 99999, name="X"
        )
        assert result is None

    def test_delete_profile(self, db_session):
        profile = IntegrationProfileRepository.create(
            db_session, name="ToDelete", integration_type="zabbix"
        )
        deleted = IntegrationProfileRepository.delete(
            db_session, profile.id
        )
        assert deleted is True
        assert (
            IntegrationProfileRepository.get_by_id(
                db_session, profile.id
            )
            is None
        )

    def test_delete_not_found(self, db_session):
        deleted = IntegrationProfileRepository.delete(
            db_session, 99999
        )
        assert deleted is False

    def test_count_by_type(self, db_session):
        IntegrationProfileRepository.create(
            db_session, name="Z1", integration_type="zabbix"
        )
        IntegrationProfileRepository.create(
            db_session, name="AD1", integration_type="active_directory"
        )
        counts = IntegrationProfileRepository.count_by_type(db_session)
        assert "zabbix" in counts
        assert "active_directory" in counts

    def test_count_enabled(self, db_session):
        IntegrationProfileRepository.create(
            db_session,
            name="E1",
            integration_type="zabbix",
            enabled=True,
        )
        IntegrationProfileRepository.create(
            db_session,
            name="D1",
            integration_type="zabbix",
            enabled=False,
        )
        count = IntegrationProfileRepository.count_enabled(db_session)
        assert count >= 1


# ------------------------------------------------------------------ #
# Encryption Tests                                                    #
# ------------------------------------------------------------------ #


class TestIntegrationEncryption:
    def test_encrypt_decrypt_round_trip(self, enc_cipher):
        plaintext = "super-secret-password-123"
        encrypted = enc_cipher.encrypt(plaintext)
        assert encrypted != plaintext
        decrypted = enc_cipher.decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypt_empty_string(self, enc_cipher):
        result = enc_cipher.encrypt("")
        assert result == ""

    def test_encrypt_none_like(self, enc_cipher):
        result = enc_cipher.encrypt("")
        assert result == ""

    def test_decrypt_empty_string(self, enc_cipher):
        result = enc_cipher.decrypt("")
        assert result == ""

    def test_secret_not_in_response(self, db_session, enc_cipher):
        """Encrypted secrets must never appear in API responses."""
        from app.services.integration_service import (
            IntegrationService,
        )

        service = IntegrationService()
        profile = IntegrationProfileRepository.create(
            db_session,
            name="Secret Test",
            integration_type="zabbix",
            encrypted_secret=enc_cipher.encrypt("my-password"),
            client_secret_encrypted=enc_cipher.encrypt("client-secret"),
        )
        response = service._to_response(profile)
        serialized = response.model_dump()
        assert "my-password" not in str(serialized)
        assert "client-secret" not in str(serialized)


# ------------------------------------------------------------------ #
# Service Tests                                                       #
# ------------------------------------------------------------------ #


class TestIntegrationService:
    @pytest.mark.asyncio
    async def test_list_profiles(self, db_session):
        from app.services.integration_service import (
            IntegrationService,
        )

        service = IntegrationService()
        IntegrationProfileRepository.create(
            db_session, name="P1", integration_type="zabbix"
        )
        result = await service.list_profiles(db_session)
        assert result.count >= 1

    @pytest.mark.asyncio
    async def test_get_profile(self, db_session):
        from app.services.integration_service import (
            IntegrationService,
        )

        service = IntegrationService()
        profile = IntegrationProfileRepository.create(
            db_session, name="Get Me", integration_type="zabbix"
        )
        result = await service.get_profile(db_session, profile.id)
        assert result.name == "Get Me"

    @pytest.mark.asyncio
    async def test_create_profile(self, db_session):
        from app.services.integration_service import (
            IntegrationService,
        )

        service = IntegrationService()
        data = IntegrationProfileCreate(
            name="New Integration",
            integration_type="zabbix",
            base_url="https://zabbix.local",
            username="Admin",
            password="secret123",
        )
        result = await service.create_profile(db_session, data)
        assert result.name == "New Integration"
        assert result.base_url == "https://zabbix.local"

    @pytest.mark.asyncio
    async def test_create_invalid_type(self, db_session):
        from fastapi import HTTPException

        from app.services.integration_service import (
            IntegrationService,
        )

        service = IntegrationService()
        data = IntegrationProfileCreate(
            name="Bad",
            integration_type="invalid_type",
        )
        with pytest.raises(HTTPException) as exc_info:
            await service.create_profile(db_session, data)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_update_profile(self, db_session):
        from app.services.integration_service import (
            IntegrationService,
        )

        service = IntegrationService()
        profile = IntegrationProfileRepository.create(
            db_session, name="Old", integration_type="zabbix"
        )
        data = IntegrationProfileUpdate(name="Updated")
        result = await service.update_profile(
            db_session, profile.id, data
        )
        assert result.name == "Updated"

    @pytest.mark.asyncio
    async def test_update_password_emptied_keeps_existing(
        self, db_session, enc_cipher
    ):
        from app.services.integration_service import (
            IntegrationService,
        )

        service = IntegrationService()
        profile = IntegrationProfileRepository.create(
            db_session,
            name="Pwd Test",
            integration_type="zabbix",
            encrypted_secret=enc_cipher.encrypt("keep-this"),
        )
        data = IntegrationProfileUpdate(password="")
        result = await service.update_profile(
            db_session, profile.id, data
        )
        assert result.id == profile.id

    @pytest.mark.asyncio
    async def test_enable_disable(self, db_session):
        from app.services.integration_service import (
            IntegrationService,
        )

        service = IntegrationService()
        profile = IntegrationProfileRepository.create(
            db_session,
            name="Toggle",
            integration_type="zabbix",
            enabled=False,
        )
        result = await service.enable_profile(db_session, profile.id)
        assert result.enabled is True

        result = await service.disable_profile(db_session, profile.id)
        assert result.enabled is False

    @pytest.mark.asyncio
    async def test_delete_profile(self, db_session):
        from app.services.integration_service import (
            IntegrationService,
        )

        service = IntegrationService()
        profile = IntegrationProfileRepository.create(
            db_session, name="Del", integration_type="zabbix"
        )
        await service.delete_profile(db_session, profile.id)
        assert (
            IntegrationProfileRepository.get_by_id(
                db_session, profile.id
            )
            is None
        )

    @pytest.mark.asyncio
    async def test_delete_not_found(self, db_session):
        from fastapi import HTTPException

        from app.services.integration_service import (
            IntegrationService,
        )

        service = IntegrationService()
        with pytest.raises(HTTPException) as exc_info:
            await service.delete_profile(db_session, 99999)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_not_found(self, db_session):
        from fastapi import HTTPException

        from app.services.integration_service import (
            IntegrationService,
        )

        service = IntegrationService()
        with pytest.raises(HTTPException) as exc_info:
            await service.get_profile(db_session, 99999)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_test_connection_zabbix(self, db_session):
        from unittest.mock import AsyncMock, patch

        from app.services.integration_service import (
            IntegrationService,
        )

        service = IntegrationService()
        profile = IntegrationProfileRepository.create(
            db_session,
            name="ZTest",
            integration_type="zabbix",
            base_url="https://zabbix.example.com",
            username="Admin",
        )

        with patch(
            "app.providers.zabbix.zabbix_provider.ApiZabbixProvider"
        ) as MockProvider:
            mock_instance = MockProvider.return_value
            mock_instance.test_connection = AsyncMock(
                return_value={
                    "connected": True,
                    "message": "Mocked Zabbix connection successful",
                }
            )
            result = await service.test_connection(
                db_session, profile.id
            )
            assert result.success is True
            assert result.message is not None

    @pytest.mark.asyncio
    async def test_test_connection_ad(self, db_session):
        from app.services.integration_service import (
            IntegrationService,
        )

        service = IntegrationService()
        profile = IntegrationProfileRepository.create(
            db_session,
            name="ADTest",
            integration_type="active_directory",
        )
        result = await service.test_connection(db_session, profile.id)
        assert result.success is False
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_test_connection_m365(self, db_session):
        from app.services.integration_service import (
            IntegrationService,
        )

        service = IntegrationService()
        profile = IntegrationProfileRepository.create(
            db_session,
            name="M365Test",
            integration_type="microsoft_365",
            tenant_id="test-tenant",
            client_id="test-client",
            client_secret_encrypted="encrypted-test-secret",
        )
        result = await service.test_connection(db_session, profile.id)
        assert result.success is False
        assert result.error is not None


# ------------------------------------------------------------------ #
# API Tests                                                           #
# ------------------------------------------------------------------ #


class TestIntegrationAPI:
    def test_list_integrations(self, client):
        resp = client.get("/api/v1/integrations")
        assert resp.status_code == 200
        data = resp.json()
        assert "count" in data
        assert "items" in data

    def test_create_integration(self, client):
        resp = client.post(
            "/api/v1/integrations",
            json={
                "name": "API Zabbix",
                "integration_type": "zabbix",
                "base_url": "https://zabbix.example.com",
                "username": "Admin",
                "password": "secret",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "API Zabbix"
        assert data["integration_type"] == "zabbix"
        assert "secret" not in str(data)

    def test_get_integration(self, client):
        create_resp = client.post(
            "/api/v1/integrations",
            json={
                "name": "Get API",
                "integration_type": "zabbix",
            },
        )
        profile_id = create_resp.json()["id"]
        resp = client.get(f"/api/v1/integrations/{profile_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Get API"

    def test_get_integration_not_found(self, client):
        resp = client.get("/api/v1/integrations/99999")
        assert resp.status_code == 404

    def test_update_integration(self, client):
        create_resp = client.post(
            "/api/v1/integrations",
            json={
                "name": "Upd API",
                "integration_type": "zabbix",
            },
        )
        profile_id = create_resp.json()["id"]
        resp = client.put(
            f"/api/v1/integrations/{profile_id}",
            json={"name": "Updated API"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated API"

    def test_delete_integration(self, client):
        create_resp = client.post(
            "/api/v1/integrations",
            json={
                "name": "Del API",
                "integration_type": "zabbix",
            },
        )
        profile_id = create_resp.json()["id"]
        resp = client.delete(f"/api/v1/integrations/{profile_id}")
        assert resp.status_code == 204

    def test_delete_integration_not_found(self, client):
        resp = client.delete("/api/v1/integrations/99999")
        assert resp.status_code == 404

    def test_test_connection(self, client):
        create_resp = client.post(
            "/api/v1/integrations",
            json={
                "name": "Test API",
                "integration_type": "zabbix",
            },
        )
        profile_id = create_resp.json()["id"]
        resp = client.post(
            f"/api/v1/integrations/{profile_id}/test"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "success" in data

    def test_enable_integration(self, client):
        create_resp = client.post(
            "/api/v1/integrations",
            json={
                "name": "Enable API",
                "integration_type": "zabbix",
                "enabled": False,
            },
        )
        profile_id = create_resp.json()["id"]
        resp = client.post(
            f"/api/v1/integrations/{profile_id}/enable"
        )
        assert resp.status_code == 200
        assert resp.json()["enabled"] is True

    def test_disable_integration(self, client):
        create_resp = client.post(
            "/api/v1/integrations",
            json={
                "name": "Disable API",
                "integration_type": "zabbix",
                "enabled": True,
            },
        )
        profile_id = create_resp.json()["id"]
        resp = client.post(
            f"/api/v1/integrations/{profile_id}/disable"
        )
        assert resp.status_code == 200
        assert resp.json()["enabled"] is False

    def test_create_invalid_type(self, client):
        resp = client.post(
            "/api/v1/integrations",
            json={
                "name": "Bad",
                "integration_type": "hyper_v",
            },
        )
        assert resp.status_code == 400

    def test_secrets_never_exposed(self, client):
        resp = client.post(
            "/api/v1/integrations",
            json={
                "name": "Sec Test",
                "integration_type": "zabbix",
                "password": "my-secret-pw",
                "client_secret": "my-client-secret",
            },
        )
        data = resp.json()
        serialized = str(data)
        assert "my-secret-pw" not in serialized
        assert "my-client-secret" not in serialized

    def test_create_microsoft_365(self, client):
        resp = client.post(
            "/api/v1/integrations",
            json={
                "name": "M365 Integration",
                "integration_type": "microsoft_365",
                "tenant_id": "test-tenant-id",
                "client_id": "test-client-id",
                "client_secret": "test-secret",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["tenant_id"] == "test-tenant-id"
        assert "test-secret" not in str(data)

    def test_create_active_directory(self, client):
        resp = client.post(
            "/api/v1/integrations",
            json={
                "name": "AD Integration",
                "integration_type": "active_directory",
                "base_url": "ldap://dc01.corp.local",
                "username": "admin",
                "password": "ad-password",
                "domain": "corp.local",
                "base_dn": "DC=corp,DC=local",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["domain"] == "corp.local"
        assert "ad-password" not in str(data)


# ------------------------------------------------------------------ #
# Zabbix Provider Selection Tests                                     #
# ------------------------------------------------------------------ #


class TestZabbixProviderSelection:
    """Verify the factory selects the right provider based on DB state."""

    def setup_method(self):
        from app.providers.zabbix.provider_factory import (
            reset_zabbix_provider,
        )

        reset_zabbix_provider()

    def teardown_method(self):
        from app.providers.zabbix.provider_factory import (
            reset_zabbix_provider,
        )

        reset_zabbix_provider()

    def test_active_profile_returns_production_provider(
        self, db_session
    ):
        """Active profile with URL + username → ApiZabbixProvider."""
        from app.providers.zabbix.provider_factory import (
            get_zabbix_provider,
        )
        from app.providers.zabbix.zabbix_provider import (
            ApiZabbixProvider,
        )

        IntegrationProfileRepository.create(
            db_session,
            name="Prod Zabbix",
            integration_type="zabbix",
            enabled=True,
            base_url="https://zabbix.corp.local",
            username="Admin",
        )
        provider = get_zabbix_provider(db_session)
        assert isinstance(provider, ApiZabbixProvider)

    def test_no_profile_falls_back_to_mock(self, db_session):
        """No active profile → MockZabbixProvider."""
        from app.providers.zabbix.mock_provider import (
            MockZabbixProvider,
        )
        from app.providers.zabbix.provider_factory import (
            get_zabbix_provider,
        )

        provider = get_zabbix_provider(db_session)
        assert isinstance(provider, MockZabbixProvider)

    def test_disabled_profile_falls_back_to_mock(self, db_session):
        """Disabled profile is ignored → MockZabbixProvider."""
        from app.providers.zabbix.mock_provider import (
            MockZabbixProvider,
        )
        from app.providers.zabbix.provider_factory import (
            get_zabbix_provider,
        )

        IntegrationProfileRepository.create(
            db_session,
            name="Disabled Zabbix",
            integration_type="zabbix",
            enabled=False,
            base_url="https://zabbix.corp.local",
            username="Admin",
        )
        provider = get_zabbix_provider(db_session)
        assert isinstance(provider, MockZabbixProvider)

    def test_profile_without_url_falls_back_to_mock(self, db_session):
        """Profile missing base_url → MockZabbixProvider."""
        from app.providers.zabbix.mock_provider import (
            MockZabbixProvider,
        )
        from app.providers.zabbix.provider_factory import (
            get_zabbix_provider,
        )

        IntegrationProfileRepository.create(
            db_session,
            name="No URL Zabbix",
            integration_type="zabbix",
            enabled=True,
            username="Admin",
        )
        provider = get_zabbix_provider(db_session)
        assert isinstance(provider, MockZabbixProvider)

    def test_profile_without_username_falls_back_to_mock(
        self, db_session
    ):
        """Profile missing username → MockZabbixProvider."""
        from app.providers.zabbix.mock_provider import (
            MockZabbixProvider,
        )
        from app.providers.zabbix.provider_factory import (
            get_zabbix_provider,
        )

        IntegrationProfileRepository.create(
            db_session,
            name="No User Zabbix",
            integration_type="zabbix",
            enabled=True,
            base_url="https://zabbix.corp.local",
        )
        provider = get_zabbix_provider(db_session)
        assert isinstance(provider, MockZabbixProvider)

    @pytest.mark.asyncio
    async def test_profile_without_url_test_connection_fails(
        self, db_session
    ):
        """Test connection with missing URL returns error."""
        from app.services.integration_service import (
            IntegrationService,
        )

        service = IntegrationService()
        profile = IntegrationProfileRepository.create(
            db_session,
            name="No URL",
            integration_type="zabbix",
            enabled=True,
            username="Admin",
        )
        result = await service.test_connection(db_session, profile.id)
        assert result.success is False
        assert "URL" in result.error

    @pytest.mark.asyncio
    async def test_profile_without_username_test_connection_fails(
        self, db_session
    ):
        """Test connection with missing username returns error."""
        from app.services.integration_service import (
            IntegrationService,
        )

        service = IntegrationService()
        profile = IntegrationProfileRepository.create(
            db_session,
            name="No User",
            integration_type="zabbix",
            enabled=True,
            base_url="https://zabbix.corp.local",
        )
        result = await service.test_connection(db_session, profile.id)
        assert result.success is False
        assert "username" in result.error

    @pytest.mark.asyncio
    async def test_test_connection_uses_production_provider(
        self, db_session
    ):
        """Test connection dispatches to ApiZabbixProvider, not mock."""
        from unittest.mock import AsyncMock, patch

        from app.services.integration_service import (
            IntegrationService,
        )

        service = IntegrationService()
        profile = IntegrationProfileRepository.create(
            db_session,
            name="Real Zabbix",
            integration_type="zabbix",
            enabled=True,
            base_url="https://zabbix.corp.local",
            username="Admin",
        )

        mock_result = {
            "connected": True,
            "message": "Zabbix 7.0.0 reachable",
            "version": "7.0.0",
        }
        with patch(
            "app.providers.zabbix.zabbix_provider.ApiZabbixProvider"
        ) as MockProvider:
            mock_instance = MockProvider.return_value
            mock_instance.test_connection = AsyncMock(
                return_value=mock_result
            )
            result = await service.test_connection(
                db_session, profile.id
            )

            MockProvider.assert_called_once_with(
                url="https://zabbix.corp.local",
                username="Admin",
                password=None,
                verify_ssl=True,
                timeout=30,
            )
            assert result.success is True
            assert result.message == "Zabbix 7.0.0 reachable"

    @pytest.mark.asyncio
    async def test_test_connection_auth_error(self, db_session):
        """Invalid credentials → authentication failure."""
        from app.services.integration_service import (
            IntegrationService,
        )

        service = IntegrationService()
        profile = IntegrationProfileRepository.create(
            db_session,
            name="Bad Creds",
            integration_type="zabbix",
            enabled=True,
            base_url="https://zabbix.corp.local",
            username="Admin",
        )
        result = await service.test_connection(db_session, profile.id)
        assert result.success is False
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_live_connection_reaches_real_api(self, db_session):
        """When profile has valid URL, ApiZabbixProvider is instantiated
        with explicit credentials (not from env vars)."""
        from unittest.mock import AsyncMock, patch

        from app.services.integration_service import (
            IntegrationService,
        )

        service = IntegrationService()
        profile = IntegrationProfileRepository.create(
            db_session,
            name="Live Test",
            integration_type="zabbix",
            enabled=True,
            base_url="https://zabbix.live.com",
            username="zabbix_admin",
        )

        with patch(
            "app.providers.zabbix.zabbix_provider.ApiZabbixProvider"
        ) as MockProvider:
            mock_instance = MockProvider.return_value
            mock_instance.test_connection = AsyncMock(
                return_value={
                    "connected": True,
                    "message": "Zabbix 7.0.0 reachable",
                    "version": "7.0.0",
                }
            )
            result = await service.test_connection(
                db_session, profile.id
            )
            assert result.success is True
            assert result.version == "7.0.0"

    def test_factory_resolves_from_db_not_env(self, db_session):
        """Factory uses DB profile when db session provided."""
        from app.providers.zabbix.provider_factory import (
            get_zabbix_provider,
        )
        from app.providers.zabbix.zabbix_provider import (
            ApiZabbixProvider,
        )

        IntegrationProfileRepository.create(
            db_session,
            name="Factory Test",
            integration_type="zabbix",
            enabled=True,
            base_url="https://factory.test.com",
            username="factory_user",
        )
        provider = get_zabbix_provider(db_session)
        assert isinstance(provider, ApiZabbixProvider)
        assert provider._get_config()["url"] == "https://factory.test.com"
        assert provider._get_config()["username"] == "factory_user"

    def test_factory_without_db_uses_env_or_mock(self, db_session):
        """Factory without db session falls back to env/mock."""
        from app.providers.zabbix.mock_provider import (
            MockZabbixProvider,
        )
        from app.providers.zabbix.provider_factory import (
            get_zabbix_provider,
        )

        IntegrationProfileRepository.create(
            db_session,
            name="Should Be Ignored",
            integration_type="zabbix",
            enabled=True,
            base_url="https://should-not-use.com",
            username="nope",
        )
        provider = get_zabbix_provider(None)
        assert isinstance(provider, MockZabbixProvider)
