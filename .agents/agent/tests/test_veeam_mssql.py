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


def raw_mssql_jobs():
    return (
        "99D1BF3D-E2E0-4BEC-B2B3-820C0B87D212|Backup Configuration Job|100|1|-1|2"
        "|2026-08-31 22:00:00|2026-08-31 22:30:00|100\n"
    )


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


# ---------- db_type-aware _db_collect (MSSQL schema) ----------

def test_collect_sql_mssql_jobs_uses_bjobs_and_applies():
    sql = VeeamPlugin._db_collect_sql("jobs", db_type="mssql")
    assert "FROM BJobs" in sql
    assert "[Backup.Model.JobSessions]" in sql
    assert "OUTER APPLY" in sql
    assert "is_deleted = 0" in sql


def test_collect_sql_postgres_jobs_uses_pg_schema():
    sql = VeeamPlugin._db_collect_sql("jobs", db_type="postgresql")
    assert "FROM bjobs" in sql
    assert '"backup.model.jobsessions"' in sql


def test_collect_sql_mssql_sessions_top200():
    sql = VeeamPlugin._db_collect_sql("sessions", db_type="mssql")
    assert sql.startswith("SELECT TOP 200")
    assert "[Backup.Model.JobSessions]" in sql


def test_collect_sql_mssql_repositories_uses_backuprepositories():
    sql = VeeamPlugin._db_collect_sql("repositories", db_type="mssql")
    assert "FROM BackupRepositories" in sql


class _StubDbQuery(_StubRelay):
    """Stub _db_collect's SQL execution to return fixed pipe rows."""

    def __init__(self, raw):
        super().__init__()
        self.raw = raw
        self.calls = []

    async def _run_db_query_via_relay(self, sql, target_id=None, timeout=120, db_type="auto"):
        self.calls.append({"sql": sql, "db_type": db_type})
        return self.raw


def test_collect_jobs_mssql_parses_rows_and_enabled():
    raw = (
        "99D1BF3D-E2E0-4BEC-B2B3-820C0B87D212|Backup Configuration Job|100|1|-1|2|2026-08-31 22:00:00|2026-08-31 22:30:00|100\n"
        "D9B80F7B-EE49-46D3-8F83-C880FBBF557A|BPFHBAPPSERVER_EXT|65|0|5|-1|2026-08-31 21:00:00|2026-08-31 21:30:00|50\n"
    )
    p = _StubDbQuery(raw)
    jobs = _run(p._db_collect("jobs", target_id=12))
    assert jobs is not None
    assert len(jobs) == 2
    assert jobs[0]["name"] == "Backup Configuration Job"
    assert jobs[0]["enabled"] is True
    assert jobs[1]["enabled"] is False
    assert jobs[0]["lastRun"]["result"] == {"result": "Failed"}


def test_collect_repos_mssql_parses_status():
    raw = (
        "4D7D0692-71F1-4067-876D-9EAFB1594903|Hybar NAS|desc|2|host|\\\\192.168.4.25\\Veeam_Backup|0|1\n"
        "7D275B4F-84CD-4434-BB33-B05A81A49E52|Daily_Drives|desc2|0|host2|F:\\|1|0\n"
    )
    p = _StubDbQuery(raw)
    repos = _run(p._db_collect("repositories", target_id=12))
    assert repos is not None
    assert len(repos) == 2
    assert repos[0]["name"] == "Hybar NAS"
    assert repos[0]["status"] == "Available"
    assert repos[1]["name"] == "Daily_Drives"
    assert repos[1]["status"] == "Unavailable"


def test_collect_sessions_mssql_parses_rows():
    raw = "DF21262B-2DED-43D9-BADA-001DD84153A8|5990DF12-D37F-4DC3-B867-D34190857A74|Backup Job|0|1|2026-08-31 22:00:00|2026-08-31 22:30:00|100\n"
    p = _StubDbQuery(raw)
    sessions = _run(p._db_collect("sessions", target_id=12))
    assert sessions is not None
    assert len(sessions) == 1
    assert sessions[0]["id"] == "DF21262B-2DED-43D9-BADA-001DD84153A8"
    assert sessions[0]["result"] == {"result": "Warning"}


# ---------- db_type propagation through relay ops ----------
# BHFP has a bundled psql.exe so binary-presence detection returns
# "postgresql", but the VeeamBackup DB is MSSQL. The backend must pass the
# authoritative db_type through the relay op args.

class _StubDbQueryNoPs(_StubDbQuery):
    """_run_collector_via_relay returns None (PS module dead on BPFH)."""

    async def _run_collector_via_relay(self, collector, target_id=None):
        return None


