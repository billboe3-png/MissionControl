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
    hosts = [
        {"id": p.id, "name": p.name, "host": p.base_url or "unknown"}
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
            inv = {}
            if agent.inventory_json:
                try:
                    full_inv = json.loads(agent.inventory_json)
                    remote = full_inv.get("remote_targets", {})
                    inv = remote.get(f"target-{target.id}", {}).get("inventory", {})
                except (json.JSONDecodeError, TypeError):
                    pass
            hyperv = inv.get("hyperv")
            if hyperv and hyperv.get("vm_count", 0) > 0:
                hosts.append({
                    "id": -target.id,
                    "name": f"{target.name} (Agent)",
                    "host": target.hostname,
                })
    except Exception as e:
        logger.debug("Could not load agent targets for host list: %s", e)

    return hosts


def get_hyperv_provider(db: Session | None = None, host_id: int | None = None) -> HyperVProvider:
    """Return the Hyper-V provider for a given host_id.

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
        return _default_provider

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

    logger.info("Using mock Hyper-V provider")
    from .mock_provider import MockHyperVProvider

    _default_provider = MockHyperVProvider()
    return _default_provider


def _get_agent_provider(db: Session | None, target_id: int) -> HyperVProvider:
    """Build an AgentHyperVProvider from stored remote target inventory."""
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
        raise ValueError(f"No Hyper-V inventory collected for target {target_id}")

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


def reset_hyperv_provider(host_id: int | None = None) -> None:
    """Reset cached provider(s). If host_id given, reset only that one."""
    global _default_provider
    if host_id is not None:
        if host_id > 0:
            _providers.pop(host_id, None)
    else:
        _providers.clear()
        _default_provider = None
