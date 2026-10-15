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
AND js.job_name NOT LIKE '%Malware Detection%'
AND js.job_name NOT LIKE '%Database Maintenance%'
AND js.job_name NOT LIKE '%HealthCheck %'
AND js.job_name NOT LIKE '%Security & Compliance Analyzer%'"""

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
AND js.job_name NOT LIKE '%Malware Detection%'
AND js.job_name NOT LIKE '%Database Maintenance%'
AND js.job_name NOT LIKE '%HealthCheck %'
AND js.job_name NOT LIKE '%Security & Compliance Analyzer%'"""
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
AND js.JobName NOT LIKE '%Malware Detection%'
AND js.JobName NOT LIKE '%Database Maintenance%'
AND js.JobName NOT LIKE '%HealthCheck %'
AND js.JobName NOT LIKE '%Security & Compliance Analyzer%'"""


def _parent_only_filter(
    db_type: str = "postgresql", column_case: str = "pascal",
) -> str:
    """AND fragment selecting only parent job sessions.

    Veeam records one parent session per run plus one child session per
    protected host, named ``<job name> - <hostname>``. Both carry identical
    byte counters, so summing them would double count every job. Keeping only
    the parent (whose name matches the job name with no `` - <host>`` suffix)
    makes each job count exactly once.
    """
    if db_type == "mssql":
        col = "js.JobName" if column_case != "snake" else "js.job_name"
        return f"AND CHARINDEX(' - ', {col}) = 0"
    return "AND regexp_replace(js.job_name, ' - [A-Za-z0-9._]+$', '') = js.job_name"


def _daily_where_filter(
    db_type: str = "postgresql", column_case: str = "pascal", include_system: bool = False,
) -> str:
    """WHERE fragment for the daily stats query.

    System/internal job sessions are excluded by default. When
    ``include_system`` is True an empty fragment is returned so every job
    session (including internal Veeam jobs) is counted.
    """
    if include_system:
        return ""
    if db_type == "mssql":
        return _mssql_where(column_case)
    return _WHERE_FILTER_PG


def job_stats_sql(db_type: str = "postgresql", column_case: str = "pascal") -> str:
    """Aggregated transfer stats per job (all time)."""
    if db_type == "mssql":
        if column_case == "snake":
            norm = _NORM_NAME_MSSQL_SNAKE
            return f"""WITH base AS (
    SELECT {norm} AS job_name,
    js.result,
    js.creation_time,
    CASE WHEN {norm} = js.job_name THEN 1 ELSE 0 END AS is_parent,
    ISNULL(bs.total_size, 0) AS total_size,
    ISNULL(bs.processed_size, 0) AS processed_size,
    ISNULL(bs.read_size, 0) AS read_size,
    ISNULL(bs.stored_size, 0) AS stored_size,
    ISNULL(bs.avg_speed, 0) AS avg_speed
FROM [Backup.Model.JobSessions] js
LEFT JOIN [Backup.Model.BackupJobSessions] bs ON bs.id = js.id
WHERE 1=1 {_mssql_where(column_case)}
), pref AS (
    SELECT job_name, MAX(1 - is_parent) AS has_child
    FROM base GROUP BY job_name
)
SELECT b.job_name,
    COUNT(*) AS session_count,
    ISNULL(SUM(b.total_size), 0),
    ISNULL(SUM(b.processed_size), 0),
    ISNULL(SUM(b.read_size), 0),
    ISNULL(SUM(b.stored_size), 0),
    ISNULL(AVG(b.avg_speed), 0),
    MAX(b.creation_time),
    SUM(CASE WHEN b.result = 0 THEN 1 ELSE 0 END),
    SUM(CASE WHEN b.result = 1 THEN 1 ELSE 0 END),
    SUM(CASE WHEN b.result = 2 THEN 1 ELSE 0 END)
FROM base b
JOIN pref p ON p.job_name = b.job_name
WHERE (p.has_child = 1 AND b.is_parent = 0) OR (p.has_child = 0 AND b.is_parent = 1)
GROUP BY b.job_name
ORDER BY MAX(b.creation_time) DESC"""
        else:
            norm = _NORM_NAME_MSSQL_PASCAL
            return f"""WITH base AS (
    SELECT {norm} AS job_name,
    js.Result,
    js.CreationTime,
    CASE WHEN {norm} = js.JobName THEN 1 ELSE 0 END AS is_parent,
    ISNULL(bs.TotalSize, 0) AS total_size,
    ISNULL(bs.ProcessedSize, 0) AS processed_size,
    ISNULL(bs.ReadSize, 0) AS read_size,
    ISNULL(bs.StoredSize, 0) AS stored_size,
    ISNULL(bs.AvgSpeed, 0) AS avg_speed
FROM [Backup.Model.JobSessions] js
LEFT JOIN [Backup.Model.BackupJobSessions] bs ON bs.Id = js.Id
WHERE 1=1 {_mssql_where(column_case)}
), pref AS (
    SELECT job_name, MAX(1 - is_parent) AS has_child
    FROM base GROUP BY job_name
)
SELECT b.job_name,
    COUNT(*) AS session_count,
    ISNULL(SUM(b.total_size), 0),
    ISNULL(SUM(b.processed_size), 0),
    ISNULL(SUM(b.read_size), 0),
    ISNULL(SUM(b.stored_size), 0),
    ISNULL(AVG(b.avg_speed), 0),
    MAX(b.CreationTime),
    SUM(CASE WHEN b.Result = 0 THEN 1 ELSE 0 END),
    SUM(CASE WHEN b.Result = 1 THEN 1 ELSE 0 END),
    SUM(CASE WHEN b.Result = 2 THEN 1 ELSE 0 END)
