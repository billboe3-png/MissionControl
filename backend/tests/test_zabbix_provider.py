"""
Zabbix provider tests.

Sprint 2.3.0 - Enterprise Zabbix Integration.

Tests the provider ABC contract, mock provider scenarios,
production provider configuration, factory singleton,
and data consistency across all endpoints.
"""

import pytest

from app.providers.zabbix.base_provider import ZabbixProvider
from app.providers.zabbix.mock_provider import MockZabbixProvider, set_mock_mode
from app.providers.zabbix.provider_factory import (
    get_zabbix_provider,
    reset_zabbix_provider,
)
from app.providers.zabbix.zabbix_provider import ApiZabbixProvider

# ------------------------------------------------------------------ #
# ABC Contract                                                        #
# ------------------------------------------------------------------ #


class TestZabbixProviderABC:
    def test_cannot_instantiate_abc(self):
        with pytest.raises(TypeError):
            ZabbixProvider()

    def test_mock_implements_abc(self):
        provider = MockZabbixProvider()
        assert isinstance(provider, ZabbixProvider)

    def test_api_provider_implements_abc(self):
        provider = ApiZabbixProvider()
        assert isinstance(provider, ZabbixProvider)

    def test_has_all_required_methods(self):
        required = [
            "test_connection",
            "login",
            "logout",
            "get_summary",
            "get_hosts",
            "get_host_groups",
            "get_triggers",
            "get_problems",
            "get_events",
            "get_items",
            "get_history",
            "get_templates",
            "get_dashboards",
            "get_maps",
            "get_health",
        ]
        for method in required:
            assert hasattr(MockZabbixProvider, method), f"Missing: {method}"


# ------------------------------------------------------------------ #
# Mock Provider — Healthy Mode (default)                              #
# ------------------------------------------------------------------ #


@pytest.fixture(autouse=True)
def _reset_mock_mode():
    """Reset mock mode to healthy after each test."""
    set_mock_mode("healthy")
    yield
    set_mock_mode("healthy")


@pytest.fixture
def provider():
    return MockZabbixProvider()


class TestMockHealthyConnection:
    @pytest.mark.asyncio
    async def test_connection_succeeds(self, provider):
        result = await provider.test_connection()
        assert result["connected"] is True
        assert "latency_ms" in result
        assert "version" in result

    @pytest.mark.asyncio
    async def test_login_succeeds(self, provider):
        result = await provider.login()
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_logout_succeeds(self, provider):
        result = await provider.logout()
        assert result["success"] is True


class TestMockHealthySummary:
    @pytest.mark.asyncio
    async def test_summary_returns_connected(self, provider):
        result = await provider.get_summary()
        assert result["connected"] is True
        assert result["host_count"] > 0
        assert "version" in result

    @pytest.mark.asyncio
    async def test_summary_has_required_fields(self, provider):
        result = await provider.get_summary()
        for key in [
            "connected", "version", "host_count", "problem_count",
            "critical_count", "warning_count", "ok_count",
            "uptime_hours", "api_latency_ms",
        ]:
            assert key in result, f"Missing: {key}"


class TestMockHealthyHosts:
    @pytest.mark.asyncio
    async def test_hosts_returns_list(self, provider):
        result = await provider.get_hosts()
        assert "hosts" in result
        assert result["total_count"] > 0

    @pytest.mark.asyncio
    async def test_hosts_have_required_fields(self, provider):
        result = await provider.get_hosts()
        for host in result["hosts"]:
            for key in ["hostid", "host", "name", "status", "available"]:
                assert key in host, f"Missing {key} in host"

    @pytest.mark.asyncio
    async def test_hosts_counts_are_consistent(self, provider):
        result = await provider.get_hosts()
        en = result["enabled_count"]
        dc = result["disabled_count"]
        assert en + dc == result["total_count"]
        av = result["available_count"]
        ua = result["unavailable_count"]
        assert av + ua == result["total_count"]


class TestMockHealthyGroups:
    @pytest.mark.asyncio
    async def test_groups_returns_list(self, provider):
        result = await provider.get_host_groups()
        assert result["total_count"] > 0
        assert "groups" in result

    @pytest.mark.asyncio
    async def test_groups_have_required_fields(self, provider):
        result = await provider.get_host_groups()
        for group in result["groups"]:
            assert "groupid" in group
            assert "name" in group


