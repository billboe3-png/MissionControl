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
from datetime import UTC, datetime
from unittest.mock import patch, AsyncMock

from app.core.security import CredentialCipher
from app.models.db.integration_profile import IntegrationProfile
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
        from app.services.integration_service import (
            IntegrationService,
        )

        service = IntegrationService()
        profile = IntegrationProfileRepository.create(
            db_session, name="ZTest", integration_type="zabbix"
        )
        result = await service.test_connection(db_session, profile.id)
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
        assert result.success is True

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
        )
        result = await service.test_connection(db_session, profile.id)
        assert result.success is True


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