FROM base b
JOIN pref p ON p.job_name = b.job_name
WHERE (p.has_child = 1 AND b.is_parent = 0) OR (p.has_child = 0 AND b.is_parent = 1)
GROUP BY b.job_name
ORDER BY MAX(b.CreationTime) DESC"""
    else:
        norm = _NORM_NAME_PG
        return f"""WITH base AS (
    SELECT {norm} AS job_name,
    js.result,
    js.creation_time,
    CASE WHEN {norm} = js.job_name THEN 1 ELSE 0 END AS is_parent,
    COALESCE(bs.total_size, 0) AS total_size,
    COALESCE(bs.processed_size, 0) AS processed_size,
    COALESCE(bs.read_size, 0) AS read_size,
    COALESCE(bs.stored_size, 0) AS stored_size,
    COALESCE(bs.avg_speed, 0) AS avg_speed
FROM "backup.model.jobsessions" js
LEFT JOIN "backup.model.backupjobsessions" bs ON bs.id = js.id
WHERE 1=1 {_WHERE_FILTER_PG}
), pref AS (
    SELECT job_name, MAX(1 - is_parent) AS has_child
    FROM base GROUP BY job_name
)
SELECT b.job_name,
    COUNT(*) as session_count,
    COALESCE(SUM(b.total_size), 0),
    COALESCE(SUM(b.processed_size), 0),
    COALESCE(SUM(b.read_size), 0),
    COALESCE(SUM(b.stored_size), 0),
    COALESCE(AVG(b.avg_speed), 0),
    MAX(b.creation_time),
    SUM(CASE WHEN b.result = 0 THEN 1 ELSE 0 END),
    SUM(CASE WHEN b.result = 1 THEN 1 ELSE 0 END),
    SUM(CASE WHEN b.result = 2 THEN 1 ELSE 0 END)
FROM base b
JOIN pref p ON p.job_name = b.job_name
WHERE (p.has_child = 1 AND b.is_parent = 0) OR (p.has_child = 0 AND b.is_parent = 1)
GROUP BY b.job_name
ORDER BY MAX(b.creation_time) DESC"""


def job_stats_daily_sql(
    days: int = 7, db_type: str = "postgresql", column_case: str = "pascal",
    include_system: bool = False,
) -> str:
    """Per-job per-day transfer stats.

    ``days`` is the only caller-supplied value interpolated into SQL. It is
    coerced to int so a non-numeric value can never break out of the literal
    (the API already validates it as an int Query, but we defensively coerce
    here too). All other fragments are module-level constants.

    ``include_system`` toggles the system/internal job exclusion.
    """
    days = int(days)  # coerced to int; remaining fragments are module constants
    where = _daily_where_filter(db_type, column_case, include_system)
    window_start = days - 1
    if db_type == "mssql":
        if column_case == "snake":
            norm = _NORM_NAME_MSSQL_SNAKE
            return f"""WITH base AS (
    SELECT {norm} AS job_name,
    CAST(js.creation_time AS DATE) AS run_date,
    js.result,
    CASE WHEN {norm} = js.job_name THEN 1 ELSE 0 END AS is_parent,
    ISNULL(bs.processed_size, 0) AS processed_size,
    ISNULL(bs.read_size, 0) AS read_size,
    ISNULL(bs.stored_size, 0) AS stored_size
FROM [Backup.Model.JobSessions] js
LEFT JOIN [Backup.Model.BackupJobSessions] bs ON bs.id = js.id
WHERE CAST(js.creation_time AS DATE) >= DATEADD(day, -{window_start}, CAST(GETDATE() AS DATE)) {where}
), pref AS (
    SELECT job_name, run_date, MAX(1 - is_parent) AS has_child
    FROM base GROUP BY job_name, run_date
)
SELECT b.job_name, b.run_date,
    ISNULL(SUM(b.processed_size), 0),
    ISNULL(SUM(b.read_size), 0),
    ISNULL(SUM(b.stored_size), 0),
    COUNT(*) AS session_count,
    SUM(CASE WHEN b.result = 0 THEN 1 ELSE 0 END) AS success_count,
    SUM(CASE WHEN b.result = 1 THEN 1 ELSE 0 END) AS warning_count,
    SUM(CASE WHEN b.result = 2 THEN 1 ELSE 0 END) AS failed_count
