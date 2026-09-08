"""
Veeam Provider Base Class

Abstract base class for Veeam providers.
"""

from abc import ABC, abstractmethod
from typing import Any


class VeeamProvider(ABC):
    """Abstract base class for Veeam providers."""

    @abstractmethod
    async def test_connection(self) -> dict:
        """Test connection to Veeam server."""
        pass

    @abstractmethod
    async def get_summary(self) -> dict:
        """Get Veeam server summary."""
        pass

    @abstractmethod
    async def get_jobs(self) -> dict:
        """Get all Veeam jobs."""
        pass

    @abstractmethod
    async def get_job_detail(self, job_id: str) -> dict:
        """Get details for a specific job."""
        pass

    @abstractmethod
    async def get_sessions(self) -> dict:
        """Get Veeam sessions."""
        pass

    @abstractmethod
    async def get_repositories(self) -> dict:
        """Get Veeam repositories."""
        pass

    @abstractmethod
    async def get_managed_servers(self) -> dict:
        """Get managed servers."""
        pass

    @abstractmethod
    async def get_restore_points(self, vm_id: str | None = None) -> dict:
        """Get restore points."""
        pass

    @abstractmethod
    async def get_license(self) -> dict:
        """Get license information."""
        pass

    @abstractmethod
    async def get_capacity_tier(self) -> dict:
        """Get capacity tier information."""
        pass

    @abstractmethod
    async def start_job(self, job_id: str) -> dict:
        """Start a Veeam job."""
        pass

    @abstractmethod
    async def stop_job(self, job_id: str) -> dict:
        """Stop a Veeam job."""
        pass

    @abstractmethod
    async def get_health(self) -> dict:
        """Get health status."""
        pass

    @abstractmethod
    async def get_session_stats(self) -> dict:
        """Get session statistics."""
        pass

    @abstractmethod
    async def get_job_stats(self) -> dict:
        """Get job statistics."""
        pass

    @abstractmethod
    async def get_job_stats_daily(self, days: int = 7) -> dict:
        """Get daily job statistics."""
        pass

    @abstractmethod
    async def get_restore_points(self, vm_id: str | None = None) -> dict:
        """Get restore points."""
        pass

    @abstractmethod
    async def start_job(self, job_id: str) -> dict:
        """Start a Veeam job."""
        pass

    @abstractmethod
    async def stop_job(self, job_id: str) -> dict:
        """Stop a Veeam job."""
        pass