def test_db_collect_explicit_mssql_uses_mssql_sql():
    raw = "99D1BF3D-E2E0-4BEC-B2B3-820C0B87D212|Backup Configuration Job|100|1|-1|2|2026-08-31 22:00:00|2026-08-31 22:30:00|100\n"
    p = _StubDbQuery(raw)
    jobs = _run(p._db_collect("jobs", target_id=12, db_type="mssql"))
    assert jobs is not None
    assert len(jobs) == 1
    call = p.calls[-1]
    assert call["db_type"] == "mssql"
    assert "FROM BJobs" in call["sql"]


def test_db_collect_explicit_postgres_uses_pg_sql():
    raw = "99D1BF3D|Backup Configuration Job|100|1|-1|2|2026-08-31 22:00:00|2026-08-31 22:30:00|100\n"
    p = _StubDbQuery(raw)
    jobs = _run(p._db_collect("jobs", target_id=2, db_type="postgresql"))
    assert jobs is not None
    call = p.calls[-1]
    assert call["db_type"] == "postgresql"
    assert "FROM bjobs" in call["sql"]


def test_execute_relay_jobs_passes_db_type_to_db_collect():
    raw = "99D1BF3D-E2E0-4BEC-B2B3-820C0B87D212|Backup Configuration Job|100|1|-1|2|2026-08-31 22:00:00|2026-08-31 22:30:00|100\n"
    p = _StubDbQueryNoPs(raw)
    result = _run(p._execute_relay("veeam:jobs", {"target_id": 12, "db_type": "mssql"}))
    assert result["success"] is True
    assert p.calls and p.calls[-1]["db_type"] == "mssql"
    assert "FROM BJobs" in p.calls[-1]["sql"]


def test_execute_relay_jobs_without_db_type_falls_back_to_auto():
    raw = "99D1BF3D-E2E0-4BEC-B2B3-820C0B87D212|Backup Configuration Job|100|1|-1|2|2026-08-31 22:00:00|2026-08-31 22:30:00|100\n"
    p = _StubDbQueryNoPs(raw)
    result = _run(p._execute_relay("veeam:jobs", {"target_id": 12}))
    assert result["success"] is True
    assert p.calls and p.calls[-1]["db_type"] != "auto"
    assert "FROM BJobs" in p.calls[-1]["sql"]


def test_db_detect_prefers_explicit_db_type_over_psql_presence():
    """BPFH ships a bundled psql.exe but the VeeamBackup DB is MSSQL;
    binary-presence auto-detect would wrongly return postgresql, so an
    explicit db_type must win over _db_detect's psql_found heuristic."""
    p = _StubDbQueryNoPs(raw_mssql_jobs())
    p.probe_paths = {
        r"C:\Program Files\PostgreSQL\15\bin\psql.exe": True,
        r"C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\130\Tools\Binn\SQLCMD.EXE": True,
    }
    jobs = _run(p._db_collect("jobs", target_id=12, db_type="mssql"))
    assert jobs is not None
    assert p.calls and p.calls[-1]["db_type"] == "mssql"
    assert "FROM BJobs" in p.calls[-1]["sql"]


def test_collect_jobs_mssql_handles_nullable_columns():
    """MSSQL/SQLCMD prints the literal 'NULL' for NULL columns; parsing must
    coerce it (a job with no sessions has NULL creation_time/end_time/progress)."""
    raw = (
        "E952B512-2708-4EA4-8DC8-C32D805717A9|Transform job|22000|1|-1|-1|NULL|NULL|NULL\n"
    )
    p = _StubDbQuery(raw)
    jobs = _run(p._db_collect("jobs", target_id=12, db_type="mssql"))
    assert jobs is not None
    assert len(jobs) == 1
    assert jobs[0]["name"] == "Transform job"
    assert jobs[0]["lastRun"] is None
    assert jobs[0]["state"] in ("Stopped", "Unknown")


# ---------- stats collectors made db_type-aware ----------
# Dashboard stats panels relay veeam:job_stats / veeam:session_stats /
# veeam:job_stats_daily, which previously ran hardcoded PostgreSQL SQL and
# failed on MSSQL backup servers.  They now use the same explicit-db_type
# SQL builder as the jobs/sessions/repositories collectors.

def test_collect_sql_job_stats_mssql():
    sql = VeeamPlugin._db_collect_sql("job_stats", "mssql")
    assert "CHARINDEX(' - ', js.job_name)" in sql
    assert "FROM [Backup.Model.JobSessions] js" in sql
    assert "regexp_replace" not in sql
    assert "ISNULL(SUM(bs.total_size), 0)" in sql


