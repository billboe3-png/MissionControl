# ruff: noqa: S608
"""\
SQL Query Builders for Veeam PostgreSQL and MSSQL Backends.

Provides identical query logic in both SQL dialects so the providers
can issue the correct syntax for the detected database engine.

MSSQL supports two column naming conventions:
- PascalCase (default, used by CORHQVEEAM)
- snake_case (used by some servers like ERFRF where the DB uses lowercase names)

NOTE: Every SQL string here is assembled only from module-level constants
(_NORM_NAME_*, _WHERE_FILTER_PG, _mssql_where) and the `days` parameter,
which job_stats_daily_sql coerces to int() before interpolation. No
caller-supplied string is ever concatenated into these queries, so the
S608 "possible injection" warnings are false positives for this builder.
"""

# ── Common WHERE filter (excludes system/internal jobs) ─────────────
_WHERE_FILTER_PG = """\
AND js.job_name NOT LIKE '%Resynchronize%'
AND js.job_name NOT LIKE '%Host Discovery%'
AND js.job_name NOT LIKE '%Foreign transform%'
AND js.job_name NOT LIKE '%Infrastructure update%'
AND js.job_name NOT LIKE '%Audit Logs%'
AND js.job_name NOT LIKE '%Catalog Cleanup%'
AND js.job_name NOT LIKE '%Shell run%'
AND js.job_name NOT LIKE '%Backup Configuration%'
AND js.job_name NOT LIKE '%Hyper-V CBT%'
AND js.job_name NOT LIKE '%Rescan%'
AND js.job_name NOT LIKE '%Checkpoint Removal%'
AND js.job_name NOT LIKE '%Retention job%'
AND js.job_name NOT LIKE '%Malware Detection%'"""

# ── Job name normalization ──────────────────────────────────────────
# PostgreSQL: regexp_replace strips trailing " - hostname"
_NORM_NAME_PG = "regexp_replace(js.job_name, ' - [A-Za-z0-9._]+$', '')"

# MSSQL PascalCase
_NORM_NAME_MSSQL_PASCAL = (
    "CASE WHEN CHARINDEX(' - ', js.JobName) > 0 "
    "THEN LEFT(js.JobName, CHARINDEX(' - ', js.JobName) - 1) "
    "ELSE js.JobName END"
)

# MSSQL snake_case
_NORM_NAME_MSSQL_SNAKE = (
    "CASE WHEN CHARINDEX(' - ', js.job_name) > 0 "
    "THEN LEFT(js.job_name, CHARINDEX(' - ', js.job_name) - 1) "
    "ELSE js.job_name END"
)


def _mssql_where(column_case: str = "pascal") -> str:
    """Return the WHERE filter for MSSQL with correct column casing."""
    if column_case == "snake":
        return """\
AND js.job_name NOT LIKE '%Resynchronize%'
AND js.job_name NOT LIKE '%Host Discovery%'
AND js.job_name NOT LIKE '%Foreign transform%'
AND js.job_name NOT LIKE '%Infrastructure update%'
AND js.job_name NOT LIKE '%Audit Logs%'
AND js.job_name NOT LIKE '%Catalog Cleanup%'
AND js.job_name NOT LIKE '%Shell run%'
AND js.job_name NOT LIKE '%Backup Configuration%'
AND js.job_name NOT LIKE '%Hyper-V CBT%'
AND js.job_name NOT LIKE '%Rescan%'
AND js.job_name NOT LIKE '%Checkpoint Removal%'
AND js.job_name NOT LIKE '%Retention job%'
AND js.job_name NOT LIKE '%Malware Detection%'"""
    return """\
AND js.JobName NOT LIKE '%Resynchronize%'
AND js.JobName NOT LIKE '%Host Discovery%'
AND js.JobName NOT LIKE '%Foreign transform%'
AND js.JobName NOT LIKE '%Infrastructure update%'
AND js.JobName NOT LIKE '%Audit Logs%'
AND js.JobName NOT LIKE '%Catalog Cleanup%'
AND js.JobName NOT LIKE '%Shell run%'
AND js.JobName NOT LIKE '%Backup Configuration%'
AND js.JobName NOT LIKE '%Hyper-V CBT%'
AND js.JobName NOT LIKE '%Rescan%'
AND js.JobName NOT LIKE '%Checkpoint Removal%'
AND js.JobName NOT LIKE '%Retention job%'
AND js.JobName NOT LIKE '%Malware Detection%'"""


