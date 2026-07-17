"""
Mission Control Proxmox Provider Factory

Singleton factory that selects mock or production provider
based on IntegrationProfile configuration. Never reads config.py.
"""

import logging

from sqlalchemy.orm import Session

from .base_provider import ProxmoxProvider

logger = logging.getLogger(__name__)

_provider: ProxmoxProvider | None = None


def get_proxmox_provider(db: Session | None = None) -> ProxmoxProvider:
    """Return the Proxmox provider.

    If a database session is provided, looks up the enabled
    IntegrationProfile of type 'proxmox' and creates a production
    provider with injected credentials. Falls back to mock.
    """
    global _provider
    if _provider is not None:
        return _provider

    if db is not None:
        try:
            from app.core.config import get_settings
            from app.core.security import CredentialCipher
            from app.repositories.integration_profile_repository import (
                IntegrationProfileRepository,
            )

            profile = IntegrationProfileRepository.get_enabled_by_type(
                db, "proxmox"
            )
            if profile is not None:
                settings = get_settings()
                cipher = CredentialCipher(settings.missioncontrol_secret_key)
                token_secret = ""
                if profile.encrypted_secret:
                    token_secret = cipher.decrypt(
                        profile.encrypted_secret
                    )
                base_url = profile.base_url or ""
                token_id = profile.username or ""
                timeout = profile.timeout or 30
                verify_ssl = (
                    profile.verify_ssl
                    if profile.verify_ssl is not None
                    else True
                )

                if base_url and token_id:
                    if token_secret:
                        full_token = f"{token_id}={token_secret}"
                    else:
                        full_token = token_id
                    logger.info(
                        "Using production Proxmox provider (profile: %s)",
                        profile.name,
                    )
                    from .proxmox_provider import ProxmoxRESTProvider

                    _provider = ProxmoxRESTProvider(
                        base_url=base_url,
                        token=full_token,
                        timeout=timeout,
                        verify_ssl=verify_ssl,
                    )
                    return _provider
        except Exception as e:
            logger.warning(
                "Failed to load Proxmox profile from DB: %s", e
            )

    logger.info("Using mock Proxmox provider")
    from .mock_provider import MockProxmoxProvider

    _provider = MockProxmoxProvider()
    return _provider


def reset_proxmox_provider() -> None:
    global _provider
    _provider = None
