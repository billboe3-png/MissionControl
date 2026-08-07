"""
Mission Control Hyper-V Provider Factory

Manages multiple Hyper-V providers keyed by IntegrationProfile ID.
Falls back to mock when no profile is configured.
"""

import json
import logging

from sqlalchemy.orm import Session

from .base_provider import HyperVProvider

logger = logging.getLogger(__name__)

_providers: dict[int, HyperVProvider] = {}
_default_provider: HyperVProvider | None = None


def _build_provider(profile) -> HyperVProvider:
    """Create a production provider from an IntegrationProfile."""
    from app.core.config import get_settings
    from app.core.security import CredentialCipher

    settings = get_settings()
    cipher = CredentialCipher(settings.missioncontrol_secret_key)
    password = cipher.decrypt(profile.encrypted_secret) if profile.encrypted_secret else ""
    host = profile.base_url or ""
    username = profile.username or ""
    timeout = profile.timeout or 30
    transport = profile.domain or "winrm"

    if not host or not username:
        raise ValueError("Profile missing base_url or username")

    port = 22 if transport == "ssh" else 5985

    from .hyperv_provider import HyperVPowerShellProvider

    return HyperVPowerShellProvider(
        host=host,
        port=port,
        username=username,
        password=password,
        timeout=timeout,
        transport=transport,
    )


def list_hyperv_hosts(db: Session) -> list[dict]:
    """Return all enabled Hyper-V hosts for the frontend selector.

    Includes both IntegrationProfile hosts and agent remote targets
    that have collected Hyper-V inventory.
    """
    from app.repositories.integration_profile_repository import (
        IntegrationProfileRepository,
    )

    profiles = IntegrationProfileRepository.get_all_enabled_by_type(db, "hyperv")
    remote_hosts = [
        {"id": p.id, "name": p.name, "host": p.base_url or "unknown"}
        for p in profiles
        if p.base_url and p.base_url.lower() not in {"localhost", "127.0.0.1", "::1"}
    ]

    agent_hosts: list[dict] = []
    seen_hostnames: set[str] = set()
    try:
        from app.models.db.agent import Agent
        from app.models.db.agent_remote_target import AgentRemoteTarget

        targets = (
            db.query(AgentRemoteTarget, Agent)
            .join(Agent, AgentRemoteTarget.agent_id == Agent.id)
            .filter(
                AgentRemoteTarget.enabled.is_(True),
                Agent.status != "offline",
            )
            .all()
        )
        for target, agent in targets:
            inv = {}
            target_data = {}
            if agent.inventory_json:
                try:
                    full_inv = json.loads(agent.inventory_json)
                    remote = full_inv.get("remote_targets", {})
                    target_data = remote.get(f"target-{target.id}", {})
                    inv = target_data.get("inventory", {})
                except (json.JSONDecodeError, TypeError):
                    pass
            hyperv = inv.get("hyperv")
            if not hyperv:
                try:
                    full_inv = json.loads(agent.inventory_json)
                    plugins = full_inv.get("plugins", {})
                    hyperv = plugins.get("hyperv")
                except (json.JSONDecodeError, TypeError):
                    pass
            if not hyperv:
                continue
            if isinstance(hyperv, dict):
                remote_hyperv = (target_data.get("inventory", {}).get("hyperv") or {}).get("remote")
                if remote_hyperv:
                    hyperv = remote_hyperv
                else:
                    plugins_hyperv = hyperv.get("remote")
                    if not plugins_hyperv:
                        plugins_hyperv = hyperv.get("local") or hyperv
                    hyperv = plugins_hyperv
            vm_count = 0
            if isinstance(hyperv, dict):
                vm_count = hyperv.get("vm_count", 0)
            elif isinstance(hyperv, list):
                vm_count = len(hyperv)
            if vm_count > 0:
                host = target.hostname
                try:
                    raw = hyperv.get("vms") if isinstance(hyperv, dict) else (hyperv if isinstance(hyperv, list) else [])
                    if isinstance(raw, str):
                        raw = json.loads(raw)
                    if isinstance(raw, dict):
                        raw = raw.get("vms", [])
                    names = [v.get("ComputerName") or v.get("computer_name") for v in raw if isinstance(v, dict)]
                    if names:
                        host = max(set(names), key=names.count)
                except (json.JSONDecodeError, TypeError):
                    pass
                entry_id = -target.id
                entry = {"id": entry_id, "name": host, "host": host}
                if host not in seen_hostnames:
                    seen_hostnames.add(host)
                    agent_hosts.append(entry)
    except Exception as e:
        logger.debug("Could not load agent targets for host list: %s", e)

    local_hosts: list[dict] = []
    try:
        from app.models.db.agent import Agent
        local_agents = (
            db.query(Agent)
            .filter(Agent.status != "offline", Agent.inventory_json.isnot(None))
            .all()
        )
        for agent in local_agents:
            try:
                full_inv = json.loads(agent.inventory_json)
                hyperv = full_inv.get("plugins", {}).get("hyperv")
                plugin_data = hyperv or {}
                local_data = plugin_data.get("local")
                if not local_data:
                    continue
                if isinstance(local_data, dict):
                    vm_count = local_data.get("vm_count", 0)
                elif isinstance(local_data, list):
                    vm_count = len(local_data)
                else:
                    vm_count = 0
                if vm_count <= 0:
                    continue
                host_id = -(1000 + agent.id)
                hostname = agent.name
                try:
                    raw = local_data.get("vms") if isinstance(local_data, dict) else (local_data if isinstance(local_data, list) else [])
                    if isinstance(raw, str):
                        raw = json.loads(raw)
                    if isinstance(raw, dict):
                        raw = raw.get("vms", [])
                    names = [v.get("ComputerName") or v.get("computer_name") for v in raw if isinstance(v, dict)]
                    if names:
                        hostname = max(set(names), key=names.count)
                except (json.JSONDecodeError, TypeError):
                    pass
                if hostname not in seen_hostnames:
                    seen_hostnames.add(hostname)
                    local_hosts.append({
                        "id": host_id,
                        "name": hostname,
                        "host": hostname,
                    })
            except (json.JSONDecodeError, TypeError):
                pass
    except Exception as e:
        logger.debug("Could not load local agent hosts for host list: %s", e)

    return local_hosts + agent_hosts + remote_hosts


