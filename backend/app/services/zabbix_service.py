"""
Mission Control Zabbix Service

Business logic for Zabbix monitoring operations.
Orchestrates provider calls and formats responses.

Sprint 2.3.0 - Enterprise Zabbix Integration.
"""

import logging

from app.providers.zabbix.provider_factory import get_zabbix_provider

logger = logging.getLogger(__name__)


class ZabbixService:
    """
    Service layer for Zabbix operations.

    Delegates to the Zabbix provider and formats responses.
    """

    def __init__(self) -> None:
        self._provider = get_zabbix_provider()

    async def test_connection(self) -> dict:
        """Test Zabbix connectivity."""
        return await self._provider.test_connection()

    async def login(self) -> dict:
        """Authenticate with Zabbix."""
        return await self._provider.login()

    async def logout(self) -> dict:
        """End Zabbix session."""
        return await self._provider.logout()

    async def get_summary(self) -> dict:
        """Get monitoring overview."""
        return await self._provider.get_summary()

    async def get_hosts(self) -> dict:
        """List monitored hosts."""
        return await self._provider.get_hosts()

    async def get_host_groups(self) -> dict:
        """List host groups."""
        return await self._provider.get_host_groups()

    async def get_triggers(self) -> dict:
        """List triggers."""
        return await self._provider.get_triggers()

    async def get_problems(self) -> dict:
        """List current problems."""
        return await self._provider.get_problems()

    async def get_events(self) -> dict:
        """List recent events."""
        return await self._provider.get_events()

    async def get_items(self) -> dict:
        """List items."""
        return await self._provider.get_items()

    async def get_history(self) -> dict:
        """Get historical data."""
        return await self._provider.get_history()

    async def get_templates(self) -> dict:
        """List templates."""
        return await self._provider.get_templates()

    async def get_dashboards(self) -> dict:
        """List dashboards."""
        return await self._provider.get_dashboards()

    async def get_maps(self) -> dict:
        """List maps."""
        return await self._provider.get_maps()

    async def get_health(self) -> dict:
        """Get Zabbix health."""
        return await self._provider.get_health()


zabbix_service = ZabbixService()
