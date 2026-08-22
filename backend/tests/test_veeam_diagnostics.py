"""
Tests for Veeam multi-stage connection diagnostics.
"""

import pytest

from app.plugins.installed.official_veeam.diagnostics import run_connection_diagnostics
from app.plugins.installed.official_veeam.models import VeeamBackupServer
from app.plugins.installed.official_veeam.provider import VeeamServerProvider


class FakeRest:
    def __init__(self, connected=True, error=None):
        self.connected = connected
        self.error = error
        self.calls = []

    async def test(self):
        self.calls.append("test")
        if not self.connected:
            return {"connected": False, "error": self.error or "REST connection failed"}
        return {"connected": True, "version": "12.3", "name": "v1"}


class FakeExecutor:
    def __init__(self, results=None):
        self._results = results or {}
        self.ops = []

    async def run(self, op, params=None, timeout=120):
        self.ops.append((op, params))
        return self._results.get(op, {"success": True, "output": "[]", "stderr": "", "exit_code": 0})


class FakeSession:
    def __init__(self):
        self.committed = False

    def commit(self):
        self.committed = True


def make_test_provider(edition="enterprise", data_source="both", db_type="postgresql", executor_results=None, rest_connected=True, rest_error=None):
    server = VeeamBackupServer(
        name="v1",
        edition=edition,
        data_source=data_source,
        db_type=db_type,
        column_case="pascal",
        rest_url="https://veeam:9419",
    )
    executor = FakeExecutor(executor_results)
    rest = FakeRest(connected=rest_connected, error=rest_error)
    session = FakeSession()
    provider = VeeamServerProvider(server=server, db=session, executor=executor, rest=rest)
    return provider, server, session


@pytest.mark.anyio
async def test_diagnostics_success():
    executor_results = {
        "veeam:test": {"success": True, "output": '{"rest_available": true, "powershell_available": true}'},
        "veeam:db:detect": {
            "success": True,
            "db_type": "postgresql",
            "psql_found": True,
            "sqlcmd_found": False,
            "pg_port": True,
            "mssql_port": False,
        },
    }
    provider, _, _ = make_test_provider(executor_results=executor_results)
    result = await run_connection_diagnostics(provider)

    assert result["success"] is True
    assert result["agent_link"]["success"] is True
    assert result["rest"]["connected"] is True
    assert result["db"]["db_type"] == "postgresql"
    assert isinstance(result["recommendations"], list)


@pytest.mark.anyio
async def test_diagnostics_agent_failure():
    executor_results = {
        "veeam:test": {"success": False, "error": "SSH connection refused"},
        "veeam:db:detect": {"success": False, "error": "SSH connection refused"},
    }
    provider, _, _ = make_test_provider(executor_results=executor_results)
    result = await run_connection_diagnostics(provider)

    assert result["agent_link"]["success"] is False
    assert "SSH connection refused" in result["agent_link"]["error"]


@pytest.mark.anyio
async def test_diagnostics_rest_failure():
    provider, _, _ = make_test_provider(rest_connected=False, rest_error="Unauthorized")
    result = await run_connection_diagnostics(provider)

    assert result["rest"]["connected"] is False
    assert "Unauthorized" in result["rest"]["error"]


@pytest.mark.anyio
async def test_diagnostics_db_probe_failure():
    executor_results = {
        "veeam:test": {"success": True, "output": "{}"},
        "veeam:db:detect": {"success": False, "error": "psql not found"},
    }
    provider, _, _ = make_test_provider(executor_results=executor_results)
    result = await run_connection_diagnostics(provider)

    assert result["db"]["db_type"] is None
    assert "psql not found" in result["db"]["error"]


@pytest.mark.anyio
async def test_diagnostics_auto_db_writeback():
    executor_results = {
        "veeam:test": {"success": True, "output": "{}"},
        "veeam:db:detect": {
            "success": True,
            "db_type": "mssql",
            "psql_found": False,
            "sqlcmd_found": True,
            "pg_port": False,
            "mssql_port": True,
        },
    }
    provider, server, session = make_test_provider(db_type="auto", executor_results=executor_results)
    result = await run_connection_diagnostics(provider)

    assert result["success"] is True
    assert server.db_type == "mssql"
    assert session.committed is True


@pytest.mark.anyio
async def test_diagnostics_never_raises():
    class BadProvider:
        @property
        def server(self):
            raise RuntimeError("Boom")

        @property
        def rest(self):
            raise RuntimeError("Boom")

        @property
        def executor(self):
            raise RuntimeError("Boom")

    result = await run_connection_diagnostics(BadProvider())
    assert result["success"] is False
    assert "Boom" in result["error"]


@pytest.mark.anyio
async def test_diagnostics_both_fallback_requires_db():
    executor_results = {
        "veeam:test": {"success": True, "output": "{}"},
        "veeam:db:detect": {"success": False, "error": "psql not found"},
    }
    provider, _, _ = make_test_provider(
        edition="enterprise", data_source="both",
        executor_results=executor_results, rest_connected=False,
    )
    result = await run_connection_diagnostics(provider)
    assert result["success"] is False
    assert result["error"] is not None


@pytest.mark.anyio
async def test_diagnostics_both_fallback_success_when_db_ok():
    executor_results = {
        "veeam:test": {"success": True, "output": "{}"},
        "veeam:db:detect": {
            "success": True,
            "db_type": "postgresql",
            "psql_found": True,
            "sqlcmd_found": False,
            "pg_port": True,
            "mssql_port": False,
        },
    }
    provider, _, _ = make_test_provider(
        edition="enterprise", data_source="both",
        executor_results=executor_results, rest_connected=False,
    )
    result = await run_connection_diagnostics(provider)
    assert result["success"] is True


@pytest.mark.anyio
async def test_diagnostics_api_mode_ignores_agent_db_noise():
    provider, _, _ = make_test_provider(
        edition="enterprise", data_source="api",
        executor_results={}, rest_connected=False, rest_error="Unauthorized",
    )
    result = await run_connection_diagnostics(provider)
    assert result["success"] is False
    assert "REST:" in result["error"]
    assert "Agent:" not in result["error"]
    assert "DB:" not in result["error"]
    assert not any("SSH" in r or "psql" in r for r in result["recommendations"])


@pytest.mark.anyio
async def test_diagnostics_community_mode_ignores_rest_noise():
    executor_results = {
        "veeam:test": {"success": True, "output": "{}"},
        "veeam:db:detect": {
            "success": True,
            "db_type": "postgresql",
            "psql_found": True,
            "sqlcmd_found": False,
            "pg_port": True,
            "mssql_port": False,
        },
    }
    provider, _, _ = make_test_provider(
        edition="community", data_source="ssh",
        executor_results=executor_results, rest_connected=False,
    )
    result = await run_connection_diagnostics(provider)
    assert result["success"] is True
    assert not any("REST" in r for r in result["recommendations"])
