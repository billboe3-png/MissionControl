"""
Mission Control Identity Provider Tests

Tests for mocked Active Directory and Microsoft 365 providers.
Validates all standardized provider methods return correct shapes.

Sprint 2.2.0 - Microsoft 365 & Active Directory Integration.
"""

import pytest

from app.providers.identity.ad_provider import MockActiveDirectoryProvider
from app.providers.identity.base_provider import (
    ActiveDirectoryProvider,
    Microsoft365Provider,
)
from app.providers.identity.m365_provider import MockMicrosoft365Provider
from app.providers.identity.provider_factory import (
    get_active_directory_provider,
    get_microsoft365_provider,
    reset_providers,
)


# ------------------------------------------------------------------ #
# AD Provider Tests                                                   #
# ------------------------------------------------------------------ #


class TestADProviderTestConnection:
    """Tests for AD provider test_connection."""

    @pytest.fixture()
    def provider(self) -> MockActiveDirectoryProvider:
        return MockActiveDirectoryProvider()

    @pytest.mark.anyio()
    async def test_returns_connected_true(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.test_connection()
        assert result["connected"] is True

    @pytest.mark.anyio()
    async def test_returns_message(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.test_connection()
        assert "message" in result or "latency_ms" in result


class TestADProviderGetSummary:
    """Tests for AD provider get_summary."""

    @pytest.fixture()
    def provider(self) -> MockActiveDirectoryProvider:
        return MockActiveDirectoryProvider()

    @pytest.mark.anyio()
    async def test_returns_connected(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_summary()
        assert result["connected"] is True

    @pytest.mark.anyio()
    async def test_has_domain(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_summary()
        assert "domain" in result
        assert "name" in result["domain"]

    @pytest.mark.anyio()
    async def test_has_counts(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_summary()
        assert "user_count" in result
        assert "group_count" in result
        assert "computer_count" in result


class TestADProviderGetUsers:
    """Tests for AD provider get_users."""

    @pytest.fixture()
    def provider(self) -> MockActiveDirectoryProvider:
        return MockActiveDirectoryProvider()

    @pytest.mark.anyio()
    async def test_returns_connected(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_users()
        assert result["connected"] is True

    @pytest.mark.anyio()
    async def test_has_users_list(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_users()
        assert "users" in result
        assert isinstance(result["users"], list)

    @pytest.mark.anyio()
    async def test_has_total_count(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_users()
        assert "total_count" in result
        assert result["total_count"] >= len(result["users"])

    @pytest.mark.anyio()
    async def test_user_has_required_fields(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_users()
        user = result["users"][0]
        required = ["sam_account_name", "display_name", "enabled"]
        for field in required:
            assert field in user, f"Missing field: {field}"


class TestADProviderGetGroups:
    """Tests for AD provider get_groups."""

    @pytest.fixture()
    def provider(self) -> MockActiveDirectoryProvider:
        return MockActiveDirectoryProvider()

    @pytest.mark.anyio()
    async def test_returns_connected(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_groups()
        assert result["connected"] is True

    @pytest.mark.anyio()
    async def test_has_groups_list(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_groups()
        assert "groups" in result
        assert isinstance(result["groups"], list)

    @pytest.mark.anyio()
    async def test_has_total_count(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_groups()
        assert "total_count" in result
        assert result["total_count"] > 0

    @pytest.mark.anyio()
    async def test_group_has_name(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_groups()
        group = result["groups"][0]
        assert "name" in group


class TestADProviderGetDevices:
    """Tests for AD provider get_devices."""

    @pytest.fixture()
    def provider(self) -> MockActiveDirectoryProvider:
        return MockActiveDirectoryProvider()

    @pytest.mark.anyio()
    async def test_returns_connected(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_devices()
        assert result["connected"] is True

    @pytest.mark.anyio()
    async def test_has_devices_list(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_devices()
        assert "devices" in result
        assert isinstance(result["devices"], list)

    @pytest.mark.anyio()
    async def test_has_total_count(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_devices()
        assert "total_count" in result

    @pytest.mark.anyio()
    async def test_device_has_name(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_devices()
        if result["devices"]:
            device = result["devices"][0]
            assert "name" in device


class TestADProviderGetHealth:
    """Tests for AD provider get_health."""

    @pytest.fixture()
    def provider(self) -> MockActiveDirectoryProvider:
        return MockActiveDirectoryProvider()

    @pytest.mark.anyio()
    async def test_returns_connected(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_health()
        assert result["connected"] is True

    @pytest.mark.anyio()
    async def test_has_status(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_health()
        assert "status" in result

    @pytest.mark.anyio()
    async def test_has_replication(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_health()
        assert "replication" in result
        repl = result["replication"]
        assert "pending_replications" in repl
        assert "failed_replications" in repl


# ------------------------------------------------------------------ #
# M365 Provider Tests                                                 #
# ------------------------------------------------------------------ #


class TestM365ProviderTestConnection:
    """Tests for M365 provider test_connection."""

    @pytest.fixture()
    def provider(self) -> MockMicrosoft365Provider:
        return MockMicrosoft365Provider()

    @pytest.mark.anyio()
    async def test_returns_connected_true(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.test_connection()
        assert result["connected"] is True

    @pytest.mark.anyio()
    async def test_returns_message(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.test_connection()
        assert "message" in result or "latency_ms" in result


class TestM365ProviderGetSummary:
    """Tests for M365 provider get_summary."""

    @pytest.fixture()
    def provider(self) -> MockMicrosoft365Provider:
        return MockMicrosoft365Provider()

    @pytest.mark.anyio()
    async def test_returns_connected(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_summary()
        assert result["connected"] is True

    @pytest.mark.anyio()
    async def test_has_tenant(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_summary()
        assert "tenant" in result
        assert "display_name" in result["tenant"]

    @pytest.mark.anyio()
    async def test_has_licenses(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_summary()
        assert "licenses" in result
        assert isinstance(result["licenses"], list)

    @pytest.mark.anyio()
    async def test_has_verified_domains(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_summary()
        tenant = result["tenant"]
        assert "verified_domains" in tenant


class TestM365ProviderGetUsers:
    """Tests for M365 provider get_users."""

    @pytest.fixture()
    def provider(self) -> MockMicrosoft365Provider:
        return MockMicrosoft365Provider()

    @pytest.mark.anyio()
    async def test_returns_connected(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_users()
        assert result["connected"] is True

    @pytest.mark.anyio()
    async def test_has_users_list(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_users()
        assert "users" in result
        assert isinstance(result["users"], list)

    @pytest.mark.anyio()
    async def test_has_total_count(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_users()
        assert "total_count" in result

    @pytest.mark.anyio()
    async def test_user_has_required_fields(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_users()
        user = result["users"][0]
        required = ["display_name", "account_enabled"]
        for field in required:
            assert field in user, f"Missing field: {field}"


class TestM365ProviderGetGroups:
    """Tests for M365 provider get_groups."""

    @pytest.fixture()
    def provider(self) -> MockMicrosoft365Provider:
        return MockMicrosoft365Provider()

    @pytest.mark.anyio()
    async def test_returns_connected(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_groups()
        assert result["connected"] is True

    @pytest.mark.anyio()
    async def test_has_groups_list(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_groups()
        assert "groups" in result
        assert isinstance(result["groups"], list)

    @pytest.mark.anyio()
    async def test_has_total_count(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_groups()
        assert "total_count" in result


class TestM365ProviderGetDevices:
    """Tests for M365 provider get_devices."""

    @pytest.fixture()
    def provider(self) -> MockMicrosoft365Provider:
        return MockMicrosoft365Provider()

    @pytest.mark.anyio()
    async def test_returns_connected(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_devices()
        assert result["connected"] is True

    @pytest.mark.anyio()
    async def test_has_devices_list(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_devices()
        assert "devices" in result
        assert isinstance(result["devices"], list)

    @pytest.mark.anyio()
    async def test_has_total_count(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_devices()
        assert "total_count" in result


class TestM365ProviderGetHealth:
    """Tests for M365 provider get_health."""

    @pytest.fixture()
    def provider(self) -> MockMicrosoft365Provider:
        return MockMicrosoft365Provider()

    @pytest.mark.anyio()
    async def test_returns_connected(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_health()
        assert result["connected"] is True

    @pytest.mark.anyio()
    async def test_has_status(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_health()
        assert "status" in result

    @pytest.mark.anyio()
    async def test_has_services(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_health()
        assert "services" in result
        assert isinstance(result["services"], list)

    @pytest.mark.anyio()
    async def test_has_active_incidents(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_health()
        assert "active_incidents" in result


# ------------------------------------------------------------------ #
# Provider Factory Tests                                              #
# ------------------------------------------------------------------ #


class TestProviderFactory:
    """Tests for identity provider factory singletons."""

    @pytest.fixture(autouse=True)
    def _reset(self) -> None:
        reset_providers()

    @pytest.mark.anyio()
    async def test_get_ad_provider_returns_mock_when_not_configured(self) -> None:
        provider = get_active_directory_provider()
        assert isinstance(provider, MockActiveDirectoryProvider)

    @pytest.mark.anyio()
    async def test_get_m365_provider_returns_mock_when_not_configured(self) -> None:
        provider = get_microsoft365_provider()
        assert isinstance(provider, MockMicrosoft365Provider)

    @pytest.mark.anyio()
    async def test_get_ad_provider_returns_same_instance(self) -> None:
        p1 = get_active_directory_provider()
        p2 = get_active_directory_provider()
        assert p1 is p2

    @pytest.mark.anyio()
    async def test_get_m365_provider_returns_same_instance(self) -> None:
        p1 = get_microsoft365_provider()
        p2 = get_microsoft365_provider()
        assert p1 is p2

    @pytest.mark.anyio()
    async def test_reset_providers_clears_singletons(self) -> None:
        p1 = get_active_directory_provider()
        reset_providers()
        p2 = get_active_directory_provider()
        assert p1 is not p2

    @pytest.mark.anyio()
    async def test_ad_provider_is_abstract_type(self) -> None:
        provider = get_active_directory_provider()
        assert isinstance(provider, ActiveDirectoryProvider)

    @pytest.mark.anyio()
    async def test_m365_provider_is_abstract_type(self) -> None:
        provider = get_microsoft365_provider()
        assert isinstance(provider, Microsoft365Provider)
