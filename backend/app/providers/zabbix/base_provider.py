"""
Mission Control Zabbix Provider Base

Abstract base class defining the contract for Zabbix providers.
Standardized methods: test_connection, login, logout, get_summary,
get_hosts, get_host_groups, get_triggers, get_problems, get_events,
get_items, get_history, get_templates, get_dashboards, get_maps,
get_health.

Providers never raise exceptions to the dashboard.
They return {"connected": false, "error": "..."} on failure.

Sprint 2.3.0 - Enterprise Zabbix Integration.
"""

from abc import ABC, abstractmethod


class ZabbixProvider(ABC):
    """
    Abstract base class for Zabbix providers.

    Standardized interface for monitoring data retrieval.
    """

    @abstractmethod
    async def test_connection(self) -> dict:
        """Test connectivity to Zabbix."""
        ...

    @abstractmethod
    async def login(self) -> dict:
        """Authenticate with Zabbix."""
        ...

    @abstractmethod
    async def logout(self) -> dict:
        """End Zabbix session."""
        ...

    @abstractmethod
    async def get_summary(self) -> dict:
        """Get monitoring overview."""
        ...

    @abstractmethod
    async def get_hosts(self) -> dict:
        """List monitored hosts."""
        ...

    @abstractmethod
    async def get_host_groups(self) -> dict:
        """List host groups."""
        ...

    @abstractmethod
    async def get_triggers(self) -> dict:
        """List triggers."""
        ...

    @abstractmethod
    async def get_problems(self) -> dict:
        """List current problems."""
        ...

    @abstractmethod
    async def get_events(self) -> dict:
        """List recent events."""
        ...

    @abstractmethod
    async def get_items(self) -> dict:
        """List items."""
        ...

    @abstractmethod
    async def get_history(self) -> dict:
        """Get historical data."""
        ...

    @abstractmethod
    async def get_templates(self) -> dict:
        """List templates."""
        ...

    @abstractmethod
    async def get_dashboards(self) -> dict:
        """List dashboards."""
        ...

    @abstractmethod
    async def get_maps(self) -> dict:
        """List maps."""
        ...

    @abstractmethod
    async def get_health(self) -> dict:
        """Get Zabbix health."""
        ...
