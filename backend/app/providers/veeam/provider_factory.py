"""
Mission Control Veeam Provider Factory

Manages multiple Veeam providers keyed by IntegrationProfile ID.
Also supports agent-relayed Veeam inventory via negative host IDs.
Falls back to mock when no profile is configured.
"""

import json
import logging

from sqlalchemy.orm import Session

from .base_provider import VeeamProvider

logger = logging.getLogger(__name__)

_providers: dict[int, VeeamProvider] = {}
_default_provider: VeeamProvider | None = None


def _build_provider(profile) -> VeeamProvider:
    """Create a production provider from an IntegrationProfile."""
    from app.core.config import get_settings
    from app.core.security import CredentialCipher

    settings = get_settings()
    cipher = CredentialCipher(settings.missioncontrol_secret_key)
    password = cipher.decrypt(profile.encrypted_secret) if profile.encrypted_secret else ""
    username = profile.username or ""
    base_url = profile.base_url or ""
    timeout = profile.timeout or 30
    verify_ssl = profile.verify_ssl if profile.verify_ssl is not None else True

    # REST API provider
    if base_url and username:
        from .veeam_provider import VeeamRESTProvider

        return VeeamRESTProvider(
            base_url=base_url,
            username=username,
            password=password,
            timeout=timeout,
            verify_ssl=verify_ssl,
        )

    # PowerShell provider (SSH bridge)
    ssh_host = profile.ssh_host or ""
    ssh_port = profile.ssh_port or 22
    ssh_username = profile.ssh_username or ""
    ssh_password = cipher.decrypt(profile.ssh_password_encrypted) if profile.ssh_password_encrypted else ""
    if ssh_host and ssh_username:
        from .powershell_provider import VeeamPowerShellProvider

        return VeeamPowerShellProvider(
            host=ssh_host,
            port=ssh_port,
            username=ssh_username,
            password=ssh_password,
            timeout=timeout,
            transport="ssh",
        )

    raise ValueError("Profile missing base_url/username or ssh_host/ssh_username")


def list_veeam_hosts(db: Session) -> list[dict]:
    """Return all Veeam hosts (profiles + agent targets with Veeam inventory)."""
    from app.repositories.integration_profile_repository import (
        IntegrationProfileRepository,
    )

    profiles = IntegrationProfileRepository.get_all_enabled_by_type(db, "veeam")
    hosts = [
        {"id": p.id, "name": p.name, "host": p.base_url or p.ssh_host or "unknown"}
        for p in profiles
    ]

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
            inv = _get_target_inventory(agent, target.id)
            veeam = inv.get("veeam")
            if veeam and len(veeam.get("jobs", [])) > 0:
                hosts.append({
                    "id": -target.id,
                    "name": f"{target.name} (Agent)",
                    "host": target.hostname,
                })
    except Exception as e:
        logger.debug("Could not load agent targets for Veeam: %s", e)

    return hosts


def get_veeam_provider(
    db: Session | None = None,
    host_id: int | None = None,
) -> VeeamProvider:
    """Return a Veeam provider.

    If host_id is positive: loads (or caches) the provider for that IntegrationProfile.
    If host_id is negative: loads from agent remote target inventory.
    If host_id is None: returns the default (first available) provider.
    Falls back to mock when no profile exists.
    """
    global _default_provider

    if host_id is not None:
        if host_id < 0:
            return _get_agent_provider(db, -host_id)

        if host_id in _providers:
            return _providers[host_id]

        if db is not None:
            try:
                from app.repositories.integration_profile_repository import (
                    IntegrationProfileRepository,
                )

                profile = IntegrationProfileRepository.get_by_id(db, host_id)
                if profile is not None and profile.enabled and profile.integration_type == "veeam":
                    try:
                        provider = _build_provider(profile)
                        _providers[host_id] = provider
                        logger.info("Created Veeam provider for profile %s", profile.name)
                        return provider
                    except Exception as e:
                        logger.warning("Failed to create provider for profile %s: %s", profile.name, e)
            except Exception as e:
                logger.warning("Failed to load Veeam profile %s from DB: %s", host_id, e)

        logger.warning("Veeam host_id=%s not found, falling back to default", host_id)

    if _default_provider is not None:
        return _default_provider

    if db is not None:
        try:
            from app.repositories.integration_profile_repository import (
                IntegrationProfileRepository,
            )

            profile = IntegrationProfileRepository.get_enabled_by_type(db, "veeam")
            if profile is not None:
                try:
                    _default_provider = _build_provider(profile)
                    _providers[profile.id] = _default_provider
                    logger.info("Using production Veeam provider (profile: %s)", profile.name)
                    return _default_provider
                except Exception as e:
                    logger.warning("Failed to create default Veeam provider: %s", e)
        except Exception as e:
            logger.warning("Failed to load Veeam profile from DB: %s", e)

    logger.info("Using mock Veeam provider")
    from .mock_provider import MockVeeamProvider

    _default_provider = MockVeeamProvider()
    return _default_provider


def _get_target_inventory(agent, target_id: int) -> dict:
    """Extract the remote target inventory dict from an agent."""
    if not agent.inventory_json:
        return {}
    try:
        full_inv = json.loads(agent.inventory_json)
        remote = full_inv.get("remote_targets", {})
        target_data = remote.get(f"target-{target_id}", {})
        return target_data.get("inventory", {})
    except (json.JSONDecodeError, TypeError):
        return {}


def _get_agent_provider(db: Session | None, target_id: int) -> VeeamProvider:
    """Build an AgentVeeamProvider from stored remote target inventory."""
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

    inv = _get_target_inventory(agent, target_id)
    veeam = inv.get("veeam")
    if not veeam:
        raise ValueError(f"No Veeam inventory collected for target {target_id}")

    async def _dispatch_on_agent(command_str: str) -> dict:
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

    from .agent_provider import AgentVeeamProvider
    return AgentVeeamProvider(
        veeam,
        target_hostname=target.hostname,
        agent_id=agent.id,
        target_id=target.id,
        dispatch_cmd=_dispatch_on_agent,
    )


def reset_veeam_provider(host_id: int | None = None) -> None:
    """Reset cached provider(s). If host_id given, reset only that one."""
    global _default_provider
    if host_id is not None:
        if host_id > 0:
            _providers.pop(host_id, None)
    else:
        _providers.clear()
        _default_provider = None


def get_all_veeam_providers(db: Session) -> list[tuple[str, VeeamProvider]]:
    """Return list of (name, provider) for all enabled Veeam profiles."""
    from app.repositories.integration_profile_repository import (
        IntegrationProfileRepository,
    )

    profiles = IntegrationProfileRepository.get_all_enabled_by_type(db, "veeam")
    result: list[tuple[str, VeeamProvider]] = []
    for p in profiles:
        try:
            provider = _build_provider(p)
            result.append((p.name, provider))
        except Exception as e:
            logger.warning("Failed to build Veeam provider for %s: %s", p.name, e)
    return result
