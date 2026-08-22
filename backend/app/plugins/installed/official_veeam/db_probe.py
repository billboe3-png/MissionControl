"""Rich Veeam DB detection + SQL execution via the SSH executor."""

import json
import logging
from typing import Any

logger = logging.getLogger("plugin.veeam.db_probe")


async def detect_db_type(executor: Any, timeout: int = 120) -> dict[str, Any]:
    """Probe the remote Veeam host for its database engine.

    Delegates the psql/sqlcmd binary + port probing to the executor
    (agent in production, direct paramiko in dev). Returns a structured
    dict that the diagnostics stage renders verbatim.
    """
    try:
        result = await executor.run("veeam:db:detect", timeout=timeout)
    except Exception as exc:
        logger.exception("DB detect dispatch failed")
        return {"db_type": None, "psql_found": False, "sqlcmd_found": False,
                "pg_port": False, "mssql_port": False, "error": str(exc)}
    if not result.get("success"):
        return {"db_type": None, "psql_found": False, "sqlcmd_found": False,
                "pg_port": False, "mssql_port": False,
                "error": result.get("error") or result.get("stderr") or "DB detect failed"}
    payload = result
    if payload.get("db_type") is None and isinstance(result.get("output"), str):
        output = result["output"].strip()
        if output:
            try:
                parsed = json.loads(output)
                if isinstance(parsed, dict):
                    payload = parsed
            except (ValueError, TypeError):
                pass
    return {
        "db_type": payload.get("db_type"),
        "psql_found": bool(payload.get("psql_found")),
        "sqlcmd_found": bool(payload.get("sqlcmd_found")),
        "pg_port": bool(payload.get("pg_port")),
        "mssql_port": bool(payload.get("mssql_port")),
        "error": None,
    }


async def run_db_query(
    executor: Any,
    sql: str,
    db_type: str = "postgresql",
    column_case: str = "pascal",
    timeout: int = 120,
) -> dict[str, Any]:
    """Execute a SQL query on the Veeam database via the executor."""
    try:
        result = await executor.run(
            "veeam:db:query",
            params={"sql": sql, "db_type": db_type, "column_case": column_case},
            timeout=timeout,
        )
    except Exception as exc:
        logger.exception("DB query dispatch failed")
        return {"success": False, "output": "", "stderr": "", "exit_code": 1, "error": str(exc)}
    if not result.get("success"):
        return {
            "success": False,
            "output": result.get("output", ""),
            "stderr": result.get("stderr", ""),
            "exit_code": result.get("exit_code", 1),
            "error": result.get("error") or result.get("stderr") or "DB query failed",
        }
    return {
        "success": True,
        "output": result.get("output", ""),
        "stderr": result.get("stderr", ""),
        "exit_code": result.get("exit_code", 0),
        "error": None,
    }
