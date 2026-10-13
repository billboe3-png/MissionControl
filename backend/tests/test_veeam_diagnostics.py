"""
Tests for Veeam multi-stage connection diagnostics.
"""

import json

import pytest

from app.plugins.installed.official_veeam.diagnostics import (
    run_connection_diagnostics,
    run_server_diagnostics,
)
from app.plugins.installed.official_veeam.models import VeeamBackupServer


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


class FakeProvider:
    """Duck-typed stand-in for the provider interface diagnostics consumes."""

    def __init__(self, server, executor, rest, db=None):
        self.server = server
        self.executor = executor
        self.rest = rest
        self._db = db
        self.db = db


def make_test_provider(edition="enterprise", data_source="both", db_type="postgresql", executor_results=None, rest_connected=True, rest_error=None):
    server = VeeamBackupServer(
        name="v1",
        edition=edition,
        data_source=data_source,
        db_type=db_type,
        column_case="pascal",
        url="https://veeam:9419",
    )
    executor = FakeExecutor(executor_results)
    rest = FakeRest(connected=rest_connected, error=rest_error)
    session = FakeSession()
    provider = FakeProvider(server=server, executor=executor, rest=rest, db=session)
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


class RelayExecutor:
    """Fake AgentSshExecutor whose `run` hands back SshResult-style dicts."""

    def __init__(self, results=None):
        self.results = results or {}
        self.ops = []

    async def run(self, op, params=None, timeout=120):
        self.ops.append((op, params))
        return self.results.get(
            op,
            {"success": True, "output": "{}", "stderr": "", "exit_code": 0, "error": None},
        )


def fake_build_for(executor, monkeypatch):
    def _build(_db, _server):
        return executor

    monkeypatch.setattr(
        "app.plugins.installed.official_veeam.diagnostics.build_ssh_executor",
        _build,
    )
    return executor


def diag_server(**kw):
    defaults = {
        "name": "v1", "edition": "enterprise", "data_source": "both", "db_type": "postgresql",
        "column_case": "pascal", "agent_id": 10, "target_id": 20, "enabled": True,
    }
    defaults.update(kw)
    return VeeamBackupServer(**defaults)


@pytest.mark.anyio
async def test_server_diagnostics_success(monkeypatch):
    executor = fake_build_for(
        RelayExecutor(
            {
                "veeam:test": {
                    "success": True,
                    "output": json.dumps(
                        {"success": True, "db_available": True, "rest_available": True,
                         "powershell_available": True}
                    ),
                    "stderr": "", "exit_code": 0, "error": None,
                },
                "veeam:db:detect": {
                    "success": True,
                    "output": json.dumps(
                        {"db_type": "postgresql", "psql_found": True, "sqlcmd_found": False,
                         "pg_port": True, "mssql_port": False}
                    ),
                    "stderr": "", "exit_code": 0, "error": None,
                },
                "veeam:db:query": {
                    "success": True,
                    "output": json.dumps({"success": True, "output": "1", "stderr": "", "exit_code": 0}),
                    "stderr": "", "exit_code": 0, "error": None,
                },
            }
        ),
        monkeypatch,
    )
    result = await run_server_diagnostics(db=None, server=diag_server())

    assert result["success"] is True
    assert result["server"]["id"] is None
    assert result["agent"]["db_available"] is True
    assert result["db_detect"]["psql_found"] is True
    assert result["db_detect"]["db_type"] == "postgresql"
    assert result["db_query"]["success"] is True
    assert any("healthy" in r for r in result["recommendations"])
    assert ("veeam:test", None) in executor.ops
    assert ("veeam:db:query", {"sql": "SELECT 1", "db_type": "postgresql"}) in executor.ops


@pytest.mark.anyio
async def test_server_diagnostics_no_agent_target(monkeypatch):
    def _build(_db, _server):
        raise AssertionError("should not build executor without agent/target")

    monkeypatch.setattr(
        "app.plugins.installed.official_veeam.diagnostics.build_ssh_executor", _build
    )
    result = await run_server_diagnostics(db=None, server=diag_server(agent_id=None, target_id=None))

    assert result["success"] is False
    assert "No agent/remote target" in result["error"]
    assert any("Link this Veeam server" in r for r in result["recommendations"])


@pytest.mark.anyio
async def test_server_diagnostics_agent_offline(monkeypatch):
    fake_build_for(
        RelayExecutor(
            {"veeam:test": {"success": False, "error": "Agent 'a1' is offline",
                            "output": "", "stderr": "", "exit_code": 1}}
        ),
        monkeypatch,
    )
    result = await run_server_diagnostics(db=None, server=diag_server())

    assert result["success"] is False
    assert result["agent"]["error"] == "Agent 'a1' is offline"
    assert any("Agent relay failed" in r for r in result["recommendations"])


