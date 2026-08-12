"""
Mission Control Veeam Server Provider Tests

Tests for the plugin-side VeeamServerProvider: capability routing,
per-method source selection, and payload shapes.
"""

import json

import pytest

from app.plugins.installed.official_veeam.models import VeeamBackupServer
from app.plugins.installed.official_veeam.provider import (
    VeeamServerProvider,
    _rest_for,
    _agent_for,
)


class FakeRest:
    def __init__(self, **kw):
        self.calls: list[tuple] = []
        self.kw = kw

    async def test(self):
        self.calls.append(("test",))
        return {"connected": True, "version": "12.3", "name": "v1"}

    async def get(self, path):
        self.calls.append(("get", path))
        if path == "/api/v1/serverInfo":
            return {"buildVersion": "12.3", "name": "v1"}
        if path == "/api/v1/jobs":
            return {"data": [{"id": "j1", "name": "Daily"}]}
        return {"data": []}

    async def post(self, path, json=None):
        self.calls.append(("post", path))
        return {"success": True}


class FakeExecutor:
    def __init__(self, results):
        self._results = results
        self.ops = []

    async def run(self, op, params=None, timeout=120):
        self.ops.append(op)
        return self._results.get(op, {"success": True, "output": "[]", "stderr": "", "exit_code": 0})

    def json_result(self, op, data):
        return {"success": True, "output": json.dumps(data), "stderr": "", "exit_code": 0}


def make_provider(edition="enterprise", data_source="both", executor=None, rest=None):
    server = VeeamBackupServer(
        name="v1", edition=edition, data_source=data_source,
        db_type="postgresql", column_case="pascal",
        agent_id=1, target_id=2, rest_url="https://veeam:9419",
        rest_username="admin", rest_password_encrypted="enc",
    )
    return VeeamServerProvider(
        server=server, db=object(),
        executor=executor or FakeExecutor({}),
        rest=rest or FakeRest(),
    )


def test_routing_table_metadata():
    assert _rest_for("repositories", "enterprise", "api") is True
    assert _rest_for("repositories", "enterprise", "both") is True
    assert _rest_for("repositories", "enterprise", "ssh") is False
    assert _rest_for("repositories", "community", "ssh") is False


def test_routing_table_jobs_sessions():
    assert _agent_for("jobs", "enterprise", "api") is False
    assert _agent_for("jobs", "enterprise", "both") is True
    assert _agent_for("jobs", "community", "ssh") is True
    assert _rest_for("sessions", "enterprise", "both") is False


def test_routing_table_job_control():
    assert _rest_for("start_job", "enterprise", "both") is True
    assert _rest_for("stop_job", "community", "ssh") is False


@pytest.mark.anyio
async def test_community_get_jobs_uses_agent():
    executor = FakeExecutor({})
    executor._results["veeam:jobs"] = executor.json_result("veeam:jobs", {
        "jobs": [{"id": "j1", "name": "Daily"}],
    })
    provider = make_provider(edition="community", data_source="ssh", executor=executor)
    result = await provider.get_jobs()
    assert result["success"] is True
    assert executor.ops == ["veeam:jobs"]


@pytest.mark.anyio
async def test_enterprise_api_get_jobs_uses_rest():
    rest = FakeRest()
    executor = FakeExecutor({})
    provider = make_provider(edition="enterprise", data_source="api", executor=executor, rest=rest)
    result = await provider.get_jobs()
    assert result["success"] is True
    assert any(c[0] == "get" and c[1] == "/api/v1/jobs" for c in rest.calls)
    assert executor.ops == []


@pytest.mark.anyio
async def test_enterprise_both_jobs_use_agent_metadata_rest():
    executor = FakeExecutor({})
    executor._results["veeam:jobs"] = executor.json_result("veeam:jobs", {
        "jobs": [{"id": "j1", "name": "Daily"}],
    })
    provider = make_provider(edition="enterprise", data_source="both", executor=executor)
    jobs = await provider.get_jobs()
    assert executor.ops == ["veeam:jobs"]
    repos = await provider.get_repositories()
    assert repos["success"] is True
    assert any(c[0] == "get" and c[1] == "/api/v1/backupInfrastructure/repositories" for c in provider.rest.calls)


@pytest.mark.anyio
async def test_health_reports_via_rest_for_enterprise():
    provider = make_provider(edition="enterprise", data_source="both")
    health = await provider.get_health()
    assert health["healthy"] is True
    assert health["version"] == "12.3"


@pytest.mark.anyio
async def test_start_stop_job_routes():
    rest = FakeRest()
    provider = make_provider(edition="enterprise", data_source="both", rest=rest)
    started = await provider.start_job("j1")
    assert started["success"] is True
    assert ("post", "/api/v1/jobs/j1/start") in rest.calls