def job_stats_sql(db_type: str = "postgresql", column_case: str = "pascal") -> str:
    """Aggregated transfer stats per job (all time)."""
    if db_type == "mssql":
        if column_case == "snake":
            norm = _NORM_NAME_MSSQL_SNAKE
            return f"""SELECT
    {norm} AS job_name,
    COUNT(*) AS session_count,
    ISNULL(SUM(bs.total_size), 0),
    ISNULL(SUM(bs.processed_size), 0),
    ISNULL(SUM(bs.read_size), 0),
    ISNULL(SUM(bs.stored_size), 0),
    ISNULL(AVG(bs.avg_speed), 0),
    MAX(js.creation_time),
    SUM(CASE WHEN js.result = 0 THEN 1 ELSE 0 END),
    SUM(CASE WHEN js.result = 1 THEN 1 ELSE 0 END),
    SUM(CASE WHEN js.result = 2 THEN 1 ELSE 0 END)
FROM [Backup.Model.JobSessions] js
LEFT JOIN [Backup.Model.BackupJobSessions] bs ON bs.Id = js.Id
WHERE 1=1 {_mssql_where(column_case)}
GROUP BY {norm}
ORDER BY MAX(js.creation_time) DESC"""
        else:
            norm = _NORM_NAME_MSSQL_PASCAL
            return f"""SELECT
    {norm} AS job_name,
    COUNT(*) AS session_count,
    ISNULL(SUM(bs.TotalSize), 0),
    ISNULL(SUM(bs.ProcessedSize), 0),
    ISNULL(SUM(bs.ReadSize), 0),
    ISNULL(SUM(bs.StoredSize), 0),
    ISNULL(AVG(bs.AvgSpeed), 0),
    MAX(js.CreationTime),
    SUM(CASE WHEN js.Result = 0 THEN 1 ELSE 0 END),
    SUM(CASE WHEN js.Result = 1 THEN 1 ELSE 0 END),
    SUM(CASE WHEN js.Result = 2 THEN 1 ELSE 0 END)
FROM [Backup.Model.JobSessions] js
LEFT JOIN [Backup.Model.BackupJobSessions] bs ON bs.Id = js.Id
WHERE 1=1 {_mssql_where(column_case)}
GROUP BY {norm}
ORDER BY MAX(js.CreationTime) DESC"""
    else:
        norm = _NORM_NAME_PG
        return f"""SELECT
    {norm} AS job_name,
    COUNT(*) as session_count,
    COALESCE(SUM(bs.total_size), 0),
    COALESCE(SUM(bs.processed_size), 0),
    COALESCE(SUM(bs.read_size), 0),
    COALESCE(SUM(bs.stored_size), 0),
    COALESCE(AVG(bs.avg_speed), 0),
    MAX(js.creation_time),
    SUM(CASE WHEN js.result = 0 THEN 1 ELSE 0 END),
    SUM(CASE WHEN js.result = 1 THEN 1 ELSE 0 END),
    SUM(CASE WHEN js.result = 2 THEN 1 ELSE 0 END)
FROM "backup.model.jobsessions" js
LEFT JOIN "backup.model.backupjobsessions" bs ON bs.id = js.id
WHERE 1=1 {_WHERE_FILTER_PG}
GROUP BY 1
ORDER BY MAX(js.creation_time) DESC"""


def job_stats_daily_sql(days: int = 7, db_type: str = "postgresql", column_case: str = "pascal") -> str:
    """Per-job per-day transfer stats.

    ``days`` is the only caller-supplied value interpolated into SQL. It is
    coerced to int so a non-numeric value can never break out of the literal
    (the API already validates it as an int Query, but we defensively coerce
    here too). All other fragments are module-level constants.
    """
    days = int(days)  # coerced to int; remaining fragments are module constants
    if db_type == "mssql":
        if column_case == "snake":
            norm = _NORM_NAME_MSSQL_SNAKE
            return f"""SELECT
    {norm} AS job_name,
    CAST(js.creation_time AS DATE) AS run_date,
    ISNULL(SUM(bs.processed_size), 0),
    ISNULL(SUM(bs.read_size), 0),
    ISNULL(SUM(bs.stored_size), 0),
    COUNT(*) AS session_count,
    SUM(CASE WHEN js.result = 0 THEN 1 ELSE 0 END) AS success_count,
    SUM(CASE WHEN js.result = 1 THEN 1 ELSE 0 END) AS warning_count,
    SUM(CASE WHEN js.result = 2 THEN 1 ELSE 0 END) AS failed_count
FROM [Backup.Model.JobSessions] js
LEFT JOIN [Backup.Model.BackupJobSessions] bs ON bs.Id = js.Id
WHERE js.creation_time >= DATEADD(day, -{days}, GETDATE()) {_mssql_where(column_case)}
GROUP BY {norm}, CAST(js.creation_time AS DATE)
ORDER BY 1, 2 DESC"""
        else:
            norm = _NORM_NAME_MSSQL_PASCAL
            return f"""SELECT
    {norm} AS job_name,
    CAST(js.CreationTime AS DATE) AS run_date,
    ISNULL(SUM(bs.ProcessedSize), 0),
    ISNULL(SUM(bs.ReadSize), 0),
    ISNULL(SUM(bs.StoredSize), 0),
    COUNT(*) AS session_count,
    SUM(CASE WHEN js.Result = 0 THEN 1 ELSE 0 END) AS success_count,
    SUM(CASE WHEN js.Result = 1 THEN 1 ELSE 0 END) AS warning_count,
    SUM(CASE WHEN js.Result = 2 THEN 1 ELSE 0 END) AS failed_count
FROM [Backup.Model.JobSessions] js
LEFT JOIN [Backup.Model.BackupJobSessions] bs ON bs.Id = js.Id
WHERE js.CreationTime >= DATEADD(day, -{days}, GETDATE()) {_mssql_where(column_case)}
GROUP BY {norm}, CAST(js.CreationTime AS DATE)
ORDER BY 1, 2 DESC"""
    else:
        norm = _NORM_NAME_PG
        return f"""SELECT
    {norm} AS job_name,
    DATE(js.creation_time) AS run_date,
    COALESCE(SUM(bs.processed_size), 0),
    COALESCE(SUM(bs.read_size), 0),
    COALESCE(SUM(bs.stored_size), 0),
    COUNT(*) AS session_count,
    SUM(CASE WHEN js.result = 0 THEN 1 ELSE 0 END) AS success_count,
    SUM(CASE WHEN js.result = 1 THEN 1 ELSE 0 END) AS warning_count,
    SUM(CASE WHEN js.result = 2 THEN 1 ELSE 0 END) AS failed_count
FROM "backup.model.jobsessions" js
LEFT JOIN "backup.model.backupjobsessions" bs ON bs.id = js.id
WHERE js.creation_time >= NOW() - INTERVAL '{days} days' {_WHERE_FILTER_PG}
GROUP BY 1, DATE(js.creation_time)
ORDER BY 1, DATE(js.creation_time) DESC"""


