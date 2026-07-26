"""
Veeam B&R Mock Provider

Returns realistic sample data for development and testing.
Used when no real Veeam B&R server is configured.
"""

import logging
from datetime import UTC, datetime, timedelta

from app.providers.veeam.base_provider import VeeamProvider

logger = logging.getLogger(__name__)


def _ts(offset_hours: int = 0) -> str:
    return (datetime.now(UTC) - timedelta(hours=offset_hours)).isoformat()


class MockVeeamProvider(VeeamProvider):
    """Mock Veeam B&R provider with realistic sample data."""

    async def test_connection(self) -> dict:
        return {
            "connected": True,
            "version": "12.3.1.1139",
            "name": "VEEAM-SRV01",
            "server_id": "b7e2c3d4-5678-9abc-def0-123456789abc",
            "_mock": True,
        }

    async def get_summary(self) -> dict:
        return {
            "success": True,
            "version": "12.3.1.1139",
            "name": "VEEAM-SRV01",
            "total_jobs": 14,
            "running_jobs": 2,
            "total_repositories": 3,
            "total_space_bytes": 5_000_000_000_000,
            "used_space_bytes": 2_100_000_000_000,
            "recent_sessions": 42,
            "sessions_success": 38,
            "sessions_warning": 3,
            "sessions_failed": 1,
            "_mock": True,
        }

    async def get_jobs(self) -> dict:
        jobs = [
            {"id": "job-001", "name": "Daily Backup - File Servers", "type": "Backup",
             "status": "Running", "nextRun": _ts(-1), "lastRun": _ts(2),
             "schedule": "Daily at 22:00", "includedObjects": "24 VMs",
             "estimatedSizeBytes": 500_000_000_000, "processedBytes": 120_000_000_000,
             "_mock": True},
            {"id": "job-002", "name": "SQL Server Backup", "type": "Backup",
             "status": "Success", "nextRun": _ts(-2), "lastRun": _ts(8),
             "schedule": "Daily at 01:00", "includedObjects": "6 VMs",
             "estimatedSizeBytes": 200_000_000_000, "processedBytes": 200_000_000_000,
             "_mock": True},
            {"id": "job-003", "name": "Replication to DR", "type": "Replica",
             "status": "Running", "nextRun": _ts(-3), "lastRun": _ts(4),
             "schedule": "Every 4 hours", "includedObjects": "12 VMs",
             "estimatedSizeBytes": 300_000_000_000, "processedBytes": 80_000_000_000,
             "_mock": True},
            {"id": "job-004", "name": "Exchange Backup", "type": "Backup",
             "status": "Success", "nextRun": _ts(-4), "lastRun": _ts(12),
             "schedule": "Daily at 23:00", "includedObjects": "4 VMs",
             "estimatedSizeBytes": 150_000_000_000, "processedBytes": 150_000_000_000,
             "_mock": True},
            {"id": "job-005", "name": "Dev/Test Restore", "type": "Backup",
             "status": "Failed", "nextRun": _ts(-5), "lastRun": _ts(6),
             "schedule": "Weekly Sunday", "includedObjects": "8 VMs",
             "estimatedSizeBytes": 80_000_000_000, "processedBytes": 0,
             "error": "Repository disk full", "_mock": True},
        ]
        return {"success": True, "jobs": jobs, "count": len(jobs), "_mock": True}

    async def get_job_detail(self, job_id: str) -> dict:
        return {"success": True, "job": {"id": job_id, "name": f"Job {job_id}",
                "status": "Success", "_mock": True}}

    async def get_sessions(self) -> dict:
        sessions = [
            {"id": f"sess-{i:03d}", "jobId": f"job-{(i % 5) + 1:03d}",
             "jobName": ["Daily Backup - File Servers", "SQL Server Backup",
                         "Replication to DR", "Exchange Backup", "Dev/Test Restore"][i % 5],
             "status": ["Success", "Success", "Success", "Warning", "Failed"][i % 5],
             "result": ["Success", "Success", "Success", "Warning", "Failed"][i % 5],
             "startTime": _ts(i * 2), "endTime": _ts(i * 2 - 1),
             "progressPercent": 100, "_mock": True}
            for i in range(10)
        ]
        return {"success": True, "sessions": sessions, "count": len(sessions), "_mock": True}

    async def get_repositories(self) -> dict:
        repos = [
            {"id": "repo-001", "name": "Primary Repository",
             "path": "\\\\veeam-repo01\\backup",
             "capacityBytes": 2_000_000_000_000, "usedSpaceBytes": 900_000_000_000,
             "freeSpaceBytes": 1_100_000_000_000, "status": "Available",
             "type": "Windows local", "_mock": True},
            {"id": "repo-002", "name": "Secondary Repository",
             "path": "\\\\veeam-repo02\\backup",
             "capacityBytes": 3_000_000_000_000, "usedSpaceBytes": 1_200_000_000_000,
             "freeSpaceBytes": 1_800_000_000_000, "status": "Available",
             "type": "Linux local", "_mock": True},
            {"id": "repo-003", "name": "Capacity Tier (S3)",
             "path": "s3://veeam-capacity-tier",
             "capacityBytes": 10_000_000_000_000, "usedSpaceBytes": 0,
             "freeSpaceBytes": 10_000_000_000_000, "status": "Available",
             "type": "S3 object storage", "_mock": True},
        ]
        return {"success": True, "repositories": repos, "count": len(repos), "_mock": True}

    async def get_managed_servers(self) -> dict:
        servers = [
            {"id": "srv-001", "name": "HYPERV-NODE01", "type": "Hyper-V",
             "osVersion": "Windows Server 2022", "status": "Connected",
             "agentVersion": "12.3.1.1139", "_mock": True},
            {"id": "srv-002", "name": "HYPERV-NODE02", "type": "Hyper-V",
             "osVersion": "Windows Server 2022", "status": "Connected",
             "agentVersion": "12.3.1.1139", "_mock": True},
            {"id": "srv-003", "name": "ESXI-PROD01", "type": "VMware",
             "osVersion": "ESXi 8.0 Update 2", "status": "Connected",
             "agentVersion": "", "_mock": True},
            {"id": "srv-004", "name": "PROXMOX-NODE01", "type": "Linux",
             "osVersion": "Ubuntu 24.04", "status": "Connected",
             "agentVersion": "", "_mock": True},
        ]
        return {"success": True, "servers": servers, "count": len(servers), "_mock": True}

    async def get_restore_points(self, vm_id: str | None = None) -> dict:
        points = [
            {"id": f"rp-{i:03d}", "vmId": f"vm-{(i % 3) + 1:03d}",
             "vmName": ["SQL-PROD01", "WEB-PROD01", "DC-PRIMARY"][i % 3],
             "type": ["Full", "Incremental", "Incremental"][i % 3],
             "creationTime": _ts(i * 24), "sizeBytes": 50_000_000_000,
             "pointType": "RestorePoint", "_mock": True}
            for i in range(12)
        ]
        if vm_id:
            points = [p for p in points if p["vmId"] == vm_id]
        return {"success": True, "restore_points": points, "count": len(points), "_mock": True}

    async def get_license(self) -> dict:
        return {
            "success": True,
            "license": {
                "status": "Licensed",
                "type": "Enterprise Plus",
                "expirationDate": "2027-12-31T23:59:59Z",
                "socketCount": 16,
                "usedSockets": 12,
                "instanceCount": 0,
                "usedInstances": 0,
                "_mock": True,
            },
        }

    async def get_capacity_tier(self) -> dict:
        return {
            "success": True,
            "object_storages": [
                {"id": "cap-001", "name": "AWS S3 Capacity Tier",
                 "type": "S3", "bucket": "veeam-capacity-backups",
                 "region": "eu-west-1", "usedBytes": 500_000_000_000,
                 "status": "Connected", "_mock": True},
                {"id": "cap-002", "name": "Azure Blob Archive",
                 "type": "AzureBlob", "container": "veeam-archive",
                 "usedBytes": 1_000_000_000_000,
                 "status": "Connected", "_mock": True},
            ],
            "count": 2,
            "_mock": True,
        }

    async def start_job(self, job_id: str) -> dict:
        return {"success": True, "message": f"Job {job_id} started (mock)", "_mock": True}

    async def stop_job(self, job_id: str) -> dict:
        return {"success": True, "message": f"Job {job_id} stopped (mock)", "_mock": True}

    async def get_health(self) -> dict:
        return {
            "healthy": True,
            "version": "12.3.1.1139",
            "name": "VEEAM-SRV01",
            "_mock": True,
        }

    async def get_session_stats(self) -> dict:
        return {
            "success": True,
            "stats": [],
            "ssh_available": False,
            "message": "Mock provider - no SSH bridge",
            "_mock": True,
        }

    async def get_job_stats(self) -> dict:
        return {
            "success": True,
            "jobs": [],
            "ssh_available": False,
            "message": "Mock provider - no SSH bridge",
            "_mock": True,
        }

    async def get_job_stats_daily(self, days: int = 7) -> dict:
        return {
            "success": True,
            "jobs": [],
            "ssh_available": False,
            "message": "Mock provider - no SSH bridge",
            "_mock": True,
        }