class TestMockHealthyTriggers:
    @pytest.mark.asyncio
    async def test_triggers_returns_list(self, provider):
        result = await provider.get_triggers()
        assert result["total_count"] > 0

    @pytest.mark.asyncio
    async def test_triggers_have_required_fields(self, provider):
        result = await provider.get_triggers()
        for trigger in result["triggers"]:
            for key in ["triggerid", "description", "priority", "value"]:
                assert key in trigger, f"Missing {key}"

    @pytest.mark.asyncio
    async def test_trigger_counts_consistent(self, provider):
        result = await provider.get_triggers()
        assert result["problem_count"] + result["ok_count"] == result["total_count"]
        en = result["enabled_count"]
        dc = result["disabled_count"]
        assert en + dc == result["total_count"]


class TestMockHealthyProblems:
    @pytest.mark.asyncio
    async def test_problems_returns_list(self, provider):
        result = await provider.get_problems()
        assert result["total_count"] > 0
        assert "severity_counts" in result

    @pytest.mark.asyncio
    async def test_problems_have_required_fields(self, provider):
        result = await provider.get_problems()
        keys = [
            "eventid", "name", "severity",
            "status", "acknowledged", "host",
        ]
        for problem in result["problems"]:
            for key in keys:
                assert key in problem, f"Missing {key}"

    @pytest.mark.asyncio
    async def test_severity_counts_add_up(self, provider):
        result = await provider.get_problems()
        total_severity = sum(result["severity_counts"].values())
        assert total_severity == result["total_count"]

    @pytest.mark.asyncio
    async def test_acknowledged_counts_consistent(self, provider):
        result = await provider.get_problems()
        ac = result["acknowledged_count"]
        uac = result["unacknowledged_count"]
        assert ac + uac == result["total_count"]


class TestMockHealthyEvents:
    @pytest.mark.asyncio
    async def test_events_returns_list(self, provider):
        result = await provider.get_events()
        assert result["total_count"] > 0

    @pytest.mark.asyncio
    async def test_events_have_required_fields(self, provider):
        result = await provider.get_events()
        for event in result["events"]:
            for key in ["eventid", "name", "severity", "status", "timestamp"]:
                assert key in event, f"Missing {key}"


class TestMockHealthyTemplates:
    @pytest.mark.asyncio
    async def test_templates_returns_list(self, provider):
        result = await provider.get_templates()
        assert result["total_count"] > 0

    @pytest.mark.asyncio
    async def test_templates_have_required_fields(self, provider):
        result = await provider.get_templates()
        for t in result["templates"]:
            assert "templateid" in t
            assert "name" in t


class TestMockHealthyItems:
    @pytest.mark.asyncio
    async def test_items_returns_list(self, provider):
        result = await provider.get_items()
        assert result["total_count"] > 0

    @pytest.mark.asyncio
    async def test_items_have_required_fields(self, provider):
        result = await provider.get_items()
        for item in result["items"]:
            for key in ["itemid", "name", "status", "type"]:
                assert key in item, f"Missing {key}"

    @pytest.mark.asyncio
    async def test_item_counts_consistent(self, provider):
        result = await provider.get_items()
        sc = result["supported_count"]
        usc = result["unsupported_count"]
        assert sc + usc == result["total_count"]


class TestMockHealthyDashboards:
    @pytest.mark.asyncio
    async def test_dashboards_returns_list(self, provider):
        result = await provider.get_dashboards()
        assert result["total_count"] > 0

    @pytest.mark.asyncio
    async def test_dashboards_have_required_fields(self, provider):
        result = await provider.get_dashboards()
        for d in result["dashboards"]:
            assert "dashboardid" in d
            assert "name" in d


class TestMockHealthyMaps:
    @pytest.mark.asyncio
    async def test_maps_returns_list(self, provider):
        result = await provider.get_maps()
        assert result["total_count"] > 0

    @pytest.mark.asyncio
    async def test_maps_have_required_fields(self, provider):
        result = await provider.get_maps()
        for m in result["maps"]:
            assert "sysmapid" in m
            assert "name" in m
            assert "width" in m


