"""
Mission Control Identity Provider Base

Abstract base classes defining the contract for all identity
providers. Standardized methods: test_connection, get_summary,
get_users, get_groups, get_devices, get_health.

Providers never raise exceptions to the dashboard.
They return {"connected": false, "error": "..."} on failure.

Sprint 2.2.0 - Microsoft 365 & Active Directory Integration.
"""

from abc import ABC, abstractmethod


class ActiveDirectoryProvider(ABC):
    """
    Abstract base class for Active Directory providers.

    Standardized interface:
    - test_connection: Verify AD connectivity
    - get_summary: Get domain/forest overview
    - get_users: List user summaries
    - get_groups: List group summaries
    - get_devices: List computer/device summaries
    - get_health: Get replication and health status
    """

    @abstractmethod
    async def test_connection(self) -> dict:
        """Test connectivity to Active Directory."""
        ...

    @abstractmethod
    async def get_summary(self) -> dict:
        """Get domain and forest summary information."""
        ...

    @abstractmethod
    async def get_users(self) -> dict:
        """List user summaries."""
        ...

    @abstractmethod
    async def get_groups(self) -> dict:
        """List group summaries."""
        ...

    @abstractmethod
    async def get_devices(self) -> dict:
        """List computer/device summaries."""
        ...

    @abstractmethod
    async def get_health(self) -> dict:
        """Get replication and health status."""
        ...


class Microsoft365Provider(ABC):
    """
    Abstract base class for Microsoft 365 providers.

    Standardized interface:
    - test_connection: Verify M365 connectivity
    - get_summary: Get tenant overview
    - get_users: List user summaries
    - get_groups: List group summaries
    - get_devices: List device summaries
    - get_health: Get service health status
    """

    @abstractmethod
    async def test_connection(self) -> dict:
        """Test connectivity to Microsoft 365."""
        ...

    @abstractmethod
    async def get_summary(self) -> dict:
        """Get tenant summary information."""
        ...

    @abstractmethod
    async def get_users(self) -> dict:
        """List user summaries."""
        ...

    @abstractmethod
    async def get_groups(self) -> dict:
        """List group summaries."""
        ...

    @abstractmethod
    async def get_devices(self) -> dict:
        """List device summaries."""
        ...

    @abstractmethod
    async def get_health(self) -> dict:
        """Get service health status."""
        ...
