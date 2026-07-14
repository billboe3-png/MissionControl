"""
Mission Control Identity Service Tests

Tests for IdentityService business logic layer.
Validates service correctly delegates to providers.

Sprint 2.2.1 - Identity Platform Foundation.
"""

import pytest

from app.services.identity_service import IdentityService


class TestIdentityServiceAD:
    """Tests for IdentityService AD operations."""

    @pytest.fixture()
    def service(self) -> IdentityService:
        return IdentityService()

    @pytest.mark.anyio()
    async def test_get_domain_controllers(self, service: IdentityService) -> None:
        result = await service.get_domain_controllers()
        assert result["success"] is True
        assert "domain_controllers" in result

    @pytest.mark.anyio()
    async def test_get_forest(self, service: IdentityService) -> None:
        result = await service.get_forest()
        assert result["success"] is True
        assert "forest" in result

    @pytest.mark.anyio()
    async def test_get_domain(self, service: IdentityService) -> None:
        result = await service.get_domain()
        assert result["success"] is True
        assert "domain" in result

    @pytest.mark.anyio()
    async def test_get_organizational_units(self, service: IdentityService) -> None:
        result = await service.get_organizational_units()
        assert result["success"] is True
        assert "organizational_units" in result

    @pytest.mark.anyio()
    async def test_get_users(self, service: IdentityService) -> None:
        result = await service.get_users()
        assert result["success"] is True
        assert "users" in result
        assert "total_count" in result

    @pytest.mark.anyio()
    async def test_get_groups(self, service: IdentityService) -> None:
        result = await service.get_groups()
        assert result["success"] is True
        assert "groups" in result

    @pytest.mark.anyio()
    async def test_get_computers(self, service: IdentityService) -> None:
        result = await service.get_computers()
        assert result["success"] is True
        assert "computers" in result

    @pytest.mark.anyio()
    async def test_get_gpos(self, service: IdentityService) -> None:
        result = await service.get_gpos()
        assert result["success"] is True
        assert "gpos" in result

    @pytest.mark.anyio()
    async def test_get_fsmo_roles(self, service: IdentityService) -> None:
        result = await service.get_fsmo_roles()
        assert result["success"] is True
        assert "forest_roles" in result
        assert "domain_roles" in result

    @pytest.mark.anyio()
    async def test_get_dns_health(self, service: IdentityService) -> None:
        result = await service.get_dns_health()
        assert result["success"] is True
        assert "dns_health" in result

    @pytest.mark.anyio()
    async def test_get_dhcp_health(self, service: IdentityService) -> None:
        result = await service.get_dhcp_health()
        assert result["success"] is True
        assert "dhcp_health" in result


class TestIdentityServiceM365:
    """Tests for IdentityService M365 operations."""

    @pytest.fixture()
    def service(self) -> IdentityService:
        return IdentityService()

    @pytest.mark.anyio()
    async def test_get_tenant(self, service: IdentityService) -> None:
        result = await service.get_tenant()
        assert result["success"] is True
        assert "tenant" in result

    @pytest.mark.anyio()
    async def test_get_licenses(self, service: IdentityService) -> None:
        result = await service.get_licenses()
        assert result["success"] is True
        assert "licenses" in result

    @pytest.mark.anyio()
    async def test_get_service_health(self, service: IdentityService) -> None:
        result = await service.get_service_health()
        assert result["success"] is True
        assert "service_health" in result

    @pytest.mark.anyio()
    async def test_get_entra_health(self, service: IdentityService) -> None:
        result = await service.get_entra_health()
        assert result["success"] is True
        assert "entra_health" in result

    @pytest.mark.anyio()
    async def test_get_exchange_health(self, service: IdentityService) -> None:
        result = await service.get_exchange_health()
        assert result["success"] is True
        assert "exchange_health" in result

    @pytest.mark.anyio()
    async def test_get_secure_score(self, service: IdentityService) -> None:
        result = await service.get_secure_score()
        assert result["success"] is True
        assert "secure_score" in result

    @pytest.mark.anyio()
    async def test_get_message_center(self, service: IdentityService) -> None:
        result = await service.get_message_center()
        mc = result.get("message_center", result)
        assert "items" in mc
        assert isinstance(mc["items"], list)


class TestIdentityServiceOverview:
    """Tests for IdentityService combined overview."""

    @pytest.fixture()
    def service(self) -> IdentityService:
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
    async def test_overview_ad_has_counts(self, service: IdentityService) -> None:
        result = await service.get_overview()
        ad = result["overview"]["ad"]
        assert "domain_controllers" in ad
        assert "total_users" in ad
        assert "total_computers" in ad
        assert "total_groups" in ad
        assert "total_gpos" in ad

    @pytest.mark.anyio()
    async def test_overview_m365_has_counts(self, service: IdentityService) -> None:
        result = await service.get_overview()
        m365 = result["overview"]["m365"]
        assert "total_users" in m365
        assert "licensed_users" in m365
        assert "overall_status" in m365
        assert "secure_score" in m365
