"""TDD tests for the MSSQL/SQLCMD DB bridge in the Veeam agent plugin."""

import asyncio

from agent.plugins.veeam_plugin import VeeamPlugin


class _StubRelay(VeeamPlugin):
    """Captures the relayed PowerShell script instead of running it."""

    def __init__(self):
        super().__init__()
        self.captured = []
        self.probe_paths = {}
        self.script_result = {
            "success": True,
            "stdout": "127|Backup Job\n",
            "stderr": "",
        }

    async def _run_script_via_relay(self, script, timeout=60, target_id=None):
        self.captured.append(
            {"script": script, "timeout": timeout, "target_id": target_id}
        )
        return dict(self.script_result)

    async def _relay_path_exists(self, path, target_id=None):
        return bool(self.probe_paths.get(path))


def _run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


def test_mssql_builds_sqlcmd_powershell_and_uses_odbc130():
    p = _StubRelay()
    p.probe_paths = {
        r"C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\130\Tools\Binn\SQLCMD.EXE": True,
    }
    out = _run(p._run_db_query_via_relay("SELECT Id", target_id=12, db_type="mssql"))
    assert out is not None
    assert len(p.captured) == 1
    script = p.captured[0]["script"]
    # Uses SQLCMD, not psql
    assert "SQLCMD" in script
    assert "psql.exe" not in script
    # Picks the Veeam-bundled ODBC\130 path
    assert (
        r"C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\130\Tools\Binn\SQLCMD.EXE"
        in script
    )
    # Named Veeam instance and pipe-delimited output for _parse_psql_rows compatibility
    assert "VEEAMSQL2016" in script
    assert "-s '|'" in script


def test_auto_detect_uses_sqlcmd_when_no_psql():
    p = _StubRelay()
    p.probe_paths = {
        r"C:\Program Files\PostgreSQL\15\bin\psql.exe": False,
        r"C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\130\Tools\Binn\SQLCMD.EXE": True,
    }
    out = _run(p._run_db_query_via_relay("SELECT Id", target_id=12, db_type="auto"))
    assert out is not None
    script = p.captured[-1]["script"]
    assert "SQLCMD" in script
    assert "psql.exe" not in script


def test_postgres_still_builds_psql_powershell():
    p = _StubRelay()
    out = _run(
        p._run_db_query_via_relay("SELECT id", target_id=2, db_type="postgresql")
    )
    assert out is not None
    assert len(p.captured) == 1
    script = p.captured[0]["script"]
    assert "psql.exe" in script
    assert "SQLCMD" not in script
    assert "-h 127.0.0.1" in script


def test_db_detect_finds_sqlcmd_at_odbc130_when_no_psql():
    p = _StubRelay()
    # No psql binary, but SQLCMD present at ODBC\130 -> db_type mssql + sqlcmd_found.
    p.probe_paths = {
        r"C:\Program Files\PostgreSQL\15\bin\psql.exe": False,
        r"C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\170\Tools\Binn\SQLCMD.EXE": False,
        r"C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\130\Tools\Binn\SQLCMD.EXE": True,
    }
    result = _run(p._db_detect(target_id=12))
    assert result["success"] is True
    assert result["db_type"] == "mssql"
    assert result["sqlcmd_found"] is True
    assert result["psql_found"] is False


def test_db_detect_still_reports_postgres_when_psql_present():
    p = _StubRelay()
    p.probe_paths = {
        r"C:\Program Files\PostgreSQL\15\bin\psql.exe": True,
    }
    result = _run(p._db_detect(target_id=12))
    assert result["db_type"] == "postgresql"
    assert result["psql_found"] is True