"""
Mission Control Identity Provider Factory

Singleton factory that returns the correct identity provider
based on the platform type.

Sprint 2.2.1 - Identity Platform Foundation.
"""

import logging

from app.providers.identity.ad_provider import (
    MockActiveDirectoryProvider,
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


def get_active_directory_provider() -> ActiveDirectoryProvider:
    """
    Return the singleton Active Directory provider.

    Currently returns MockActiveDirectoryProvider.
    Will return LDAPProvider or PowerShellProvider in Sprint 2.2.2.
    """
    global _ad_provider

    if _ad_provider is None:
        _ad_provider = MockActiveDirectoryProvider()
        logger.info("Created singleton MockActiveDirectoryProvider")

    return _ad_provider


def get_microsoft365_provider() -> Microsoft365Provider:
    """
    Return the singleton Microsoft 365 provider.

    Currently returns MockMicrosoft365Provider.
    Will return GraphProvider in Sprint 2.2.3.
    """
    global _m365_provider

    if _m365_provider is None:
        _m365_provider = MockMicrosoft365Provider()
        logger.info("Created singleton MockMicrosoft365Provider")

    return _m365_provider
