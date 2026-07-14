"""
Mission Control Identity Service Tests

Tests for IdentityService business logic layer.
Validates service correctly delegates to providers.

Sprint 2.2.0 - Microsoft 365 & Active Directory Integration.
"""

import pytest

from app.providers.identity.provider_factory import reset_providers
from app.services.identity_service import IdentityService


class TestIdentityServiceAD:
    """Tests for IdentityService AD operations."""

    @pytest.fixture()
    def service(self) -> IdentityService:
        reset_providers()
        return IdentityService()

    @pytest.mark.anyio()
    async def test_ad_test_connection(self, service: IdentityService) -> None:
        result = await service.ad_test_connection()
        assert "connected" in result
        assert result["connected"] is True

    @pytest.mark.anyio()
    async def test_ad_get_summary(self, service: IdentityService) -> None:
        result = await service.ad_get_summary()
        assert "connected" in result
        assert result["connected"] is True
        assert "domain" in result

    @pytest.mark.anyio()
    async def test_ad_get_users(self, service: IdentityService) -> None:
        result = await service.ad_get_users()
        assert "connected" in result
        assert result["connected"] is True
        assert "users" in result
        assert "total_count" in result

    @pytest.mark.anyio()
    async def test_ad_get_groups(self, service: IdentityService) -> None:
        result = await service.ad_get_groups()
        assert "connected" in result
        assert result["connected"] is True
        assert "groups" in result

    @pytest.mark.anyio()
    async def test_ad_get_devices(self, service: IdentityService) -> None:
        result = await service.ad_get_devices()
        assert "connected" in result
        assert result["connected"] is True
        assert "devices" in result

    @pytest.mark.anyio()
    async def test_ad_get_health(self, service: IdentityService) -> None:
        result = await service.ad_get_health()
        assert "connected" in result
        assert result["connected"] is True
        assert "status" in result


class TestIdentityServiceM365:
    """Tests for IdentityService M365 operations."""

    @pytest.fixture()
    def service(self) -> IdentityService:
        reset_providers()
        return IdentityService()

    @pytest.mark.anyio()
    async def test_m365_test_connection(self, service: IdentityService) -> None:
        result = await service.m365_test_connection()
        assert "connected" in result
        assert result["connected"] is True

    @pytest.mark.anyio()
    async def test_m365_get_summary(self, service: IdentityService) -> None:
        result = await service.m365_get_summary()
        assert "connected" in result
        assert result["connected"] is True
        assert "tenant" in result

    @pytest.mark.anyio()
    async def test_m365_get_users(self, service: IdentityService) -> None:
        result = await service.m365_get_users()
        assert "connected" in result
        assert result["connected"] is True
        assert "users" in result

    @pytest.mark.anyio()
    async def test_m365_get_groups(self, service: IdentityService) -> None:
        result = await service.m365_get_groups()
        assert "connected" in result
        assert result["connected"] is True
        assert "groups" in result

    @pytest.mark.anyio()
    async def test_m365_get_devices(self, service: IdentityService) -> None:
        result = await service.m365_get_devices()
        assert "connected" in result
        assert result["connected"] is True
        assert "devices" in result

    @pytest.mark.anyio()
    async def test_m365_get_health(self, service: IdentityService) -> None:
        result = await service.m365_get_health()
        assert "connected" in result
        assert result["connected"] is True
        assert "status" in result


class TestIdentityServiceOverview:
    """Tests for IdentityService combined overview."""

    @pytest.fixture()
    def service(self) -> IdentityService:
        reset_providers()
        return IdentityService()

    @pytest.mark.anyio()
    async def test_overview_returns_success(self, service: IdentityService) -> None:
        result = await service.get_overview()
        assert result["success"] is True

    @pytest.mark.anyio()
    async def test_overview_has_ad_section(self, service: IdentityService) -> None:
        result = await service.get_overview()
        overview = result["overview"]
        assert "ad" in overview

    @pytest.mark.anyio()
    async def test_overview_has_m365_section(self, service: IdentityService) -> None:
        result = await service.get_overview()
        overview = result["overview"]
        assert "m365" in overview

    @pytest.mark.anyio()
    async def test_overview_ad_has_connected(self, service: IdentityService) -> None:
        result = await service.get_overview()
        ad = result["overview"]["ad"]
        assert "connected" in ad

    @pytest.mark.anyio()
    async def test_overview_m365_has_connected(self, service: IdentityService) -> None:
        result = await service.get_overview()
        m365 = result["overview"]["m365"]
        assert "connected" in m365
