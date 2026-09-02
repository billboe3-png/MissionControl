"""
Database query bridge for Veeam SSH+SQL operations.

Executes SQL queries on the Veeam database via the Mission Control agent
relay (production) or direct SSH (development/test only).
"""

import logging
from typing import Any

from sqlalchemy.orm import Session

logger = logging.getLogger("plugin.veeam.db_bridge")


async def run_db_query(
    sql: str,
    ssh_host: str,
    ssh_port: int,
    ssh_username: str,
    ssh_password: str,
    db_type: str = "postgresql",
    db: Session | None = None,
    server_id: int | None = None,
    agent_id: int | None = None,
    target_id: int | None = None,
) -> dict[str, Any]:
    """Run a SQL query on the Veeam database.

    Production path: dispatch ``veeam:db:query`` through the linked Mission
    Control agent (AgentSshExecutor) so the query is executed on the Veeam
    host via the agent's SSH relay.

    Fallback path: DirectSshExecutor (paramiko) straight to the host, only
    available outside the production environment (used by tests).
    """
    if agent_id is not None and target_id is not None and db is not None:
        from app.plugins.installed.official_veeam.ssh_executor import AgentSshExecutor

        executor = AgentSshExecutor(
            db=db,
            agent_id=agent_id,
            target_id=target_id,
            timeout=120,
        )
        try:
            result = await executor.run(
                op="veeam:db:query",
                params={
                    "sql": sql,
                    "db_type": db_type,
                },
                timeout=120,
            )
        except Exception as exc:
            logger.error("Agent DB query raised: %s", exc)
            return {
                "success": False,
                "output": "",
                "stderr": str(exc),
                "error": str(exc),
                "data": None,
            }
        return {
            "success": result.get("success", False),
            "output": result.get("output", "") or "",
            "stderr": result.get("stderr", "") or "",
            "error": result.get("error"),
            "data": None,
        }

    # Fallback: direct SSH (non-production only, e.g. tests)
    from app.core.config import get_settings

    if get_settings().environment == "production":
        return {
            "success": False,
            "output": "",
            "stderr": "No agent relay configured for Veeam server",
            "error": "No agent relay configured for Veeam server",
            "data": None,
        }

    from app.plugins.installed.official_veeam.ssh_executor import DirectSshExecutor

    executor = DirectSshExecutor(
        host=ssh_host,
        port=ssh_port or 22,
        username=ssh_username,
        password=ssh_password,
    )
    try:
        result = await executor.run(
            op="veeam:db:query",
            params={
                "query": sql,
                "db_type": db_type,
            },
            timeout=120,
        )
    except Exception as exc:
        logger.error("Direct DB query raised: %s", exc)
        return {
            "success": False,
            "output": "",
            "stderr": str(exc),
            "error": str(exc),
            "data": None,
        }
    return {
        "success": result.get("success", False),
        "output": result.get("output", "") or "",
        "stderr": result.get("stderr", "") or "",
        "error": result.get("error"),
        "data": None,
    }
