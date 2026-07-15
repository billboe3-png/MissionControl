"""
Mission Control Zabbix Provider Factory

Singleton factory that returns the correct Zabbix provider
based on configuration.

Priority order:
  1. Active IntegrationProfile in the database (when db is provided)
  2. ZABBIX_URL + ZABBIX_USERNAME environment variables
  3. MockZabbixProvider (fallback for dev/testing)

Sprint 2.3.0 - Enterprise Zabbix Integration.
Sprint 2.3.2 - Database-driven provider selection.
"""

import logging

from app.providers.zabbix.base_provider import ZabbixProvider
from app.providers.zabbix.mock_provider import MockZabbixProvider

logger = logging.getLogger(__name__)

_zabbix_provider: ZabbixProvider | None = None


def _is_zabbix_configured() -> bool:
    """Check if production Zabbix is configured via env vars."""
    try:
        from app.core.config import get_settings

        settings = get_settings()
        return bool(settings.zabbix_url and settings.zabbix_username)
    except Exception:
        return False


def _build_provider_from_profile(profile) -> ZabbixProvider:
    """Create an ApiZabbixProvider from a database IntegrationProfile."""
    from app.core.security import CredentialCipher
    from app.core.config import get_settings
    from app.providers.zabbix.zabbix_provider import ApiZabbixProvider

    password = None
    if profile.encrypted_secret:
        try:
            settings = get_settings()
            cipher = CredentialCipher(
                settings.missioncontrol_secret_key
            )
            password = cipher.decrypt(profile.encrypted_secret)
        except Exception as e:
            logger.warning(
                "Failed to decrypt Zabbix credential: %s", e
            )
            password = None

    return ApiZabbixProvider(
        url=profile.base_url,
        username=profile.username,
        password=password,
        verify_ssl=profile.verify_ssl,
        timeout=profile.timeout,
    )


def _resolve_from_db(db) -> ZabbixProvider | None:
    """Query DB for an active Zabbix integration profile."""
    try:
        from app.repositories.integration_profile_repository import (
            IntegrationProfileRepository,
        )

        profile = IntegrationProfileRepository.get_enabled_by_type(
            db, "zabbix"
        )
        if profile is None:
            logger.debug("No active Zabbix profile in database")
            return None

        if not profile.base_url:
            logger.warning(
                "Active Zabbix profile %s has no URL", profile.id
            )
            return None

        if not profile.username:
            logger.warning(
                "Active Zabbix profile %s has no username", profile.id
            )
            return None

        logger.info(
            "Using database profile '%s' for Zabbix provider",
            profile.name,
        )
        return _build_provider_from_profile(profile)
    except Exception as e:
        logger.warning("Failed to resolve Zabbix from DB: %s", e)
        return None


def get_zabbix_provider(db=None) -> ZabbixProvider:
    """
    Return the singleton Zabbix provider.

    Resolution order:
      1. Cached singleton (if already created)
      2. Active Zabbix IntegrationProfile in DB (when *db* provided)
      3. ZABBIX_URL + ZABBIX_USERNAME env vars
      4. MockZabbixProvider (fallback)

    When *db* is None the database is skipped and the provider
    is resolved from env vars or falls back to mock.
    """
    global _zabbix_provider

    if _zabbix_provider is not None:
        return _zabbix_provider

    # 1. Try database profile
    if db is not None:
        db_provider = _resolve_from_db(db)
        if db_provider is not None:
            _zabbix_provider = db_provider
            return _zabbix_provider

    # 2. Fall back to env vars
    if _is_zabbix_configured():
        from app.providers.zabbix.zabbix_provider import ApiZabbixProvider

        _zabbix_provider = ApiZabbixProvider()
        logger.info("Created singleton ApiZabbixProvider (env config)")
    else:
        _zabbix_provider = MockZabbixProvider()
        logger.info("Created singleton MockZabbixProvider (no config)")

    return _zabbix_provider


def reset_zabbix_provider() -> None:
    """Reset singleton provider. Used for testing."""
    global _zabbix_provider
    _zabbix_provider = None
    logger.info("Zabbix provider singleton reset")
