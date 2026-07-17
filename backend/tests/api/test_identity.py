"""
Mission Control Identity API Tests

Integration tests for /api/v1/identity endpoints.
Validates all endpoints return correct response shapes.

Sprint 2.2.0 - Microsoft 365 & Active Directory Integration.
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
    async def test_overview_has_success(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/overview")
        data = response.json()
        assert "success" in data
        assert data["success"] is True

    @pytest.mark.anyio()
    async def test_overview_has_ad_and_m365(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/overview")
        data = response.json()
        overview = data["overview"]
        assert "ad" in overview
        assert "m365" in overview


# ------------------------------------------------------------------ #
# Active Directory Endpoints                                          #
# ------------------------------------------------------------------ #


class TestADTestConnectionAPI:
    """Tests for GET /api/v1/identity/ad/test."""

    @pytest.mark.anyio()
    async def test_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/ad/test")
        assert response.status_code == 200

    @pytest.mark.anyio()
    async def test_has_connected_field(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/ad/test")
        data = response.json()
        assert "connected" in data
        assert isinstance(data["connected"], bool)


class TestADSummaryAPI:
    """Tests for GET /api/v1/identity/ad/summary."""

    @pytest.mark.anyio()
    async def test_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/ad/summary")
        assert response.status_code == 200

    @pytest.mark.anyio()
    async def test_has_connected(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/ad/summary")
        data = response.json()
        assert "connected" in data
        assert isinstance(data["connected"], bool)

    @pytest.mark.anyio()
    async def test_has_domain(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/ad/summary")
        data = response.json()
        assert "domain" in data


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
    async def test_has_total_count(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/ad/users")
        data = response.json()
        assert "total_count" in data


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


class TestADDevicesAPI:
    """Tests for GET /api/v1/identity/ad/devices."""

    @pytest.mark.anyio()
    async def test_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/ad/devices")
        assert response.status_code == 200

    @pytest.mark.anyio()
    async def test_has_devices(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/ad/devices")
        data = response.json()
        assert "devices" in data


class TestADHealthAPI:
    """Tests for GET /api/v1/identity/ad/health."""

    @pytest.mark.anyio()
    async def test_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/ad/health")
        assert response.status_code == 200

    @pytest.mark.anyio()
    async def test_has_connected(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/ad/health")
        data = response.json()
        assert "connected" in data


# ------------------------------------------------------------------ #
# Microsoft 365 Endpoints                                             #
# ------------------------------------------------------------------ #


class TestM365TestConnectionAPI:
    """Tests for GET /api/v1/identity/m365/test."""

    @pytest.mark.anyio()
    async def test_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/m365/test")
        assert response.status_code == 200

    @pytest.mark.anyio()
    async def test_has_connected_field(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/m365/test")
        data = response.json()
        assert "connected" in data
        assert isinstance(data["connected"], bool)


class TestM365SummaryAPI:
    """Tests for GET /api/v1/identity/m365/summary."""

    @pytest.mark.anyio()
    async def test_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/m365/summary")
        assert response.status_code == 200

    @pytest.mark.anyio()
    async def test_has_tenant(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/m365/summary")
        data = response.json()
        assert "tenant" in data
        assert "display_name" in data["tenant"]


class TestM365UsersAPI:
    """Tests for GET /api/v1/identity/m365/users."""

    @pytest.mark.anyio()
    async def test_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/m365/users")
        assert response.status_code == 200

    @pytest.mark.anyio()
    async def test_has_users_list(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/m365/users")
        data = response.json()
        assert "users" in data
        assert isinstance(data["users"], list)


class TestM365GroupsAPI:
    """Tests for GET /api/v1/identity/m365/groups."""

    @pytest.mark.anyio()
    async def test_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/m365/groups")
        assert response.status_code == 200

    @pytest.mark.anyio()
    async def test_has_groups(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/m365/groups")
        data = response.json()
        assert "groups" in data


class TestM365DevicesAPI:
    """Tests for GET /api/v1/identity/m365/devices."""

    @pytest.mark.anyio()
    async def test_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/m365/devices")
        assert response.status_code == 200

    @pytest.mark.anyio()
    async def test_has_devices(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/m365/devices")
        data = response.json()
        assert "devices" in data


class TestM365HealthAPI:
    """Tests for GET /api/v1/identity/m365/health."""

    @pytest.mark.anyio()
    async def test_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/m365/health")
        assert response.status_code == 200

    @pytest.mark.anyio()
    async def test_has_connected(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/identity/m365/health")
        data = response.json()
        assert "connected" in data
