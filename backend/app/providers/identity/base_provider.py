"""
Mission Control Identity Provider Base

Abstract base class defining the contract for all identity providers.
Each provider implements Active Directory or Microsoft 365 operations.

Sprint 2.2.1 - Identity Platform Foundation.
"""

from abc import ABC, abstractmethod


class ActiveDirectoryProvider(ABC):
    """
    Abstract base class for Active Directory providers.

    Each concrete provider must implement:
    - get_domain_controllers: List domain controllers
    - get_forest: Get forest information
    - get_domain: Get domain information
    - get_organizational_units: List OUs
    - get_users: List user summaries
    - get_groups: List group summaries
    - get_computers: List computer summaries
    - get_gpos: List Group Policy Objects
    - get_fsmo_roles: Get FSMO role holders
    - get_dns_health: Get DNS health status
    - get_dhcp_health: Get DHCP health status
    """

    @abstractmethod
    async def get_domain_controllers(self) -> dict:
        """List domain controllers in the forest."""
        ...

    @abstractmethod
    async def get_forest(self) -> dict:
        """Get forest information."""
        ...

    @abstractmethod
    async def get_domain(self) -> dict:
        """Get domain information."""
        ...

    @abstractmethod
    async def get_organizational_units(self) -> dict:
        """List organizational units."""
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
    async def get_computers(self) -> dict:
        """List computer summaries."""
        ...

    @abstractmethod
    async def get_gpos(self) -> dict:
        """List Group Policy Objects."""
        ...

    @abstractmethod
    async def get_fsmo_roles(self) -> dict:
        """Get FSMO role holders."""
        ...

    @abstractmethod
    async def get_dns_health(self) -> dict:
        """Get DNS health status."""
        ...

    @abstractmethod
    async def get_dhcp_health(self) -> dict:
        """Get DHCP health status."""
        ...


class Microsoft365Provider(ABC):
    """
    Abstract base class for Microsoft 365 providers.

    Each concrete provider must implement:
    - get_tenant: Get tenant information
    - get_licenses: List license summaries
    - get_service_health: Get Microsoft 365 service health
    - get_entra_health: Get Entra ID health
    - get_exchange_health: Get Exchange Online health
    - get_secure_score: Get Secure Score
    - get_message_center: Get Message Center items
    """

    @abstractmethod
    async def get_tenant(self) -> dict:
        """Get tenant information."""
        ...

    @abstractmethod
    async def get_licenses(self) -> dict:
        """List license summaries."""
        ...

    @abstractmethod
    async def get_service_health(self) -> dict:
        """Get Microsoft 365 service health."""
        ...

    @abstractmethod
    async def get_entra_health(self) -> dict:
        """Get Entra ID health."""
        ...

    @abstractmethod
    async def get_exchange_health(self) -> dict:
        """Get Exchange Online health."""
        ...

    @abstractmethod
    async def get_secure_score(self) -> dict:
        """Get Secure Score."""
        ...

    @abstractmethod
    async def get_message_center(self) -> dict:
        """Get Message Center items."""
        ...
