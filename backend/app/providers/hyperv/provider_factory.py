"""
Mission Control Hyper-V Provider Factory

Manages multiple Hyper-V providers keyed by IntegrationProfile ID.
Falls back to mock when no profile is configured.
"""

import logging

from sqlalchemy.orm import Session

from .base_provider import HyperVProvider

logger = logging.getLogger(__name__)

_providers: dict[int, HyperVProvider] = {}
_default_provider: HyperVProvider | None = None


def _build_provider(profile) -> HyperVProvider:
    """Create a production provider from an IntegrationProfile."""
    from app.core.security import CredentialCipher
    from app.core.config import get_settings

    settings = get_settings()
    cipher = CredentialCipher(settings.missioncontrol_secret_key)
    password = cipher.decrypt(profile.encrypted_secret) if profile.encrypted_secret else ""
    host = profile.base_url or ""
    username = profile.username or ""
    timeout = profile.timeout or 30

    if not host or not username:
        raise ValueError("Profile missing base_url or username")

    from .hyperv_provider import HyperVPowerShellProvider

    return HyperVPowerShellProvider(
        host=host,
        port=22,
        username=username,
        password=password,
        timeout=timeout,
    )


def list_hyperv_hosts(db: Session) -> list[dict]:
    """Return all enabled Hyper-V hosts for the frontend selector."""
    from app.repositories.integration_profile_repository import (
        IntegrationProfileRepository,
    )

    profiles = IntegrationProfileRepository.get_all_enabled_by_type(db, "hyperv")
    return [
        {"id": p.id, "name": p.name, "host": p.base_url or "unknown"}
        for p in profiles
    ]


def get_hyperv_provider(db: Session | None = None, host_id: int | None = None) -> HyperVProvider:
    """Return the Hyper-V provider for a given host_id.

    If host_id is provided, loads (or caches) the provider for that profile.
    If host_id is None, returns the default (first available) provider.
    Falls back to mock when no profile exists.
    """
    global _default_provider

    if host_id is not None:
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


def reset_hyperv_provider(host_id: int | None = None) -> None:
    """Reset cached provider(s). If host_id given, reset only that one."""
    global _default_provider
    if host_id is not None:
        _providers.pop(host_id, None)
    else:
        _providers.clear()
        _default_provider = None
