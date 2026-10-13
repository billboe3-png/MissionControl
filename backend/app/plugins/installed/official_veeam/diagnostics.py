"""
Multi-stage connection diagnostics for Veeam servers.
"""

import json
import logging
from typing import Any

from app.plugins.installed.official_veeam.db_probe import detect_db_type
from app.plugins.installed.official_veeam.ssh_executor import build_ssh_executor

logger = logging.getLogger("plugin.veeam.diagnostics")


async def run_connection_diagnostics(provider: Any) -> dict[str, Any]:
    """Run multi-stage connection diagnostics for a Veeam server provider.

    Stages tested:
    1. agent_link / ssh (via executor probe `veeam:test`)
    2. rest (via REST API test)
    3. db (via db_probe.detect_db_type)

    Also handles automatic db_type writeback when server.db_type == 'auto'.
    Never raises exceptions.
    """
    agent_link: dict[str, Any] = {"success": False, "error": "Not tested"}
    ssh_status: dict[str, Any] = {"success": False, "error": "Not tested"}
    rest_status: dict[str, Any] = {"connected": False, "error": "Not tested"}
    db_status: dict[str, Any] = {
        "db_type": None,
        "psql_found": False,
        "sqlcmd_found": False,
        "pg_port": False,
        "mssql_port": False,
        "error": "Not tested",
    }
    recommendations: list[str] = []
    overall_success = False

    try:
        edition = getattr(provider.server, "edition", "enterprise")
        data_source = getattr(provider.server, "data_source", "both")

        # Which stages this server actually requires.
        need_agent = (edition == "community") or (data_source in ("ssh", "both"))
        need_rest = (edition == "enterprise") and (data_source in ("api", "both"))

        # 1. Agent / SSH test via executor
        try:
            res = await provider.executor.run("veeam:test")
            if res.get("success"):
                agent_link = {"success": True, "error": None, "output": res.get("output", "")}
                ssh_status = {"success": True, "error": None}
            else:
                err_msg = res.get("error") or res.get("stderr") or "Agent probe failed"
                agent_link = {"success": False, "error": err_msg}
                ssh_status = {"success": False, "error": err_msg}
                if need_agent:
                    recommendations.append("Check SSH connectivity, credentials, and agent installation on the Veeam server.")
        except Exception as exc:
            logger.warning("Agent link test failed: %s", exc)
            agent_link = {"success": False, "error": str(exc)}
            ssh_status = {"success": False, "error": str(exc)}
            if need_agent:
                recommendations.append("Ensure SSH service is running and network firewall allows connections.")

        # 2. REST test
        try:
            rest_res = await provider.rest.test()
            if isinstance(rest_res, dict) and rest_res.get("connected"):
                rest_status = {
                    "connected": True,
                    "version": rest_res.get("version", ""),
                    "name": rest_res.get("name", ""),
                    "error": None,
                }
            else:
                err_msg = rest_res.get("error") if isinstance(rest_res, dict) else "REST test failed"
                rest_status = {"connected": False, "error": err_msg or "REST connection failed"}
                if need_rest:
                    recommendations.append("Verify Veeam REST API URL, username, password, and SSL certificate settings.")
        except Exception as exc:
            logger.warning("REST connection test failed: %s", exc)
            rest_status = {"connected": False, "error": str(exc)}
            if need_rest:
                recommendations.append("Verify Veeam REST API port (default 9419) and service status.")

        # 3. Database detection probe
        try:
            db_res = await detect_db_type(provider.executor)
            db_status = db_res
            if db_res.get("db_type"):
                detected = db_res["db_type"]
                # Handle auto db_type writeback
                if getattr(provider.server, "db_type", None) == "auto":
                    provider.server.db_type = detected
                    db_session = getattr(provider, "_db", None) or getattr(provider, "db", None)
                    if db_session is not None:
                        try:
                            db_session.commit()
                        except Exception:
                            logger.exception("Failed to commit auto-detected db_type")
            else:
                if not db_res.get("error"):
                    db_status["error"] = "Database type could not be determined"
                if need_agent:
                    recommendations.append("Check database binaries (psql/sqlcmd) or permissions on the Veeam database.")
        except Exception as exc:
            logger.warning("DB probe failed: %s", exc)
            db_status = {
                "db_type": None,
                "psql_found": False,
                "sqlcmd_found": False,
                "pg_port": False,
                "mssql_port": False,
                "error": str(exc),
            }
            if need_agent:
                recommendations.append("Database probe encountered an error.")

        # Determine overall success based on edition / data_source / stages
        if edition == "community":
            overall_success = bool(agent_link.get("success") and db_status.get("db_type"))
        else:
            if data_source == "api":
                overall_success = bool(rest_status.get("connected"))
            elif data_source == "ssh":
                overall_success = bool(agent_link.get("success") and db_status.get("db_type"))
            else:  # both
                overall_success = bool(
                    rest_status.get("connected")
                    or (agent_link.get("success") and db_status.get("db_type"))
                )

        error_summary = None
        if not overall_success:
            errors = []
            if need_rest and not rest_status.get("connected"):
                errors.append(f"REST: {rest_status.get('error')}")
            if need_agent:
                if not agent_link.get("success"):
                    errors.append(f"Agent: {agent_link.get('error')}")
                if db_status.get("error"):
                    errors.append(f"DB: {db_status.get('error')}")
            error_summary = "; ".join(errors) if errors else "Connection diagnostics failed"

        return {
            "success": overall_success,
            "agent_link": agent_link,
            "ssh": ssh_status,
            "rest": rest_status,
            "db": db_status,
            "error": error_summary,
            "recommendations": recommendations,
        }

    except Exception as exc:
        logger.exception("Diagnostics execution failed completely")
        return {
            "success": False,
            "agent_link": agent_link,
            "ssh": ssh_status,
            "rest": rest_status,
            "db": db_status,
            "error": str(exc),
            "recommendations": ["Review server configuration and logs."],
        }


