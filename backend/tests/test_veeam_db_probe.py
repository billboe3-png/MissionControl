"""Tests for the plugin-side Veeam DB probe + query runners."""

from app.plugins.installed.official_veeam import db_probe, sql_queries


class FakeExecutor:
    """Minimal executor double returning canned op results."""

    def __init__(self, results: dict):
        self._results = results
        self.ops: list[tuple] = []

    async def run(self, op: str, params: dict | None = None, timeout: int = 120):
        self.ops.append((op, params))
        return self._results.get(op, {"success": False, "output": "", "error": "no canned result"})


def test_job_stats_sql_pg_and_mssql_pascal():
    pg = sql_queries.job_stats_sql("postgresql", "pascal")
    mssql = sql_queries.job_stats_sql("mssql", "pascal")
    assert '"backup.model.jobsessions"' in pg
    assert "[Backup.Model.JobSessions]" in mssql
    assert "js.JobName" in mssql


def test_job_stats_sql_mssql_snake_case():
    sql = sql_queries.job_stats_sql("mssql", "snake")
    assert "js.job_name" in sql
    assert "js.JobName" not in sql


async def test_detect_db_type_returns_probe_detail():
    executor = FakeExecutor({
        "veeam:db:detect": {
            "success": True,
            "db_type": "postgresql",
            "psql_found": True,
            "sqlcmd_found": False,
            "pg_port": True,
            "mssql_port": False,
        },
    })
    result = await db_probe.detect_db_type(executor)
    assert result["db_type"] == "postgresql"
    assert result["psql_found"] is True
    assert result["error"] is None
    assert executor.ops[0][0] == "veeam:db:detect"


async def test_detect_db_type_error_surfaces():
    executor = FakeExecutor({
        "veeam:db:detect": {"success": False, "error": "Permission denied"},
    })
    result = await db_probe.detect_db_type(executor)
    assert result["db_type"] is None
    assert "Permission denied" in result["error"]


async def test_run_db_query_dispatches_with_sql_param():
    executor = FakeExecutor({
        "veeam:db:query": {"success": True, "output": "row|1", "stderr": "", "exit_code": 0},
    })
    result = await db_probe.run_db_query(
        executor, sql="SELECT 1", db_type="postgresql", column_case="pascal"
    )
    assert result["success"] is True
    assert result["output"] == "row|1"
    _, params = executor.ops[0]
    assert params["sql"] == "SELECT 1"
    assert params["db_type"] == "postgresql"
