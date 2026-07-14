"""
Mission Control Zabbix Provider Factory

Singleton factory that returns the correct Zabbix provider
based on configuration.

Sprint 2.3.0 - Enterprise Zabbix Integration.
"""

import logging

from app.providers.zabbix.base_provider import ZabbixProvider
from app.providers.zabbix.mock_provider import MockZabbixProvider

logger = logging.getLogger(__name__)

_zabbix_provider: ZabbixProvider | None = None


def _is_zabbix_configured() -> bool:
    """Check if production Zabbix is configured."""
    try:
        from app.core.config import get_settings

        settings = get_settings()
        return bool(settings.zabbix_url and settings.zabbix_username)
    except Exception:
        return False


def get_zabbix_provider() -> ZabbixProvider:
    """
    Return the singleton Zabbix provider.

    Returns ApiZabbixProvider if ZABBIX_URL and ZABBIX_USERNAME
    are configured, otherwise returns MockZabbixProvider.
    """
    global _zabbix_provider

    if _zabbix_provider is not None:
        return _zabbix_provider

    if _is_zabbix_configured():
        from app.providers.zabbix.zabbix_provider import ApiZabbixProvider

        _zabbix_provider = ApiZabbixProvider()
        logger.info("Created singleton ApiZabbixProvider (production)")
    else:
        _zabbix_provider = MockZabbixProvider()
        logger.info("Created singleton MockZabbixProvider (no config)")

    return _zabbix_provider


def reset_zabbix_provider() -> None:
    """Reset singleton provider. Used for testing."""
    global _zabbix_provider
    _zabbix_provider = None
    logger.info("Zabbix provider singleton reset")