async def _relay(executor: Any, op: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run a ``veeam:*`` relay op and parse the agent's JSON response.

    Mirrors the provider relay: transport failure -> error; the agent wraps its
    result as a JSON object on stdout, so parse it and surface the payload
    (which carries the real ``success`` for DB-critical operations).
    """
    try:
        result = await executor.run(op, params=params, timeout=120)
    except Exception as exc:  # pragma: no cover - defensive
        return {"success": False, "error": str(exc)}

    if not result.get("success"):
        return {
            "success": False,
            "error": result.get("error") or result.get("stderr") or "Agent relay command failed",
        }

    output = result.get("output") or ""
    try:
        parsed = json.loads(output)
    except (json.JSONDecodeError, TypeError):
        return {"success": False, "error": "Agent returned an invalid response", "raw": str(output)[:2000]}

    if not isinstance(parsed, dict):
        return {"success": False, "error": "Agent returned a non-object response"}
    return parsed


async def run_server_diagnostics(db: Any, server: Any) -> dict[str, Any]:
    """Diagnose why a Veeam server's data bridge works — or fails.

    Stages:
    1. ``agent``   — ``veeam:test`` through the agent relay (reachability +
       REST/PowerShell/DB capability flags).
    2. ``db_detect`` — locate psql/sqlcmd and infer the DB engine/ports.
    3. ``db_query``  — a live ``SELECT 1`` probe through the bridge.

    Never raises; always returns a JSON-serialisable dict with a derived
    ``recommendations`` list.
    """
    server_info = {
        "id": getattr(server, "id", None),
        "name": getattr(server, "name", None),
        "edition": getattr(server, "edition", None),
        "data_source": getattr(server, "data_source", None),
        "db_type": getattr(server, "db_type", None),
        "column_case": getattr(server, "column_case", None),
        "agent_id": getattr(server, "agent_id", None),
        "target_id": getattr(server, "target_id", None),
        "enabled": getattr(server, "enabled", None),
    }
    recommendations: list[str] = []
    result: dict[str, Any] = {
        "success": False,
        "server": server_info,
        "agent": {"success": False, "error": "Not tested"},
        "db_detect": {
            "db_type": None,
            "psql_found": False,
            "sqlcmd_found": False,
            "pg_port": False,
            "mssql_port": False,
            "error": "Not tested",
        },
        "db_query": {"success": False, "output": "", "stderr": "", "exit_code": None, "error": "Not tested"},
        "recommendations": recommendations,
        "error": None,
    }

    if server_info["agent_id"] is None or server_info["target_id"] is None:
        msg = "No agent/remote target linked to this server"
        result["agent"] = {"success": False, "error": msg}
        result["error"] = msg
        recommendations.append("Link this Veeam server to a remote target (host) so the agent can relay DB queries.")
        return result

    try:
        executor = build_ssh_executor(db, server)
    except Exception as exc:
        logger.warning("Diagnostics: could not build executor: %s", exc)
        result["agent"] = {"success": False, "error": str(exc)}
        result["error"] = str(exc)
        recommendations.append("Check the server's agent/target configuration.")
        return result

    # 1. Agent link + capability probe
    agent_res = await _relay(executor, "veeam:test")
    result["agent"] = agent_res
    if not agent_res.get("success"):
        result["error"] = agent_res.get("error")
        recommendations.append(
            "Agent relay failed — confirm the agent is online and can reach the host over SSH."
        )
        return result

    # 2. DB client detection
    detect = await detect_db_type(executor)
    result["db_detect"] = detect
    if detect.get("error"):
        recommendations.append(f"Database detection failed: {detect['error']}")

    psql_found = bool(detect.get("psql_found"))
    sqlcmd_found = bool(detect.get("sqlcmd_found"))
    if not psql_found and not sqlcmd_found:
        recommendations.append(
            "Neither psql.exe nor sqlcmd.exe was found on the host — Veeam Backup & Replication may not be installed there."
        )
    elif psql_found and not detect.get("pg_port"):
        recommendations.append("psql is present but PostgreSQL is not listening on port 5432.")
    elif sqlcmd_found and not detect.get("mssql_port"):
        recommendations.append("sqlcmd is present but SQL Server is not listening on port 1433.")

    configured = server_info["db_type"]
    detected = detect.get("db_type")
    if configured in (None, "", "auto"):
        db_type = detected or "postgresql"
    else:
        db_type = configured
        if detected and detected != configured:
            recommendations.append(
                f"Configured DB type is '{configured}' but the host looks like '{detected}' — "
                f"this mismatch is the likely cause. Update this server's db_type to '{detected}'."
            )

    # 3. Live connectivity probe
    query = await _relay(executor, "veeam:db:query", {"sql": "SELECT 1", "db_type": db_type})
    result["db_query"] = query
    if query.get("success"):
        result["success"] = True
    else:
        detail = query.get("error") or query.get("stderr") or "unknown error"
        if not agent_res.get("db_available", True):
            recommendations.append(
                "The agent reached the host but the Veeam database is not reachable."
            )
        recommendations.append(
            f"DB query failed ({db_type}): {detail}. Check the database name (VeeamBackup), instance/port, and credentials."
        )
        result["error"] = detail

    if result["success"]:
        recommendations.append("Database bridge is healthy — jobs/sessions data should load.")

    return result