class TestMockHealthyHealth:
    @pytest.mark.asyncio
    async def test_health_status(self, provider):
        result = await provider.get_health()
        assert result["status"] == "healthy"
        assert "version" in result
        assert "database" in result

    @pytest.mark.asyncio
    async def test_health_database_fields(self, provider):
        result = await provider.get_health()
        db = result["database"]
        assert "status" in db
        assert "type" in db
        assert "size_mb" in db


class TestMockHealthyHistory:
    @pytest.mark.asyncio
    async def test_history_returns_data(self, provider):
        result = await provider.get_history()
        assert result["total_count"] > 0
        assert "history" in result


# ------------------------------------------------------------------ #
# Mock Provider — Large Mode                                          #
# ------------------------------------------------------------------ #


class TestMockLarge:
    @pytest.mark.asyncio
    async def test_hosts_large_count(self):
        set_mock_mode("large")
        provider = MockZabbixProvider()
        result = await provider.get_hosts()
        assert result["total_count"] > 100

    @pytest.mark.asyncio
    async def test_summary_large_count(self):
        set_mock_mode("large")
        provider = MockZabbixProvider()
        result = await provider.get_summary()
        assert result["host_count"] > 100

    @pytest.mark.asyncio
    async def test_items_large_count(self):
        set_mock_mode("large")
        provider = MockZabbixProvider()
        result = await provider.get_items()
        assert result["total_count"] > 0


# ------------------------------------------------------------------ #
# Mock Provider — Offline Mode                                        #
# ------------------------------------------------------------------ #