def get_hyperv_provider(db: Session | None = None, host_id: int | None = None) -> HyperVProvider:
    """Return the Hyper-V provider for a given host_id.

    Positive host_id: IntegrationProfile-backed provider.
    Negative host_id in (-999, 0): agent remote target inventory.
    Negative host_id <= -1000: local agent host inventory, mapped as -(1000 + agent.id).
    None: default provider.
    Falls back to agent inventory when the configured host is unreachable.
    """
    global _default_provider

    if host_id is not None:
        if host_id <= -1000:
            return _get_local_agent_provider(db, -(1000 + host_id))

        if host_id < 0:
            return _get_agent_provider(db, -host_id)

        if host_id in _providers:
            cached = _providers[host_id]
            if _is_agent_host(cached):
                return cached
            del _providers[host_id]

        if db is not None:
            try:
                from app.repositories.integration_profile_repository import (
                    IntegrationProfileRepository,
                )

                profile = IntegrationProfileRepository.get_by_id(db, host_id)
                if profile is not None and profile.enabled and profile.integration_type == "hyperv":
                    try:
                        provider = _build_provider(profile)
                        _providers[host_id] = provider
                        logger.info("Created Hyper-V provider for profile %s (%s)", profile.name, profile.base_url)
                        return provider
                    except Exception as e:
                        logger.warning("Failed to create provider for profile %s: %s", profile.name, e)
            except Exception as e:
                logger.warning("Failed to load Hyper-V profile %s from DB: %s", host_id, e)

        logger.warning("Hyper-V host_id=%s not found, falling back to default", host_id)

    if _default_provider is not None:
        cached = _default_provider
        if _is_agent_host(cached):
            return cached
        _default_provider = None

    if db is not None:
        try:
            from app.repositories.integration_profile_repository import (
                IntegrationProfileRepository,
            )

            profile = IntegrationProfileRepository.get_enabled_by_type(db, "hyperv")
            if profile is not None:
                try:
                    _default_provider = _build_provider(profile)
                    _providers[profile.id] = _default_provider
                    logger.info("Using production Hyper-V provider (profile: %s)", profile.name)
                    return _default_provider
                except Exception as e:
                    logger.warning("Failed to create default provider: %s", e)
        except Exception as e:
            logger.warning("Failed to load Hyper-V profile from DB: %s", e)

    agent_default = _try_agent_default_provider(db)
    if agent_default is not None:
        _default_provider = agent_default
        return _default_provider

    logger.info("Using mock Hyper-V provider")
    from .mock_provider import MockHyperVProvider

    _default_provider = MockHyperVProvider()
    return _default_provider