def test_collect_sql_job_stats_postgres():
    sql = VeeamPlugin._db_collect_sql("job_stats", "postgresql")
    assert "regexp_replace(js.job_name" in sql
    assert '"backup.model.jobsessions" js' in sql
    assert "COALESCE(SUM(bs.total_size), 0)" in sql


def test_collect_sql_session_stats_mssql_top200():
    sql = VeeamPlugin._db_collect_sql("session_stats", "mssql")
    assert sql.startswith("SELECT TOP 200 js.id")
    assert "FROM [Backup.Model.JobSessions] js" in sql
    assert "LIMIT 200" not in sql


def test_collect_sql_job_stats_daily_mssql():
    sql = VeeamPlugin._db_collect_sql("job_stats_daily", "mssql", days=7)
    assert "DATEADD(day, -7, GETDATE())" in sql
    assert "CAST(js.creation_time AS DATE)" in sql
    assert "NOW() - INTERVAL" not in sql


def test_db_job_stats_mssql_parses_rows_and_null():
    raw = (
        "BPFHBAPPSERVER_EXT|12|322126844962|12345|100|200|40|2026-09-01 22:00:00|10|1|1\n"
        "Transform job|5|NULL|0|0|0|NULL|NULL|0|0|5\n"
    )
    p = _StubDbQuery(raw)
    jobs = _run(p._db_job_stats(target_id=12, db_type="mssql"))
    assert jobs is not None
    assert len(jobs) == 2
    assert jobs[0]["job_name"] == "BPFHBAPPSERVER_EXT"
    assert jobs[0]["session_count"] == 12
    assert jobs[0]["total_bytes"] == 322126844962
    assert jobs[0]["avg_speed"] == 40.0
    assert jobs[0]["failed_count"] == 1
    assert jobs[1]["session_count"] == 5
    assert jobs[1]["total_bytes"] == 0
    assert jobs[1]["last_run"] is None
    assert jobs[1]["failed_count"] == 5


def test_db_session_stats_mssql_parses_rows():
    raw = (
        "DF21262B-2DED-43D9-BADA-001DD84153A8|5990DF12-D37F-4DC3-B867-"
        "D34190857A74|Backup Job|0|2026-08-31 22:00:00|2026-08-31 22:30:00|1|100|200|300\n"
    )
    p = _StubDbQuery(raw)
    stats = _run(p._db_session_stats(target_id=12, db_type="mssql"))
    assert stats is not None
    assert len(stats) == 1
    assert stats[0]["job_name"] == "Backup Job"
    assert stats[0]["state"] == "0"
    assert stats[0]["processed_bytes"] == 100
    assert stats[0]["transferred_bytes"] == 300


def test_db_job_stats_daily_mssql_parses_rows():
    raw = (
        "BPFHBAPPSERVER_EXT|2026-09-01|100|10|20|2|2|0|0\n"
        "BPFHBAPPSERVER_EXT|2026-08-31|200|20|40|1|0|0|1\n"
    )
    p = _StubDbQuery(raw)
    jobs, dates = _run(p._db_job_stats_daily(7, target_id=12, db_type="mssql"))
    assert dates == ["2026-08-31", "2026-09-01"]
    assert jobs is not None and len(jobs) == 1
    daily = jobs[0]["daily"]
    assert daily["2026-09-01"]["session_count"] == 2
    assert daily["2026-09-01"]["result"] == "Success"
    assert daily["2026-08-31"]["result"] == "Failed"


def test_execute_relay_stats_pass_db_type_to_helpers():
    p = _StubDbQueryNoPs("")
    result = _run(p._execute_relay(
        "veeam:job_stats", {"target_id": 12, "db_type": "mssql"},
    ))
    assert result["success"] is True
    assert p.calls and p.calls[-1]["db_type"] == "mssql"
    assert "CHARINDEX(' - ', js.job_name)" in p.calls[-1]["sql"]


def test_execute_relay_session_stats_pass_db_type_to_helpers():
    p = _StubDbQueryNoPs("")
    result = _run(p._execute_relay(
        "veeam:session_stats", {"target_id": 12, "db_type": "mssql"},
    ))
    assert result["success"] is True
    assert p.calls and p.calls[-1]["db_type"] == "mssql"
    assert p.calls[-1]["sql"].startswith("SELECT TOP 200")


def test_execute_relay_job_stats_daily_pass_db_type_and_days():
    p = _StubDbQueryNoPs("")
    result = _run(p._execute_relay(
        "veeam:job_stats_daily", {"target_id": 12, "db_type": "mssql", "days": 7},
    ))
    assert result["success"] is True
    assert p.calls and p.calls[-1]["db_type"] == "mssql"
    assert "DATEADD(day, -7, GETDATE())" in p.calls[-1]["sql"]