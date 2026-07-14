"""
Mission Control Identity API Tests

Integration tests for /api/v1/identity endpoints.
Validates all endpoints return correct response shapes.

Sprint 2.2.1 - Identity Platform Foundation.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture()
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as c:
        yield c


# ------------------------------------------------------------------ #
# Overview Endpoint                                                   #
# ------------------------------------------------------------------ #


class TestIdentityOverviewAPI:
    """Tests for GET /api/v1/identity/overview."""

    @pytest.mark.anyio()
    async def test_overview_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/overview")
        assert response.status_code == 200

    @pytest.mark.anyio()
    async def test_overview_has_ad_fields(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/overview")
        data = response.json()
        assert "ad_domain_controllers" in data
        assert "ad_users_total" in data
        assert "ad_computers_total" in data
        assert "ad_groups_total" in data
        assert "ad_gpos_total" in data

    @pytest.mark.anyio()
    async def test_overview_has_m365_fields(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/overview")
        data = response.json()
        assert "m365_total_users" in data
        assert "m365_licensed_users" in data
        assert "m365_overall_status" in data
        assert "m365_active_incidents" in data
        assert "m365_secure_score" in data


# ------------------------------------------------------------------ #
# Active Directory Endpoints                                          #
# ------------------------------------------------------------------ #


class TestADDomainControllersAPI:
    """Tests for GET /api/v1/identity/ad/domain-controllers."""

    @pytest.mark.anyio()
    async def test_returns_200(self, client: AsyncClient) -> None:
        response = await client.get(
            "/api/v1/identity/ad/domain-controllers"
        )
        assert response.status_code == 200

    @pytest.mark.anyio()
    async def test_has_success_field(self, client: AsyncClient) -> None:
        response = await client.get(
            "/api/v1/identity/ad/domain-controllers"
        )
        data = response.json()
        assert "success" in data
        assert data["success"] is True

    @pytest.mark.anyio()
    async def test_has_domain_controllers(self, client: AsyncClient) -> None:
        response = await client.get(
            "/api/v1/identity/ad/domain-controllers"
        )
        data = response.json()
        assert "domain_controllers" in data
        assert isinstance(data["domain_controllers"], list)


class TestADForestAPI:
    """Tests for GET /api/v1/identity/ad/forest."""

    @pytest.mark.anyio()
    async def test_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/ad/forest")
        assert response.status_code == 200

    @pytest.mark.anyio()
    async def test_has_forest(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/ad/forest")
        data = response.json()
        assert "forest" in data
        assert "name" in data["forest"]


class TestADDomainAPI:
    """Tests for GET /api/v1/identity/ad/domain."""

    @pytest.mark.anyio()
    async def test_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/ad/domain")
        assert response.status_code == 200

    @pytest.mark.anyio()
    async def test_has_domain(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/ad/domain")
        data = response.json()
        assert "domain" in data
        assert "password_policy" in data["domain"]


class TestADUsersAPI:
    """Tests for GET /api/v1/identity/ad/users."""

    @pytest.mark.anyio()
    async def test_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/ad/users")
        assert response.status_code == 200

    @pytest.mark.anyio()
    async def test_has_users_list(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/ad/users")
        data = response.json()
        assert "users" in data
        assert isinstance(data["users"], list)

    @pytest.mark.anyio()
    async def test_has_summary_counts(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/ad/users")
        data = response.json()
        assert "total_count" in data
        assert "enabled_count" in data
        assert "disabled_count" in data


class TestADGroupsAPI:
    """Tests for GET /api/v1/identity/ad/groups."""

    @pytest.mark.anyio()
    async def test_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/ad/groups")
        assert response.status_code == 200

    @pytest.mark.anyio()
    async def test_has_groups(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/ad/groups")
        data = response.json()
        assert "groups" in data


class TestADComputersAPI:
    """Tests for GET /api/v1/identity/ad/computers."""

    @pytest.mark.anyio()
    async def test_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/ad/computers")
        assert response.status_code == 200

    @pytest.mark.anyio()
    async def test_has_computers(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/ad/computers")
        data = response.json()
        assert "computers" in data
        assert "server_count" in data


class TestADGPOsAPI:
    """Tests for GET /api/v1/identity/ad/gpos."""

    @pytest.mark.anyio()
    async def test_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/ad/gpos")
        assert response.status_code == 200

    @pytest.mark.anyio()
    async def test_has_gpos(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/ad/gpos")
        data = response.json()
        assert "gpos" in data


class TestADFSMOAPI:
    """Tests for GET /api/v1/identity/ad/fsmo-roles."""

    @pytest.mark.anyio()
    async def test_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/ad/fsmo-roles")
        assert response.status_code == 200

    @pytest.mark.anyio()
    async def test_has_fsmo_roles(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/ad/fsmo-roles")
        data = response.json()
        assert "fsmo_roles" in data
        assert "forest_roles" in data["fsmo_roles"]


class TestADDNSHealthAPI:
    """Tests for GET /api/v1/identity/ad/dns-health."""

    @pytest.mark.anyio()
    async def test_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/ad/dns-health")
        assert response.status_code == 200

    @pytest.mark.anyio()
    async def test_has_dns_health(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/ad/dns-health")
        data = response.json()
        assert "dns_health" in data


class TestADDHCPHealthAPI:
    """Tests for GET /api/v1/identity/ad/dhcp-health."""

    @pytest.mark.anyio()
    async def test_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/ad/dhcp-health")
        assert response.status_code == 200

    @pytest.mark.anyio()
    async def test_has_dhcp_health(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/ad/dhcp-health")
        data = response.json()
        assert "dhcp_health" in data


# ------------------------------------------------------------------ #
# Microsoft 365 Endpoints                                             #
# ------------------------------------------------------------------ #


class TestM365TenantAPI:
    """Tests for GET /api/v1/identity/m365/tenant."""

    @pytest.mark.anyio()
    async def test_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/m365/tenant")
        assert response.status_code == 200

    @pytest.mark.anyio()
    async def test_has_tenant(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/m365/tenant")
        data = response.json()
        assert "tenant" in data
        assert "domain" in data["tenant"]


class TestM365LicensesAPI:
    """Tests for GET /api/v1/identity/m365/licenses."""

    @pytest.mark.anyio()
    async def test_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/m365/licenses")
        assert response.status_code == 200

    @pytest.mark.anyio()
    async def test_has_licenses(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/m365/licenses")
        data = response.json()
        assert "licenses" in data
        assert "total_monthly_cost" in data


class TestM365ServiceHealthAPI:
    """Tests for GET /api/v1/identity/m365/service-health."""

    @pytest.mark.anyio()
    async def test_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/m365/service-health")
        assert response.status_code == 200

    @pytest.mark.anyio()
    async def test_has_service_health(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/m365/service-health")
        data = response.json()
        assert "service_health" in data


class TestM365EntraHealthAPI:
    """Tests for GET /api/v1/identity/m365/entra-health."""

    @pytest.mark.anyio()
    async def test_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/m365/entra-health")
        assert response.status_code == 200

    @pytest.mark.anyio()
    async def test_has_entra_health(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/m365/entra-health")
        data = response.json()
        assert "entra_health" in data


class TestM365ExchangeHealthAPI:
    """Tests for GET /api/v1/identity/m365/exchange-health."""

    @pytest.mark.anyio()
    async def test_returns_200(self, client: AsyncClient) -> None:
        response = await client.get(
            "/api/v1/identity/m365/exchange-health"
        )
        assert response.status_code == 200

    @pytest.mark.anyio()
    async def test_has_exchange_health(self, client: AsyncClient) -> None:
        response = await client.get(
            "/api/v1/identity/m365/exchange-health"
        )
        data = response.json()
        assert "exchange_health" in data


class TestM365SecureScoreAPI:
    """Tests for GET /api/v1/identity/m365/secure-score."""

    @pytest.mark.anyio()
    async def test_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/m365/secure-score")
        assert response.status_code == 200

    @pytest.mark.anyio()
    async def test_has_secure_score(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/m365/secure-score")
        data = response.json()
        assert "secure_score" in data
        assert "current_score" in data["secure_score"]


class TestM365MessageCenterAPI:
    """Tests for GET /api/v1/identity/m365/message-center."""

    @pytest.mark.anyio()
    async def test_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/m365/message-center")
        assert response.status_code == 200

    @pytest.mark.anyio()
    async def test_has_items(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/m365/message-center")
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
