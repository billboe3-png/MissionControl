"""
D-Link DGS-1210 Relay - Agent command dispatch
"""
import json
import logging
from typing import Any, Dict, Optional

from app.models.db.agent import Agent
from app.models.db.agent_command import AgentCommand
from app.db.database import SessionLocal
from app.services.agent_service import AgentService

logger = logging.getLogger("plugin.dlink.relay")


async def execute_plugin_command(
    target_id: int,
    command: str,
    params: Dict[str, Any],
    namespace: str = "dlink",
    agent_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Queue a plugin command for the agent to execute on a remote target.

    Args:
        target_id: The remote target ID (SSH/Telnet) on the agent
        command: The plugin command (cli, test_connection, collect_inventory, etc.)
        params: Command parameters
        namespace: Plugin namespace (default: dlink)
        agent_id: Optional specific agent ID (defaults to target's agent)

    Returns:
        Dict with success, stdout, stderr, exit_code or error
    """
    db = SessionLocal()
    try:
        # Get the remote target to find its agent
        from app.plugins.installed.official_dlink.models import DLinkRemoteTarget

        target = db.get(DLinkRemoteTarget, target_id)
        if not target:
            return {"success": False, "error": f"D-Link remote target {target_id} not found"}

        target_agent_id = agent_id or target.agent_id
        agent = db.get(Agent, target_agent_id)
        if not agent:
            return {"success": False, "error": f"Agent {target_agent_id} not found"}

        if agent.status != "online":
            return {"success": False, "error": f"Agent {agent.name} is offline"}

        # Build command payload
        payload = {
            "namespace": namespace,
            "op": command,
            "params": params,
            "target_id": target_id
        }

        # Create agent command
        agent_cmd = AgentCommand(
            agent_id=target_agent_id,
            command_type="remote_execute",
            command=json.dumps(payload),
            status="pending",
            requested_by="dlink-plugin"
        )
        db.add(agent_cmd)
        db.commit()
        db.refresh(agent_cmd)

        # Wait for completion (polling with timeout)
        import asyncio
        timeout = params.get("timeout", 30)
        max_wait = timeout + 10
        start = datetime.utcnow()

        while (datetime.utcnow() - start).total_seconds() < max_wait:
            await asyncio.sleep(0.5)
            db.refresh(agent_cmd)
            if agent_cmd.status == "completed":
                try:
                    return json.loads(agent_cmd.stdout or "{}")
                except json.JSONDecodeError:
                    return {"success": True, "stdout": agent_cmd.stdout, "stderr": agent_cmd.stderr}
            elif agent_cmd.status == "failed":
                return {
                    "success": False,
                    "error": agent_cmd.stderr or agent_cmd.stdout or "Command failed",
                    "exit_code": agent_cmd.exit_code
                }

        return {"success": False, "error": f"Command timed out after {max_wait}s"}

    except Exception as e:
        logger.exception("Error executing plugin command")
        return {"success": False, "error": str(e)}
    finally:
        db.close()


async def rest_api_call(
    target_id: int,
    method: str,
    path: str,
    body: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    port: int = 443,
    use_https: bool = True,
    agent_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Execute an HTTP/HTTPS REST API call to the D-Link switch via agent.
    """
    return await execute_plugin_command(
        target_id=target_id,
        command="rest_api",
        params={
            "method": method.upper(),
            "path": path,
            "body": body,
            "headers": headers,
            "port": port,
            "use_https": use_https
        },
        namespace="dlink",
        agent_id=agent_id
    )


async def start_webui_stream(
    agent: Agent,
    switch: Any,
    session_id: str
) -> None:
    """
    Instruct the agent to start a Web UI TCP tunnel for the D-Link switch.
    """
    from app.db.database import SessionLocal
    from app.plugins.installed.official_dlink.models import DLinkRemoteTarget
    db = SessionLocal()
    try:
        target = db.get(DLinkRemoteTarget, switch.remote_target_id)
        if not target:
            logger.error(f"D-Link remote target {switch.remote_target_id} not found for WebUI stream")
            return

        payload = {
            "namespace": "dlink",
            "op": "webui_stream",
            "params": {
                "session_id": session_id,
                "target_id": target.id,
                "host": target.hostname,
                "port": switch.webui_port or 443,
                "use_https": switch.webui_use_https
            }
        }

        agent_cmd = AgentCommand(
            agent_id=agent.id,
            command_type="remote_execute",
            command=json.dumps(payload),
            status="pending",
            requested_by="dlink-webui"
        )
        db.add(agent_cmd)
        db.commit()
        logger.info(f"Dispatched webui_stream command {agent_cmd.id} to agent {agent.id}")
    except Exception as e:
        logger.exception("Error dispatching webui_stream command")
    finally:
        db.close()


from datetime import datetime