"""
Mission Control Identity Provider Factory

Singleton factory that returns the correct identity provider
based on the platform type. Auto-selects production vs mocked
providers based on configuration.

Sprint 2.2.0 - Microsoft 365 & Active Directory Integration.
"""

import logging

from app.providers.identity.ad_provider import (
    MockActiveDirectoryProvider,
)
from app.providers.identity.agent_ad_provider import (
    AgentActiveDirectoryProvider,
)
from app.providers.identity.base_provider import (
    ActiveDirectoryProvider,
    Microsoft365Provider,
)
from app.providers.identity.m365_provider import (
    MockMicrosoft365Provider,
)

logger = logging.getLogger(__name__)

_ad_provider: ActiveDirectoryProvider | None = None
_m365_provider: Microsoft365Provider | None = None


def _is_ad_configured() -> bool:
    """Check if production AD is configured."""
    try:
        from app.core.config import get_settings

        settings = get_settings()
        return bool(settings.ad_server and settings.ad_username)
    except Exception:
        return False


def _is_m365_configured() -> bool:
    """Check if production M365 is configured."""
    try:
        from app.core.config import get_settings

        settings = get_settings()
        return bool(settings.m365_tenant_id and settings.m365_client_id)
    except Exception:
        return False


def get_active_directory_provider() -> ActiveDirectoryProvider:
    """
    Return the singleton Active Directory provider.

    Returns LDAPActiveDirectoryProvider if AD_SERVER and AD_USERNAME
    are configured, otherwise returns MockActiveDirectoryProvider.
    """
    global _ad_provider

    if _ad_provider is not None:
        return _ad_provider

    if _is_ad_configured():
        from app.providers.identity.ldap_ad_provider import (
            LDAPActiveDirectoryProvider,
        )

        _ad_provider = LDAPActiveDirectoryProvider()
        logger.info(
            "Created singleton LDAPActiveDirectoryProvider "
            "(production)"
        )
    else:
        _ad_provider = MockActiveDirectoryProvider()
        logger.info(
            "Created singleton MockActiveDirectoryProvider "
            "(no config)"
        )

    return _ad_provider


def get_microsoft365_provider() -> Microsoft365Provider:
    """
    Return the singleton Microsoft 365 provider.

    Returns GraphMicrosoft365Provider if M365_TENANT_ID and
    M365_CLIENT_ID are configured, otherwise returns
    MockMicrosoft365Provider.
    """
    global _m365_provider

    if _m365_provider is not None:
        return _m365_provider

    if _is_m365_configured():
        from app.providers.identity.graph_m365_provider import (
            GraphMicrosoft365Provider,
        )

        _m365_provider = GraphMicrosoft365Provider()
        logger.info(
            "Created singleton GraphMicrosoft365Provider "
            "(production)"
        )
    else:
        _m365_provider = MockMicrosoft365Provider()
        logger.info(
            "Created singleton MockMicrosoft365Provider "
            "(no config)"
        )

    return _m365_provider


def reset_providers() -> None:
    """
    Reset singleton providers. Used for testing.

    Calling get_active_directory_provider() or
    get_microsoft365_provider() after this will create new instances.
    """
    global _ad_provider, _m365_provider
    _ad_provider = None
    _m365_provider = None
    logger.info("Provider singletons reset")