def _get_agent_provider(db: Session | None, target_id: int) -> HyperVProvider:
    """Build an AgentHyperVProvider from stored remote target inventory.

    Falls back to local agent inventory when remote target inventory is missing.
    """
    from app.models.db.agent import Agent
    from app.models.db.agent_remote_target import AgentRemoteTarget

    if db is None:
        raise ValueError("Database session required for agent provider")

    target = db.query(AgentRemoteTarget).filter(AgentRemoteTarget.id == target_id).first()
    if target is None:
        raise ValueError(f"Agent remote target {target_id} not found")

    agent = db.query(Agent).filter(Agent.id == target.agent_id).first()
    if agent is None or not agent.inventory_json:
        raise ValueError(f"Agent inventory not available for target {target_id}")

    try:
        full_inv = json.loads(agent.inventory_json)
        remote = full_inv.get("remote_targets", {})
        target_data = remote.get(f"target-{target_id}", {})
        inv = target_data.get("inventory", {})
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError(f"Invalid inventory JSON for target {target_id}") from exc

    hyperv = inv.get("hyperv")
    if not hyperv:
        try:
            full_inv = json.loads(agent.inventory_json)
            plugins = full_inv.get("plugins", {})
            hyperv = plugins.get("hyperv")
        except (json.JSONDecodeError, TypeError):
            pass
    if not hyperv:
        raise ValueError(f"No Hyper-V inventory collected for target {target_id}")

    if isinstance(hyperv, dict):
        remote_targets = json.loads(agent.inventory_json or "{}").get("remote_targets", {})
        target_inventory = remote_targets.get(f"target-{target_id}", {}).get("inventory", {})
        remote_hyperv = target_inventory.get("hyperv", {})
        if isinstance(remote_hyperv, dict) and remote_hyperv.get("remote"):
            hyperv = remote_hyperv["remote"]

    async def _dispatch_on_agent(command_str: str) -> dict:
        """Queue a PowerShell command for execution on the remote target."""
        from fastapi import HTTPException

        from app.schemas.agent import AgentCommandDispatchRequest
        from app.services.agent_service import agent_service

        if agent.status != "online":
            return {
                "success": False,
                "error": f"Agent '{agent.name}' is {agent.status}, cannot dispatch command",
            }
        cmd_payload = json.dumps({
            "command": command_str,
            "target_id": target.id,
        })
        req = AgentCommandDispatchRequest(
            agent_id=agent.id,
            command_type="remote_execute",
            command=cmd_payload,
            timeout=120,
        )
        try:
            result = await agent_service.dispatch_command(db, req)
            return {
                "success": True,
                "command_id": result.id,
                "message": f"Command dispatched to agent (id={result.id})",
            }
        except HTTPException as e:
            return {"success": False, "error": e.detail}
        except Exception as e:
            logger.exception("Failed to dispatch command to agent %s", agent.id)
            return {"success": False, "error": str(e)}

    from .agent_provider import AgentHyperVProvider
    return AgentHyperVProvider(
        hyperv,
        target_hostname=target.hostname,
        agent_id=agent.id,
        target_id=target.id,
        dispatch_cmd=_dispatch_on_agent,
    )