FROM base b
JOIN pref p ON p.job_name = b.job_name AND p.run_date = b.run_date
WHERE (p.has_child = 1 AND b.is_parent = 0) OR (p.has_child = 0 AND b.is_parent = 1)
GROUP BY b.job_name, b.run_date
ORDER BY 1, 2 DESC"""
        else:
            norm = _NORM_NAME_MSSQL_PASCAL
            return f"""WITH base AS (
    SELECT {norm} AS job_name,
    CAST(js.CreationTime AS DATE) AS run_date,
    js.Result,
    CASE WHEN {norm} = js.JobName THEN 1 ELSE 0 END AS is_parent,
    ISNULL(bs.ProcessedSize, 0) AS processed_size,
    ISNULL(bs.ReadSize, 0) AS read_size,
    ISNULL(bs.StoredSize, 0) AS stored_size
FROM [Backup.Model.JobSessions] js
LEFT JOIN [Backup.Model.BackupJobSessions] bs ON bs.Id = js.Id
WHERE CAST(js.CreationTime AS DATE) >= DATEADD(day, -{window_start}, CAST(GETDATE() AS DATE)) {where}
), pref AS (
    SELECT job_name, run_date, MAX(1 - is_parent) AS has_child
    FROM base GROUP BY job_name, run_date
)
SELECT b.job_name, b.run_date,
    ISNULL(SUM(b.processed_size), 0),
    ISNULL(SUM(b.read_size), 0),
    ISNULL(SUM(b.stored_size), 0),
    COUNT(*) AS session_count,
    SUM(CASE WHEN b.result = 0 THEN 1 ELSE 0 END) AS success_count,
    SUM(CASE WHEN b.result = 1 THEN 1 ELSE 0 END) AS warning_count,
    SUM(CASE WHEN b.result = 2 THEN 1 ELSE 0 END) AS failed_count
FROM base b
JOIN pref p ON p.job_name = b.job_name AND p.run_date = b.run_date
WHERE (p.has_child = 1 AND b.is_parent = 0) OR (p.has_child = 0 AND b.is_parent = 1)
GROUP BY b.job_name, b.run_date
ORDER BY 1, 2 DESC"""
    else:
        norm = _NORM_NAME_PG
        return f"""WITH base AS (
    SELECT {norm} AS job_name,
    DATE(js.creation_time) AS run_date,
    js.result,
    CASE WHEN {norm} = js.job_name THEN 1 ELSE 0 END AS is_parent,
    COALESCE(bs.processed_size, 0) AS processed_size,
    COALESCE(bs.read_size, 0) AS read_size,
    COALESCE(bs.stored_size, 0) AS stored_size
FROM "backup.model.jobsessions" js
LEFT JOIN "backup.model.backupjobsessions" bs ON bs.id = js.id
WHERE DATE(js.creation_time) >= CURRENT_DATE - {window_start} {where}
), pref AS (
    SELECT job_name, run_date, MAX(1 - is_parent) AS has_child
    FROM base GROUP BY job_name, run_date
)
SELECT b.job_name, b.run_date,
    COALESCE(SUM(b.processed_size), 0),
    COALESCE(SUM(b.read_size), 0),
    COALESCE(SUM(b.stored_size), 0),
    COUNT(*) AS session_count,
    SUM(CASE WHEN b.result = 0 THEN 1 ELSE 0 END) AS success_count,
    SUM(CASE WHEN b.result = 1 THEN 1 ELSE 0 END) AS warning_count,
    SUM(CASE WHEN b.result = 2 THEN 1 ELSE 0 END) AS failed_count
FROM base b
JOIN pref p ON p.job_name = b.job_name AND p.run_date = b.run_date
WHERE (p.has_child = 1 AND b.is_parent = 0) OR (p.has_child = 0 AND b.is_parent = 1)
GROUP BY b.job_name, b.run_date
ORDER BY 1, 2 DESC"""


def session_stats_sql(db_type: str = "postgresql", column_case: str = "pascal") -> str:
    """Session-level transfer statistics."""
    if db_type == "mssql":
        if column_case == "snake":
            norm = _NORM_NAME_MSSQL_SNAKE
            return f"""SELECT TOP 200
    js.id,
    js.job_id,
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
LEFT JOIN [Backup.Model.BackupJobSessions] bs ON bs.id = js.id
WHERE 1=1 {_mssql_where(column_case)}
{_parent_only_filter(db_type, column_case)}
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
{_parent_only_filter(db_type, column_case)}
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
{_parent_only_filter(db_type, column_case)}
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
{_parent_only_filter(db_type, column_case)}
ORDER BY 1"""
    else:
        norm = _NORM_NAME_PG
        return f"""SELECT DISTINCT {norm} AS job_name
FROM "backup.model.jobsessions" js
WHERE 1=1 {_WHERE_FILTER_PG}
{_parent_only_filter(db_type, column_case)}
ORDER BY 1"""
