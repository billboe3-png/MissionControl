"""
Mission Control Zabbix Service

Business logic for Zabbix monitoring operations.
Resolves provider per-call using DB session for profile lookup.

Sprint 2.3.0 - Enterprise Zabbix Integration.
Sprint 2.3.2 - DB-driven provider resolution.
"""

import logging

from app.providers.zabbix.provider_factory import get_zabbix_provider

logger = logging.getLogger(__name__)


class ZabbixService:
    """
    Service layer for Zabbix operations.

    Resolves the provider on each call so that DB-stored
    integration profiles are respected without requiring
    a manual singleton reset.
    """

    def _get_provider(self, db=None):
        return get_zabbix_provider(db)

    async def test_connection(self, db=None) -> dict:
        """Test Zabbix connectivity."""
        return await self._get_provider(db).test_connection()

    async def login(self, db=None) -> dict:
        """Authenticate with Zabbix."""
        return await self._get_provider(db).login()

    async def logout(self, db=None) -> dict:
        """End Zabbix session."""
        return await self._get_provider(db).logout()

    async def get_summary(self, db=None) -> dict:
        """Get monitoring overview."""
        return await self._get_provider(db).get_summary()

    async def get_hosts(self, db=None) -> dict:
        """List monitored hosts."""
        return await self._get_provider(db).get_hosts()

    async def get_host_groups(self, db=None) -> dict:
        """List host groups."""
        return await self._get_provider(db).get_host_groups()

    async def get_triggers(self, db=None) -> dict:
        """List triggers."""
        return await self._get_provider(db).get_triggers()

    async def get_problems(self, db=None) -> dict:
        """List current problems."""
        return await self._get_provider(db).get_problems()

    async def get_events(self, db=None) -> dict:
        """List recent events."""
        return await self._get_provider(db).get_events()

    async def get_items(self, db=None) -> dict:
        """List items."""
        return await self._get_provider(db).get_items()

    async def get_history(self, db=None) -> dict:
        """Get historical data."""
        return await self._get_provider(db).get_history()

    async def get_templates(self, db=None) -> dict:
        """List templates."""
        return await self._get_provider(db).get_templates()

    async def get_dashboards(self, db=None) -> dict:
        """List dashboards."""
        return await self._get_provider(db).get_dashboards()

    async def get_maps(self, db=None) -> dict:
        """List maps."""
        return await self._get_provider(db).get_maps()

    async def get_health(self, db=None) -> dict:
        """Get Zabbix health."""
        return await self._get_provider(db).get_health()


zabbix_service = ZabbixService()
