"""
Mission Control Veeam B&R Provider -- Abstract Base

Defines the contract for Veeam Backup & Replication integrations.
All methods return dicts and never raise exceptions.
"""

from abc import ABC, abstractmethod


class VeeamProvider(ABC):
    """Abstract Veeam B&R provider interface."""

    @abstractmethod
    async def test_connection(self) -> dict:
        """Test connectivity to the Veeam B&R server."""

    @abstractmethod
    async def get_summary(self) -> dict:
        """Return aggregate backup statistics."""

    @abstractmethod
    async def get_jobs(self) -> dict:
        """List all backup/replication jobs."""

    @abstractmethod
    async def get_job_detail(self, job_id: str) -> dict:
        """Get detailed info for a single job."""

    @abstractmethod
    async def get_sessions(self) -> dict:
        """List recent backup sessions."""

    @abstractmethod
    async def get_repositories(self) -> dict:
        """List backup repositories."""

    @abstractmethod
    async def get_managed_servers(self) -> dict:
        """List managed servers ( hypervisors, Windows/Linux )."""

    @abstractmethod
    async def get_restore_points(self, vm_id: str | None = None) -> dict:
        """List restore points, optionally filtered by VM."""

    @abstractmethod
    async def get_license(self) -> dict:
        """Get Veeam license information."""

    @abstractmethod
    async def get_capacity_tier(self) -> dict:
        """Get capacity tier (object storage) status."""

    @abstractmethod
    async def start_job(self, job_id: str) -> dict:
        """Start a backup job."""

    @abstractmethod
    async def stop_job(self, job_id: str) -> dict:
        """Stop a running backup job."""

    @abstractmethod
    async def get_health(self) -> dict:
        """Get overall Veeam server health."""

    @abstractmethod
    async def get_session_stats(self) -> dict:
        """Get backup session transfer statistics (via SSH bridge)."""

    @abstractmethod
    async def get_job_stats(self) -> dict:
        """Get aggregated transfer statistics per backup job (via SSH bridge)."""

    @abstractmethod
    async def get_job_stats_daily(self, days: int = 7) -> dict:
        """Get per-job per-day transfer statistics (via SSH bridge)."""
