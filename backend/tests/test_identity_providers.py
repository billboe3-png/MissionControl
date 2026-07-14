"""
Mission Control Identity Provider Tests

Tests for mocked Active Directory and Microsoft 365 providers.
Validates all provider methods return correct data shapes.

Sprint 2.2.1 - Identity Platform Foundation.
"""

import pytest

from app.providers.identity.ad_provider import MockActiveDirectoryProvider
from app.providers.identity.m365_provider import MockMicrosoft365Provider
from app.providers.identity.provider_factory import (
    get_active_directory_provider,
    get_microsoft365_provider,
)


# ------------------------------------------------------------------ #
# AD Provider Tests                                                   #
# ------------------------------------------------------------------ #


class TestADProviderGetDomainControllers:
    """Tests for AD provider get_domain_controllers."""

    @pytest.fixture()
    def provider(self) -> MockActiveDirectoryProvider:
        return MockActiveDirectoryProvider()

    @pytest.mark.anyio()
    async def test_returns_success(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_domain_controllers()
        assert result["success"] is True

    @pytest.mark.anyio()
    async def test_returns_list(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_domain_controllers()
        assert "domain_controllers" in result
        assert isinstance(result["domain_controllers"], list)

    @pytest.mark.anyio()
    async def test_has_count(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_domain_controllers()
        assert "total_count" in result
        assert result["total_count"] == len(result["domain_controllers"])

    @pytest.mark.anyio()
    async def test_dc_has_required_fields(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_domain_controllers()
        dc = result["domain_controllers"][0]
        required = ["name", "ip_address", "os_version", "site",
                     "is_global_catalog", "is_fsmo", "status"]
        for field in required:
            assert field in dc, f"Missing field: {field}"

    @pytest.mark.anyio()
    async def test_dc_has_multiple_entries(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_domain_controllers()
        assert len(result["domain_controllers"]) >= 2


class TestADProviderGetForest:
    """Tests for AD provider get_forest."""

    @pytest.fixture()
    def provider(self) -> MockActiveDirectoryProvider:
        return MockActiveDirectoryProvider()

    @pytest.mark.anyio()
    async def test_returns_success(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_forest()
        assert result["success"] is True

    @pytest.mark.anyio()
    async def test_has_forest_key(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_forest()
        assert "forest" in result

    @pytest.mark.anyio()
    async def test_forest_has_domains(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_forest()
        forest = result["forest"]
        assert "domains" in forest
        assert isinstance(forest["domains"], list)
        assert len(forest["domains"]) >= 1


class TestADProviderGetDomain:
    """Tests for AD provider get_domain."""

    @pytest.fixture()
    def provider(self) -> MockActiveDirectoryProvider:
        return MockActiveDirectoryProvider()

    @pytest.mark.anyio()
    async def test_returns_success(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_domain()
        assert result["success"] is True

    @pytest.mark.anyio()
    async def test_has_domain_key(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_domain()
        assert "domain" in result

    @pytest.mark.anyio()
    async def test_domain_has_password_policy(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_domain()
        domain = result["domain"]
        assert "password_policy" in domain
        assert "min_length" in domain["password_policy"]

    @pytest.mark.anyio()
    async def test_domain_has_counts(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_domain()
        domain = result["domain"]
        assert "user_count" in domain
        assert "computer_count" in domain
        assert "group_count" in domain


class TestADProviderGetOUs:
    """Tests for AD provider get_organizational_units."""

    @pytest.fixture()
    def provider(self) -> MockActiveDirectoryProvider:
        return MockActiveDirectoryProvider()

    @pytest.mark.anyio()
    async def test_returns_success(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_organizational_units()
        assert result["success"] is True

    @pytest.mark.anyio()
    async def test_returns_list(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_organizational_units()
        assert "organizational_units" in result
        assert isinstance(result["organizational_units"], list)

    @pytest.mark.anyio()
    async def test_ou_has_dn(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_organizational_units()
        ou = result["organizational_units"][0]
        assert "distinguished_name" in ou


class TestADProviderGetUsers:
    """Tests for AD provider get_users."""

    @pytest.fixture()
    def provider(self) -> MockActiveDirectoryProvider:
        return MockActiveDirectoryProvider()

    @pytest.mark.anyio()
    async def test_returns_success(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_users()
        assert result["success"] is True

    @pytest.mark.anyio()
    async def test_has_summary_counts(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_users()
        assert "total_count" in result
        assert "enabled_count" in result
        assert "disabled_count" in result
        assert "locked_out_count" in result
        assert "password_expired_count" in result

    @pytest.mark.anyio()
    async def test_user_has_required_fields(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_users()
        user = result["users"][0]
        required = ["sam_account_name", "display_name", "department",
                     "title", "enabled"]
        for field in required:
            assert field in user, f"Missing field: {field}"


class TestADProviderGetGroups:
    """Tests for AD provider get_groups."""

    @pytest.fixture()
    def provider(self) -> MockActiveDirectoryProvider:
        return MockActiveDirectoryProvider()

    @pytest.mark.anyio()
    async def test_returns_success(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_groups()
        assert result["success"] is True

    @pytest.mark.anyio()
    async def test_has_total_count(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_groups()
        assert "total_count" in result
        assert result["total_count"] > 0

    @pytest.mark.anyio()
    async def test_group_has_scope(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_groups()
        group = result["groups"][0]
        assert "scope" in group
        assert group["scope"] in ["Global", "DomainLocal", "Universal"]


class TestADProviderGetComputers:
    """Tests for AD provider get_computers."""

    @pytest.fixture()
    def provider(self) -> MockActiveDirectoryProvider:
        return MockActiveDirectoryProvider()

    @pytest.mark.anyio()
    async def test_returns_success(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_computers()
        assert result["success"] is True

    @pytest.mark.anyio()
    async def test_has_category_counts(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_computers()
        assert "server_count" in result
        assert "workstation_count" in result

    @pytest.mark.anyio()
    async def test_computer_has_os(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_computers()
        comp = result["computers"][0]
        assert "os_version" in comp
        assert "Windows" in comp["os_version"]


class TestADProviderGetGPOs:
    """Tests for AD provider get_gpos."""

    @pytest.fixture()
    def provider(self) -> MockActiveDirectoryProvider:
        return MockActiveDirectoryProvider()

    @pytest.mark.anyio()
    async def test_returns_success(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_gpos()
        assert result["success"] is True

    @pytest.mark.anyio()
    async def test_has_gpo_list(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_gpos()
        assert "gpos" in result
        assert len(result["gpos"]) >= 1

    @pytest.mark.anyio()
    async def test_gpo_has_guid(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_gpos()
        gpo = result["gpos"][0]
        assert "guid" in gpo
        assert len(gpo["guid"]) > 0


class TestADProviderGetFSMO:
    """Tests for AD provider get_fsmo_roles."""

    @pytest.fixture()
    def provider(self) -> MockActiveDirectoryProvider:
        return MockActiveDirectoryProvider()

    @pytest.mark.anyio()
    async def test_returns_success(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_fsmo_roles()
        assert result["success"] is True

    @pytest.mark.anyio()
    async def test_has_forest_and_domain_roles(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_fsmo_roles()
        assert "forest_roles" in result
        assert "domain_roles" in result

    @pytest.mark.anyio()
    async def test_has_schema_master(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_fsmo_roles()
        assert "schema_master" in result["forest_roles"]

    @pytest.mark.anyio()
    async def test_has_pdc_emulator(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_fsmo_roles()
        assert "pdc_emulator" in result["domain_roles"]


class TestADProviderGetDNS:
    """Tests for AD provider get_dns_health."""

    @pytest.fixture()
    def provider(self) -> MockActiveDirectoryProvider:
        return MockActiveDirectoryProvider()

    @pytest.mark.anyio()
    async def test_returns_success(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_dns_health()
        assert result["success"] is True

    @pytest.mark.anyio()
    async def test_has_servers(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_dns_health()
        health = result["dns_health"]
        assert "servers" in health
        assert len(health["servers"]) >= 1

    @pytest.mark.anyio()
    async def test_has_totals(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_dns_health()
        health = result["dns_health"]
        assert "total_zones" in health
        assert "total_records" in health


class TestADProviderGetDHCP:
    """Tests for AD provider get_dhcp_health."""

    @pytest.fixture()
    def provider(self) -> MockActiveDirectoryProvider:
        return MockActiveDirectoryProvider()

    @pytest.mark.anyio()
    async def test_returns_success(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_dhcp_health()
        assert result["success"] is True

    @pytest.mark.anyio()
    async def test_has_utilization(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_dhcp_health()
        health = result["dhcp_health"]
        assert "overall_utilization_percent" in health

    @pytest.mark.anyio()
    async def test_has_authorized_flag(self, provider: MockActiveDirectoryProvider) -> None:
        result = await provider.get_dhcp_health()
        health = result["dhcp_health"]
        assert "authorized" in health
        assert isinstance(health["authorized"], bool)


# ------------------------------------------------------------------ #
# M365 Provider Tests                                                 #
# ------------------------------------------------------------------ #


class TestM365ProviderGetTenant:
    """Tests for M365 provider get_tenant."""

    @pytest.fixture()
    def provider(self) -> MockMicrosoft365Provider:
        return MockMicrosoft365Provider()

    @pytest.mark.anyio()
    async def test_returns_success(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_tenant()
        assert result["success"] is True

    @pytest.mark.anyio()
    async def test_has_tenant_key(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_tenant()
        assert "tenant" in result

    @pytest.mark.anyio()
    async def test_tenant_has_domain(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_tenant()
        tenant = result["tenant"]
        assert "domain" in tenant
        assert "verified_domains" in tenant


class TestM365ProviderGetLicenses:
    """Tests for M365 provider get_licenses."""

    @pytest.fixture()
    def provider(self) -> MockMicrosoft365Provider:
        return MockMicrosoft365Provider()

    @pytest.mark.anyio()
    async def test_returns_success(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_licenses()
        assert result["success"] is True

    @pytest.mark.anyio()
    async def test_has_license_list(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_licenses()
        assert "licenses" in result
        assert len(result["licenses"]) >= 1

    @pytest.mark.anyio()
    async def test_has_cost_totals(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_licenses()
        assert "total_monthly_cost" in result
        assert result["total_monthly_cost"] > 0

    @pytest.mark.anyio()
    async def test_license_has_sku(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_licenses()
        lic = result["licenses"][0]
        assert "sku_part_number" in lic
        assert "assigned_licenses" in lic


class TestM365ProviderGetServiceHealth:
    """Tests for M365 provider get_service_health."""

    @pytest.fixture()
    def provider(self) -> MockMicrosoft365Provider:
        return MockMicrosoft365Provider()

    @pytest.mark.anyio()
    async def test_returns_success(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_service_health()
        assert result["success"] is True

    @pytest.mark.anyio()
    async def test_has_services(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_service_health()
        health = result["service_health"]
        assert "services" in health
        assert len(health["services"]) >= 1

    @pytest.mark.anyio()
    async def test_has_overall_status(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_service_health()
        health = result["service_health"]
        assert health["overall_status"] in ["healthy", "degraded", "incident"]


class TestM365ProviderGetEntraHealth:
    """Tests for M365 provider get_entra_health."""

    @pytest.fixture()
    def provider(self) -> MockMicrosoft365Provider:
        return MockMicrosoft365Provider()

    @pytest.mark.anyio()
    async def test_returns_success(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_entra_health()
        assert result["success"] is True

    @pytest.mark.anyio()
    async def test_has_sign_in_rate(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_entra_health()
        health = result["entra_health"]
        assert "sign_in_success_rate" in health
        assert 0 <= health["sign_in_success_rate"] <= 100

    @pytest.mark.anyio()
    async def test_has_mfa_rate(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_entra_health()
        health = result["entra_health"]
        assert "mfa_success_rate" in health


class TestM365ProviderGetExchangeHealth:
    """Tests for M365 provider get_exchange_health."""

    @pytest.fixture()
    def provider(self) -> MockMicrosoft365Provider:
        return MockMicrosoft365Provider()

    @pytest.mark.anyio()
    async def test_returns_success(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_exchange_health()
        assert result["success"] is True

    @pytest.mark.anyio()
    async def test_has_mailbox_counts(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_exchange_health()
        health = result["exchange_health"]
        assert "mailboxes_total" in health
        assert "mailboxes_active" in health


class TestM365ProviderGetSecureScore:
    """Tests for M365 provider get_secure_score."""

    @pytest.fixture()
    def provider(self) -> MockMicrosoft365Provider:
        return MockMicrosoft365Provider()

    @pytest.mark.anyio()
    async def test_returns_success(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_secure_score()
        assert result["success"] is True

    @pytest.mark.anyio()
    async def test_has_score(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_secure_score()
        score = result["secure_score"]
        assert "current_score" in score
        assert "categories" in score

    @pytest.mark.anyio()
    async def test_has_industry_comparison(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_secure_score()
        score = result["secure_score"]
        assert "comparison_to_industry" in score
        assert "tier" in score["comparison_to_industry"]


class TestM365ProviderGetMessageCenter:
    """Tests for M365 provider get_message_center."""

    @pytest.fixture()
    def provider(self) -> MockMicrosoft365Provider:
        return MockMicrosoft365Provider()

    @pytest.mark.anyio()
    async def test_returns_success(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_message_center()
        mc = result.get("message_center", result)
        assert "items" in mc
        assert isinstance(mc["items"], list)

    @pytest.mark.anyio()
    async def test_has_total_items(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_message_center()
        mc = result.get("message_center", result)
        assert "total_items" in mc

    @pytest.mark.anyio()
    async def test_item_has_action_required(self, provider: MockMicrosoft365Provider) -> None:
        result = await provider.get_message_center()
        mc = result.get("message_center", result)
        item = mc["items"][0]
        assert "action_required" in item
        assert isinstance(item["action_required"], bool)


# ------------------------------------------------------------------ #
# Provider Factory Tests                                              #
# ------------------------------------------------------------------ #


class TestProviderFactory:
    """Tests for identity provider factory singletons."""

    @pytest.mark.anyio()
    async def test_get_ad_provider_returns_instance(self) -> None:
        provider = get_active_directory_provider()
        assert isinstance(provider, MockActiveDirectoryProvider)

    @pytest.mark.anyio()
    async def test_get_m365_provider_returns_instance(self) -> None:
        provider = get_microsoft365_provider()
        assert isinstance(provider, MockMicrosoft365Provider)

    @pytest.mark.anyio()
    async def test_factory_returns_same_ad_instance(self) -> None:
        p1 = get_active_directory_provider()
        p2 = get_active_directory_provider()
        assert p1 is p2

    @pytest.mark.anyio()
    async def test_factory_returns_same_m365_instance(self) -> None:
        p1 = get_microsoft365_provider()
        p2 = get_microsoft365_provider()
        assert p1 is p2