class TestMockOffline:
    @pytest.mark.asyncio
    async def test_connection_fails(self):
        set_mock_mode("offline")
        provider = MockZabbixProvider()
        result = await provider.test_connection()
        assert result["connected"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_summary_fails(self):
        set_mock_mode("offline")
        provider = MockZabbixProvider()
        result = await provider.get_summary()
        assert result["connected"] is False

    @pytest.mark.asyncio
    async def test_hosts_fails(self):
        set_mock_mode("offline")
        provider = MockZabbixProvider()
        result = await provider.get_hosts()
        assert result["connected"] is False

    @pytest.mark.asyncio
    async def test_problems_fails(self):
        set_mock_mode("offline")
        provider = MockZabbixProvider()
        result = await provider.get_problems()
        assert result["connected"] is False

    @pytest.mark.asyncio
    async def test_health_reports_unavailable(self):
        set_mock_mode("offline")
        provider = MockZabbixProvider()
        result = await provider.get_health()
        assert result["connected"] is False
        assert "status" in result

    @pytest.mark.asyncio
    async def test_login_fails(self):
        set_mock_mode("offline")
        provider = MockZabbixProvider()
        result = await provider.login()
        assert result.get("success") is not True

    @pytest.mark.asyncio
    async def test_groups_fails(self):
        set_mock_mode("offline")
        provider = MockZabbixProvider()
        result = await provider.get_host_groups()
        assert result["connected"] is False

    @pytest.mark.asyncio
    async def test_triggers_fails(self):
        set_mock_mode("offline")
        provider = MockZabbixProvider()
        result = await provider.get_triggers()
        assert result["connected"] is False

    @pytest.mark.asyncio
    async def test_events_fails(self):
        set_mock_mode("offline")
        provider = MockZabbixProvider()
        result = await provider.get_events()
        assert result["connected"] is False


# ------------------------------------------------------------------ #
# Mock Provider — Auth Failure Mode                                   #
# ------------------------------------------------------------------ #


class TestMockAuthFailure:
    @pytest.mark.asyncio
    async def test_connection_fails(self):
        set_mock_mode("auth_failure")
        provider = MockZabbixProvider()
        result = await provider.test_connection()
        assert result["connected"] is False

    @pytest.mark.asyncio
    async def test_summary_fails(self):
        set_mock_mode("auth_failure")
        provider = MockZabbixProvider()
        result = await provider.get_summary()
        assert result["connected"] is False

    @pytest.mark.asyncio
    async def test_login_fails(self):
        set_mock_mode("auth_failure")
        provider = MockZabbixProvider()
        result = await provider.login()
        assert result.get("success") is not True


# ------------------------------------------------------------------ #
# Mock Provider — Empty Mode                                          #
# ------------------------------------------------------------------ #


class TestMockEmpty:
    @pytest.mark.asyncio
    async def test_hosts_empty(self):
        set_mock_mode("empty")
        provider = MockZabbixProvider()
        result = await provider.get_hosts()
        assert result["total_count"] == 0
        assert result["hosts"] == []

    @pytest.mark.asyncio
    async def test_groups_empty(self):
        set_mock_mode("empty")
        provider = MockZabbixProvider()
        result = await provider.get_host_groups()
        assert result["total_count"] == 0

    @pytest.mark.asyncio
    async def test_triggers_empty(self):
        set_mock_mode("empty")
        provider = MockZabbixProvider()
        result = await provider.get_triggers()
        assert result["total_count"] == 0

    @pytest.mark.asyncio
    async def test_problems_empty(self):
        set_mock_mode("empty")
        provider = MockZabbixProvider()
        result = await provider.get_problems()
        assert result["total_count"] == 0

    @pytest.mark.asyncio
    async def test_events_empty(self):
        set_mock_mode("empty")
        provider = MockZabbixProvider()
        result = await provider.get_events()
        assert result["total_count"] == 0

    @pytest.mark.asyncio
    async def test_templates_empty(self):
        set_mock_mode("empty")
        provider = MockZabbixProvider()
        result = await provider.get_templates()
        assert result["total_count"] == 0

    @pytest.mark.asyncio
    async def test_items_empty(self):
        set_mock_mode("empty")
        provider = MockZabbixProvider()
        result = await provider.get_items()
        assert result["total_count"] == 0

    @pytest.mark.asyncio
    async def test_dashboards_empty(self):
        set_mock_mode("empty")
        provider = MockZabbixProvider()
        result = await provider.get_dashboards()
        assert result["total_count"] == 0

    @pytest.mark.asyncio
    async def test_maps_empty(self):
        set_mock_mode("empty")
        provider = MockZabbixProvider()
        result = await provider.get_maps()
        assert result["total_count"] == 0

    @pytest.mark.asyncio
    async def test_history_empty(self):
        set_mock_mode("empty")
        provider = MockZabbixProvider()
        result = await provider.get_history()
        assert result["total_count"] == 0


# ------------------------------------------------------------------ #
# Mock Provider — Timeout Mode                                        #
# ------------------------------------------------------------------ #


class TestMockTimeout:
    @pytest.mark.asyncio
    async def test_connection_fails(self):
        set_mock_mode("timeout")
        provider = MockZabbixProvider()
        result = await provider.test_connection()
        assert result["connected"] is False

    @pytest.mark.asyncio
    async def test_summary_fails(self):
        set_mock_mode("timeout")
        provider = MockZabbixProvider()
        result = await provider.get_summary()
        assert result["connected"] is False


# ------------------------------------------------------------------ #
# Provider Factory                                                    #
# ------------------------------------------------------------------ #


class TestProviderFactory:
    def setup_method(self):
        reset_zabbix_provider()

    def teardown_method(self):
        reset_zabbix_provider()

    def test_returns_mock_when_not_configured(self):
        provider = get_zabbix_provider()
        assert isinstance(provider, MockZabbixProvider)

    def test_is_singleton(self):
        p1 = get_zabbix_provider()
        p2 = get_zabbix_provider()
        assert p1 is p2

    def test_reset_clears_singleton(self):
        p1 = get_zabbix_provider()
        reset_zabbix_provider()
        p2 = get_zabbix_provider()
        assert p1 is not p2

    def test_mock_mode_setter(self):
        provider = MockZabbixProvider()
        set_mock_mode("offline")
        assert provider._should_fail() is True
        set_mock_mode("healthy")
        assert provider._should_fail() is False


# ------------------------------------------------------------------ #
# Production Provider — Configuration Tests                           #
# ------------------------------------------------------------------ #


class TestApiZabbixProviderConfig:
    def test_provider_is_abc_subclass(self):
        assert issubclass(ApiZabbixProvider, ZabbixProvider)

    def test_provider_instantiates(self):
        provider = ApiZabbixProvider()
        assert provider._auth_token is None
        assert provider._request_id == 0

    @pytest.mark.asyncio
    async def test_test_connection_when_not_configured(self):
        provider = ApiZabbixProvider()
        result = await provider.test_connection()
        assert result["connected"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_login_when_not_configured(self):
        provider = ApiZabbixProvider()
        result = await provider.login()
        assert result.get("connected") is False or result.get("success") is False

    @pytest.mark.asyncio
    async def test_logout_always_succeeds(self):
        provider = ApiZabbixProvider()
        result = await provider.logout()
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_get_summary_when_not_configured(self):
        provider = ApiZabbixProvider()
        result = await provider.get_summary()
        assert result["connected"] is False

    @pytest.mark.asyncio
    async def test_get_hosts_when_not_configured(self):
        provider = ApiZabbixProvider()
        result = await provider.get_hosts()
        assert result["connected"] is False

    @pytest.mark.asyncio
    async def test_get_health_when_not_configured(self):
        provider = ApiZabbixProvider()
        result = await provider.get_health()
        assert result["connected"] is False

    def test_next_id_increments(self):
        provider = ApiZabbixProvider()
        assert provider._next_id() == 1
        assert provider._next_id() == 2
        assert provider._next_id() == 3


# ------------------------------------------------------------------ #
# Schema Validation Tests                                             #
# ------------------------------------------------------------------ #


class TestZabbixSchemas:
    def test_summary_response_valid(self):
        from app.schemas.zabbix import ZabbixSummaryResponse
        resp = ZabbixSummaryResponse(
            connected=True, version="7.0.0", host_count=42,
            problem_count=3, critical_count=1, warning_count=2,
        )
        assert resp.connected is True
        assert resp.host_count == 42

    def test_hosts_response_valid(self):
        from app.schemas.zabbix import ZabbixHost, ZabbixHostsResponse
        host = ZabbixHost(
            hostid="1", host="server1", name="Server 1",
            status="enabled", available="available",
        )
        resp = ZabbixHostsResponse(connected=True, hosts=[host], total_count=1)
        assert resp.total_count == 1
        assert resp.hosts[0].host == "server1"

    def test_host_groups_response_valid(self):
        from app.schemas.zabbix import ZabbixHostGroup, ZabbixHostGroupsResponse
        group = ZabbixHostGroup(groupid="1", name="Linux", host_count=5)
        resp = ZabbixHostGroupsResponse(connected=True, groups=[group], total_count=1)
        assert resp.groups[0].name == "Linux"

    def test_triggers_response_valid(self):
        from app.schemas.zabbix import ZabbixTrigger, ZabbixTriggersResponse
        trigger = ZabbixTrigger(
            triggerid="1", description="CPU high", status="enabled",
            priority="high", value="PROBLEM", hosts=["host1"],
        )
        resp = ZabbixTriggersResponse(connected=True, triggers=[trigger], total_count=1)
        assert resp.triggers[0].priority == "high"

    def test_problems_response_valid(self):
        from app.schemas.zabbix import ZabbixProblem, ZabbixProblemsResponse
        problem = ZabbixProblem(
            eventid="1001", name="CPU load", severity="high",
            status="PROBLEM", acknowledged=False, host="host1",
            timestamp="2026-01-01T00:00:00Z",
        )
        resp = ZabbixProblemsResponse(
            connected=True, problems=[problem], total_count=1,
            severity_counts={"high": 1},
        )
        assert resp.problems[0].acknowledged is False

    def test_events_response_valid(self):
        from app.schemas.zabbix import ZabbixEvent, ZabbixEventsResponse
        event = ZabbixEvent(
            eventid="2001", name="Event 1", severity="info",
            status="OK", host="host1", timestamp="2026-01-01T00:00:00Z",
        )
        resp = ZabbixEventsResponse(connected=True, events=[event], total_count=1)
        assert len(resp.events) == 1

    def test_items_response_valid(self):
        from app.schemas.zabbix import ZabbixItem, ZabbixItemsResponse
        item = ZabbixItem(
            itemid="1", name="CPU load", status="enabled",
            type="Zabbix agent", last_value="50.0", host="host1",
        )
        resp = ZabbixItemsResponse(connected=True, items=[item], total_count=1)
        assert resp.items[0].last_value == "50.0"

    def test_templates_response_valid(self):
        from app.schemas.zabbix import ZabbixTemplate, ZabbixTemplatesResponse
        tpl = ZabbixTemplate(templateid="1", name="Linux Template", hosts_count=5)
        resp = ZabbixTemplatesResponse(connected=True, templates=[tpl], total_count=1)
        assert resp.templates[0].hosts_count == 5

    def test_dashboards_response_valid(self):
        from app.schemas.zabbix import ZabbixDashboard, ZabbixDashboardsResponse
        dash = ZabbixDashboard(
            dashboardid="1", name="Prod Overview",
            owner="admin", pages=3,
        )
        resp = ZabbixDashboardsResponse(
            connected=True, dashboards=[dash], total_count=1,
        )
        assert resp.dashboards[0].pages == 3

    def test_maps_response_valid(self):
        from app.schemas.zabbix import ZabbixMap, ZabbixMapsResponse
        m = ZabbixMap(sysmapid="1", name="Network", width=1200, height=800, elements=15)
        resp = ZabbixMapsResponse(connected=True, maps=[m], total_count=1)
        assert resp.maps[0].elements == 15

    def test_health_response_valid(self):
        from app.schemas.zabbix import ZabbixHealthResponse
        resp = ZabbixHealthResponse(
            connected=True, status="healthy", version="7.0.0",
            server="zabbix.corp.local",
        )
        assert resp.status == "healthy"

    def test_health_default_database(self):
        from app.schemas.zabbix import ZabbixHealthResponse
        resp = ZabbixHealthResponse(connected=True)
        assert resp.database.status == "unknown"

    def test_connection_test_response_valid(self):
        from app.schemas.zabbix import ZabbixConnectionTestResponse
        resp = ZabbixConnectionTestResponse(
            connected=True, latency_ms=23, message="OK",
        )
        assert resp.latency_ms == 23

    def test_empty_responses_valid(self):
        from app.schemas.zabbix import (
            ZabbixDashboardsResponse,
            ZabbixEventsResponse,
            ZabbixHostGroupsResponse,
            ZabbixHostsResponse,
            ZabbixItemsResponse,
            ZabbixMapsResponse,
            ZabbixProblemsResponse,
            ZabbixTemplatesResponse,
            ZabbixTriggersResponse,
        )
        for cls in [
            ZabbixHostsResponse, ZabbixHostGroupsResponse,
            ZabbixTriggersResponse, ZabbixProblemsResponse,
            ZabbixEventsResponse, ZabbixItemsResponse,
            ZabbixTemplatesResponse, ZabbixDashboardsResponse,
            ZabbixMapsResponse,
        ]:
            resp = cls(connected=True)
            assert resp.connected is True

    def test_disconnected_with_error(self):
        from app.schemas.zabbix import ZabbixHostsResponse
        resp = ZabbixHostsResponse(connected=False, error="Connection refused")
        assert resp.error == "Connection refused"
        assert resp.hosts == []


# ------------------------------------------------------------------ #
# Router Endpoint Tests                                               #
# ------------------------------------------------------------------ #


class TestZabbixRouterEndpoints:
    """Test all 12 API endpoints via the test client."""

    @pytest.mark.asyncio
    async def test_overview_endpoint(self, client):
        resp = client.get("/api/v1/zabbix/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert "connected" in data
        assert "host_count" in data

    @pytest.mark.asyncio
    async def test_hosts_endpoint(self, client):
        resp = client.get("/api/v1/zabbix/hosts")
        assert resp.status_code == 200
        data = resp.json()
        assert "hosts" in data
        assert "total_count" in data

    @pytest.mark.asyncio
    async def test_groups_endpoint(self, client):
        resp = client.get("/api/v1/zabbix/groups")
        assert resp.status_code == 200
        data = resp.json()
        assert "groups" in data

    @pytest.mark.asyncio
    async def test_templates_endpoint(self, client):
        resp = client.get("/api/v1/zabbix/templates")
        assert resp.status_code == 200
        data = resp.json()
        assert "templates" in data

    @pytest.mark.asyncio
    async def test_items_endpoint(self, client):
        resp = client.get("/api/v1/zabbix/items")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data

    @pytest.mark.asyncio
    async def test_triggers_endpoint(self, client):
        resp = client.get("/api/v1/zabbix/triggers")
        assert resp.status_code == 200
        data = resp.json()
        assert "triggers" in data

    @pytest.mark.asyncio
    async def test_problems_endpoint(self, client):
        resp = client.get("/api/v1/zabbix/problems")
        assert resp.status_code == 200
        data = resp.json()
        assert "problems" in data

    @pytest.mark.asyncio
    async def test_events_endpoint(self, client):
        resp = client.get("/api/v1/zabbix/events")
        assert resp.status_code == 200
        data = resp.json()
        assert "events" in data

    @pytest.mark.asyncio
    async def test_maps_endpoint(self, client):
        resp = client.get("/api/v1/zabbix/maps")
        assert resp.status_code == 200
        data = resp.json()
        assert "maps" in data

    @pytest.mark.asyncio
    async def test_dashboards_endpoint(self, client):
        resp = client.get("/api/v1/zabbix/dashboards")
        assert resp.status_code == 200
        data = resp.json()
        assert "dashboards" in data

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        resp = client.get("/api/v1/zabbix/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data

    @pytest.mark.asyncio
    async def test_test_endpoint(self, client):
        resp = client.post("/api/v1/zabbix/test")
        assert resp.status_code == 200
        data = resp.json()
        assert "connected" in data


# ------------------------------------------------------------------ #
# Data Consistency Tests                                              #
# ------------------------------------------------------------------ #


class TestDataConsistency:
    @pytest.mark.asyncio
    async def test_host_groups_host_counts_positive(self):
        provider = MockZabbixProvider()
        result = await provider.get_host_groups()
        for group in result["groups"]:
            assert group["host_count"] >= 0

    @pytest.mark.asyncio
    async def test_trigger_value_is_valid(self):
        provider = MockZabbixProvider()
        result = await provider.get_triggers()
        for trigger in result["triggers"]:
            assert trigger["value"] in ("PROBLEM", "OK")

    @pytest.mark.asyncio
    async def test_host_status_is_valid(self):
        provider = MockZabbixProvider()
        result = await provider.get_hosts()
        for host in result["hosts"]:
            assert host["status"] in ("enabled", "disabled")
            assert host["available"] in ("available", "unavailable")

    @pytest.mark.asyncio
    async def test_problem_severity_is_valid(self):
        provider = MockZabbixProvider()
        result = await provider.get_problems()
        valid_severities = {"info", "warning", "high", "disaster"}
        for problem in result["problems"]:
            assert problem["severity"] in valid_severities

    @pytest.mark.asyncio
    async def test_event_severity_is_valid(self):
        provider = MockZabbixProvider()
        result = await provider.get_events()
        valid_severities = {"info", "warning", "high", "disaster"}
        for event in result["events"]:
            assert event["severity"] in valid_severities

    @pytest.mark.asyncio
    async def test_item_type_is_valid(self):
        provider = MockZabbixProvider()
        result = await provider.get_items()
        for item in result["items"]:
            assert item["type"] in ("Zabbix agent", "External check")

    @pytest.mark.asyncio
    async def test_all_endpoints_never_raise(self):
        """Providers must never raise exceptions — return error dicts."""
        for mode in ["healthy", "large", "offline", "auth_failure", "empty", "timeout"]:
            set_mock_mode(mode)
            provider = MockZabbixProvider()
            for method_name in [
                "test_connection", "login", "get_summary", "get_hosts",
                "get_host_groups", "get_triggers", "get_problems",
                "get_events", "get_items", "get_templates",
                "get_dashboards", "get_maps", "get_health", "get_history",
            ]:
                method = getattr(provider, method_name)
                result = await method()
                assert isinstance(result, dict), (
                    f"{method_name} raised or returned "
                    f"non-dict in {mode}"
                )


# ------------------------------------------------------------------ #
# Integration with Dashboard Service                                  #
# ------------------------------------------------------------------ #


class TestDashboardZabbixIntegration:
    @pytest.mark.asyncio
    async def test_dashboard_includes_zabbix_section(self, client, mock_docker):
        resp = client.get("/api/v1/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert "zabbix" in data
        assert "integrations" in data
        assert "count" in data["integrations"]
        assert "items" in data["integrations"]

    @pytest.mark.asyncio
    async def test_dashboard_zabbix_summary_fields(self, client, mock_docker):
        resp = client.get("/api/v1/dashboard")
        data = resp.json()
        zabbix = data["zabbix"]
        assert "connected" in zabbix
        assert "host_count" in zabbix or "hostCount" in zabbix
