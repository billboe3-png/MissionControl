"""
Multi-stage connection diagnostics for Veeam servers.
"""

import logging
from typing import Any

from app.plugins.installed.official_veeam.db_probe import detect_db_type

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