@pytest.mark.anyio
async def test_server_diagnostics_db_unavailable(monkeypatch):
    fake_build_for(
        RelayExecutor(
            {
                "veeam:test": {
                    "success": True,
                    "output": json.dumps(
                        {"success": True, "db_available": False,
                         "rest_available": False, "powershell_available": False}
                    ),
                    "stderr": "", "exit_code": 0, "error": None,
                },
                "veeam:db:detect": {
                    "success": True,
                    "output": json.dumps(
                        {"db_type": "postgresql", "psql_found": True, "sqlcmd_found": False,
                         "pg_port": True, "mssql_port": False}
                    ),
                    "stderr": "", "exit_code": 0, "error": None,
                },
                "veeam:db:query": {
                    "success": True,
                    "output": json.dumps({"success": False, "error": "DB query failed",
                                          "stderr": "", "exit_code": 1}),
                    "stderr": "", "exit_code": 0, "error": None,
                },
            }
        ),
        monkeypatch,
    )
    result = await run_server_diagnostics(db=None, server=diag_server())

    assert result["success"] is False
    assert result["db_query"]["success"] is False
    assert result["error"] == "DB query failed"
    assert any("not reachable" in r for r in result["recommendations"])
    assert any("DB query failed" in r for r in result["recommendations"])


@pytest.mark.anyio
async def test_server_diagnostics_no_db_clients_found(monkeypatch):
    fake_build_for(
        RelayExecutor(
            {
                "veeam:test": {
                    "success": True,
                    "output": json.dumps(
                        {"success": True, "db_available": True,
                         "rest_available": True, "powershell_available": True}
                    ),
                    "stderr": "", "exit_code": 0, "error": None,
                },
                "veeam:db:detect": {
                    "success": True,
                    "output": json.dumps(
                        {"db_type": None, "psql_found": False, "sqlcmd_found": False,
                         "pg_port": False, "mssql_port": False}
                    ),
                    "stderr": "", "exit_code": 0, "error": None,
                },
                "veeam:db:query": {
                    "success": True,
                    "output": json.dumps({"success": False, "error": "DB query failed",
                                          "stderr": "", "exit_code": 1}),
                    "stderr": "", "exit_code": 0, "error": None,
                },
            }
        ),
        monkeypatch,
    )
    result = await run_server_diagnostics(db=None, server=diag_server())

    assert result["success"] is False
    assert any("neither psql.exe nor sqlcmd.exe" in r.lower() for r in result["recommendations"])


@pytest.mark.anyio
async def test_server_diagnostics_build_raises(monkeypatch):
    def _build(_db, _server):
        raise ValueError("boom")

    monkeypatch.setattr(
        "app.plugins.installed.official_veeam.diagnostics.build_ssh_executor", _build
    )
    result = await run_server_diagnostics(db=None, server=diag_server())

    assert result["success"] is False
    assert "boom" in result["error"]
    assert any("agent/target configuration" in r for r in result["recommendations"])


@pytest.mark.anyio
async def test_server_diagnostics_uses_configured_db_type(monkeypatch):
    executor = fake_build_for(
        RelayExecutor(
            {
                "veeam:test": {
                    "success": True,
                    "output": json.dumps({"success": True, "db_available": True}),
                    "stderr": "", "exit_code": 0, "error": None,
                },
                "veeam:db:detect": {
                    "success": True,
                    "output": json.dumps(
                        {"db_type": "mssql", "psql_found": False, "sqlcmd_found": True,
                         "pg_port": False, "mssql_port": True}
                    ),
                    "stderr": "", "exit_code": 0, "error": None,
                },
                "veeam:db:query": {
                    "success": True,
                    "output": json.dumps({"success": True, "output": "1", "stderr": "", "exit_code": 0}),
                    "stderr": "", "exit_code": 0, "error": None,
                },
            }
        ),
        monkeypatch,
    )
    result = await run_server_diagnostics(db=None, server=diag_server(db_type="auto"))

    assert result["success"] is True
    query_call = [op for op in executor.ops if op[0] == "veeam:db:query"]
    assert query_call[0][1] == {"sql": "SELECT 1", "db_type": "mssql"}


@pytest.mark.anyio
async def test_server_diagnostics_db_type_mismatch_recommendation(monkeypatch):
    fake_build_for(
        RelayExecutor(
            {
                "veeam:test": {
                    "success": True,
                    "output": json.dumps({"success": True, "db_available": True}),
                    "stderr": "", "exit_code": 0, "error": None,
                },
                "veeam:db:detect": {
                    "success": True,
                    "output": json.dumps(
                        {"db_type": "mssql", "psql_found": True, "sqlcmd_found": True,
                         "pg_port": True, "mssql_port": True}
                    ),
                    "stderr": "", "exit_code": 0, "error": None,
                },
                "veeam:db:query": {
                    "success": True,
                    "output": json.dumps({"success": False, "error": "Veeam DB query failed",
                                          "stderr": "", "exit_code": 1}),
                    "stderr": "", "exit_code": 0, "error": None,
                },
            }
        ),
        monkeypatch,
    )
    result = await run_server_diagnostics(db=None, server=diag_server(db_type="postgresql"))

    assert result["success"] is False
    assert any("Update this server's db_type to 'mssql'" in r for r in result["recommendations"])
