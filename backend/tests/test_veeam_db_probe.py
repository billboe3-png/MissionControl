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


PARENT_ONLY_PG = "regexp_replace(js.job_name, ' - [A-Za-z0-9._]+$', '') = js.job_name"
PARENT_ONLY_MSSQL_PASCAL = "CHARINDEX(' - ', js.JobName) = 0"
PARENT_ONLY_MSSQL_SNAKE = "CHARINDEX(' - ', js.job_name) = 0"

CHILD_PREFERENCE = (
    "(p.has_child = 1 AND b.is_parent = 0) "
    "OR (p.has_child = 0 AND b.is_parent = 1)"
)


def test_stats_sql_count_parent_session_once():
    """Row-list queries must keep only the parent session per run.

    Veeam writes one parent session per run plus one child session per
    protected host (``<job> - <host>``) with identical byte counters; both
    normalize to the same name, so listing both would duplicate every run.
    Session and job-name listings still need exactly one row per run.

    The aggregate builders (``job_stats``/``job_stats_daily``) no longer use
    this fragment — see ``test_stats_aggregates_prefer_child_sessions``.
    """
    expected = {
        ("postgresql", "pascal"): PARENT_ONLY_PG,
        ("mssql", "pascal"): PARENT_ONLY_MSSQL_PASCAL,
        ("mssql", "snake"): PARENT_ONLY_MSSQL_SNAKE,
    }
    for (db_type, column_case), fragment in expected.items():
        for builder in (
            sql_queries.session_stats_sql,
            sql_queries.job_names_sql,
        ):
            sql = builder(db_type, column_case)
            assert fragment in sql, (
                f"{builder.__name__}({db_type!r}, {column_case!r}) "
                f"missing parent-only filter"
            )


def test_stats_aggregates_prefer_child_sessions():
    """Regression: agent/endpoint job counters live on the child session.

    For ``Exco_*`` jobs the parent row records zeros while the per-host child
    session holds the real byte counters. The aggregate builders must use the
    child rows whenever a job (or job/day) has any, and fall back to the
    parent row when it does not — never summing both.
    """
    for db_type, column_case in (
        ("postgresql", "pascal"),
        ("mssql", "pascal"),
        ("mssql", "snake"),
    ):
        for builder in (
            sql_queries.job_stats_sql,
            sql_queries.job_stats_daily_sql,
        ):
            sql = builder(db_type=db_type, column_case=column_case)
            assert "AS is_parent" in sql, f"{builder.__name__} missing is_parent"
            assert "has_child" in sql, f"{builder.__name__} missing has_child"
            assert CHILD_PREFERENCE in sql, (
                f"{builder.__name__}({db_type!r}, {column_case!r}) "
                f"missing parent/child preference"
            )
        daily = sql_queries.job_stats_daily_sql(db_type=db_type, column_case=column_case)
        assert "p.run_date = b.run_date" in daily


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