def _get_local_agent_provider(db: Session | None, agent_id: int) -> HyperVProvider:
    """Build an AgentHyperVProvider for the agent's own local host.

    Uses the same agent-relayed dispatch path as remote targets so
    local VM actions work through the agent command queue.
    """
    from app.models.db.agent import Agent

    if db is None:
        raise ValueError("Database session required for local agent provider")

    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if agent is None or not agent.inventory_json:
        raise ValueError(f"Agent {agent_id} inventory not available")

    import json
    try:
        full_inv = json.loads(agent.inventory_json)
        plugin_data = full_inv.get("plugins", {}).get("hyperv") or {}
        hyperv = plugin_data.get("local") or plugin_data
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError(f"Invalid inventory JSON for agent {agent_id}") from exc

    if not hyperv:
        raise ValueError(f"No local Hyper-V inventory collected for agent {agent_id}")

    async def _dispatch_on_agent(command_str: str) -> dict:
        from fastapi import HTTPException
        from app.schemas.agent import AgentCommandDispatchRequest
        from app.services.agent_service import agent_service

        if agent.status != "online":
            return {
                "success": False,
                "error": f"Agent '{agent.name}' is {agent.status}, cannot dispatch command",
            }
        req = AgentCommandDispatchRequest(
            agent_id=agent.id,
            command_type="execute",
            command=command_str,
            timeout=120,
        )
        try:
            result = await agent_service.dispatch_command(db, req)
            return {
                "success": True,
                "command_id": result.id,
                "message": f"Command dispatched to agent (id={result.id})",
            }
        except HTTPException as e:
            return {"success": False, "error": e.detail}
        except Exception as e:
            logger.exception("Failed to dispatch command to agent %s", agent.id)
            return {"success": False, "error": str(e)}

    from .local_agent_provider import LocalAgentHyperVProvider
    return LocalAgentHyperVProvider(
        hyperv,
        hostname=agent.name or full_inv.get("system", {}).get("hostname", ""),
        dispatch_cmd=_dispatch_on_agent,
    )


def _is_agent_host(provider: object) -> bool:
    return provider.__class__.__name__ == "AgentHyperVProvider"


def _try_agent_default_provider(db: Session | None) -> HyperVProvider | None:
    """Return an agent-backed provider when the only configured host is unreachable."""
    if db is None:
        return None
    try:
        from app.models.db.agent import Agent
        from app.providers.hyperv.agent_provider import AgentHyperVProvider

        agent = (
            db.query(Agent)
            .filter(Agent.status != "offline", Agent.inventory_json.isnot(None))
            .order_by(Agent.id.asc())
            .first()
        )
        if agent is None:
            return None

        import json
        full_inv = json.loads(agent.inventory_json) if agent.inventory_json else {}
        plugin_data = full_inv.get("plugins", {}).get("hyperv") or {}
        local_inventory = plugin_data.get("local") or {}
        remote_inventory = plugin_data.get("remote") or {}
        hyperv = local_inventory or remote_inventory or plugin_data
        if not hyperv or (isinstance(hyperv, dict) and hyperv.get("vm_count", 0) <= 0):
            return None

        return AgentHyperVProvider(
            hyperv,
            target_hostname=agent.name or full_inv.get("system", {}).get("hostname", "Agent"),
            agent_id=agent.id,
            target_id=agent.id,
            dispatch_cmd=lambda command_str: {"success": False, "error": "Agent offline for commands"},
        )
    except Exception as exc:
        logger.debug("Agent-backed default Hyper-V provider failed: %s", exc)
        return None


def reset_hyperv_provider(host_id: int | None = None) -> None:
    """Reset cached provider(s). If host_id given, reset only that one."""
    global _default_provider
    if host_id is not None:
        if host_id > 0:
            _providers.pop(host_id, None)
    else:
        _providers.clear()
        _default_provider = None