def session_stats_sql(db_type: str = "postgresql", column_case: str = "pascal") -> str:
    """Session-level transfer statistics."""
    if db_type == "mssql":
        if column_case == "snake":
            norm = _NORM_NAME_MSSQL_SNAKE
            return f"""SELECT TOP 200
    js.Id,
    js.JobId,
    {norm} AS job_name,
    js.state,
    js.creation_time,
    js.end_time,
    js.result,
    ISNULL(bs.total_size, 0),
    ISNULL(bs.processed_size, 0),
    ISNULL(bs.read_size, 0),
    ISNULL(bs.stored_size, 0),
    ISNULL(bs.avg_speed, 0)
FROM [Backup.Model.JobSessions] js
LEFT JOIN [Backup.Model.BackupJobSessions] bs ON bs.Id = js.Id
WHERE 1=1 {_mssql_where(column_case)}
ORDER BY js.creation_time DESC"""
        else:
            norm = _NORM_NAME_MSSQL_PASCAL
            return f"""SELECT TOP 200
    js.Id,
    js.JobId,
    {norm} AS job_name,
    js.State,
    js.CreationTime,
    js.EndTime,
    js.Result,
    ISNULL(bs.TotalSize, 0),
    ISNULL(bs.ProcessedSize, 0),
    ISNULL(bs.ReadSize, 0),
    ISNULL(bs.StoredSize, 0),
    ISNULL(bs.AvgSpeed, 0)
FROM [Backup.Model.JobSessions] js
LEFT JOIN [Backup.Model.BackupJobSessions] bs ON bs.Id = js.Id
WHERE 1=1 {_mssql_where(column_case)}
ORDER BY js.CreationTime DESC"""
    else:
        norm = _NORM_NAME_PG
        return f"""SELECT
    js.id, js.job_id,
    {norm} AS job_name, js.state,
    js.creation_time, js.end_time, js.result,
    COALESCE(bs.total_size, 0),
    COALESCE(bs.processed_size, 0),
    COALESCE(bs.read_size, 0),
    COALESCE(bs.stored_size, 0),
    COALESCE(bs.avg_speed, 0)
FROM "backup.model.jobsessions" js
LEFT JOIN "backup.model.backupjobsessions" bs ON bs.id = js.id
WHERE 1=1 {_WHERE_FILTER_PG}
ORDER BY js.creation_time DESC
LIMIT 200"""


def job_names_sql(db_type: str = "postgresql", column_case: str = "pascal") -> str:
    """Distinct job names (fallback when stats query fails)."""
    if db_type == "mssql":
        if column_case == "snake":
            norm = _NORM_NAME_MSSQL_SNAKE
        else:
            norm = _NORM_NAME_MSSQL_PASCAL
        return f"""SELECT DISTINCT {norm} AS job_name
FROM [Backup.Model.JobSessions] js
WHERE 1=1 {_mssql_where(column_case)}
ORDER BY 1"""
    else:
        norm = _NORM_NAME_PG
        return f"""SELECT DISTINCT {norm} AS job_name
FROM "backup.model.jobsessions" js
WHERE 1=1 {_WHERE_FILTER_PG}
ORDER BY 1"""
