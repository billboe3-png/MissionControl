"""
Mission Control Hyper-V Provider Factory

Singleton factory that selects mock or production provider
based on IntegrationProfile configuration. Never reads config.py.
"""

import logging

from sqlalchemy.orm import Session

from .base_provider import HyperVProvider

logger = logging.getLogger(__name__)

_provider: HyperVProvider | None = None


def get_hyperv_provider(db: Session | None = None) -> HyperVProvider:
    """Return the Hyper-V provider.

    If a database session is provided, looks up the enabled
    IntegrationProfile of type 'hyperv' and creates a production
    provider with injected credentials. Falls back to mock.
    """
    global _provider
    if _provider is not None:
        return _provider

    if db is not None:
        try:
            from app.repositories.integration_profile_repository import (
                IntegrationProfileRepository,
            )
            from app.core.security import CredentialCipher
            from app.core.config import get_settings

            profile = IntegrationProfileRepository.get_enabled_by_type(
                db, "hyperv"
            )
            if profile is not None:
                settings = get_settings()
                cipher = CredentialCipher(settings.missioncontrol_secret_key)
                password = cipher.decrypt(profile.encrypted_secret) if profile.encrypted_secret else ""
                host = profile.base_url or ""
                username = profile.username or ""
                timeout = profile.timeout or 30

                if host and username:
                    logger.info(
                        "Using production Hyper-V provider (profile: %s)",
                        profile.name,
                    )
                    from .hyperv_provider import HyperVPowerShellProvider

                    _provider = HyperVPowerShellProvider(
                        host=host,
                        port=22,
                        username=username,
                        password=password,
                        timeout=timeout,
                    )
                    return _provider
        except Exception as e:
            logger.warning(
                "Failed to load Hyper-V profile from DB: %s", e
            )

    logger.info("Using mock Hyper-V provider")
    from .mock_provider import MockHyperVProvider

    _provider = MockHyperVProvider()
    return _provider


def reset_hyperv_provider() -> None:
    global _provider
    _provider = None
