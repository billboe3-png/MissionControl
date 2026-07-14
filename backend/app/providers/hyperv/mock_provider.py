"""
Mission Control Hyper-V Mock Provider

Returns realistic mock data for development and testing.
Supports switchable modes: healthy, degraded, offline, empty.
"""

import logging
import random
from datetime import UTC, datetime, timedelta

from .base_provider import HyperVProvider

logger = logging.getLogger(__name__)

MOCK_MODE = "healthy"


def set_mock_mode(mode: str) -> None:
    global MOCK_MODE
    MOCK_MODE = mode


def _now() -> datetime:
    return datetime.now(UTC)


MOCK_VMS = [
    {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "name": "DC01",
        "state": "running",
        "cpu_count": 4,
        "memory_assigned_mb": 8192,
        "memory_startup_mb": 8192,
        "memory_demand_mb": 6144,
        "uptime_seconds": 2592000,
        "host_server": "HV-HOST01",
        "guest_os": "Windows Server 2022 Datacenter",
        "creation_time": (_now() - timedelta(days=730)).isoformat(),
        "last_checkpoint": (_now() - timedelta(days=7)).isoformat(),
        "status_message": "All integration services operational",
        "integration_services_enabled": True,
        "cpu_usage_percent": 23.4,
        "disk_read_mbps": 45.2,
        "disk_write_mbps": 12.8,
        "network_receive_mbps": 8.3,
        "network_send_mbps": 2.1,
    },
    {
        "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
        "name": "WEB01",
        "state": "running",
        "cpu_count": 8,
        "memory_assigned_mb": 16384,
        "memory_startup_mb": 16384,
        "memory_demand_mb": 12288,
        "uptime_seconds": 1296000,
        "host_server": "HV-HOST01",
        "guest_os": "Windows Server 2022 Standard",
        "creation_time": (_now() - timedelta(days=365)).isoformat(),
        "last_checkpoint": (_now() - timedelta(days=3)).isoformat(),
        "status_message": "All integration services operational",
        "integration_services_enabled": True,
        "cpu_usage_percent": 67.1,
        "disk_read_mbps": 120.5,
        "disk_write_mbps": 85.3,
        "network_receive_mbps": 45.6,
        "network_send_mbps": 38.2,
    },
    {
        "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
        "name": "DB01",
        "state": "running",
        "cpu_count": 16,
        "memory_assigned_mb": 32768,
        "memory_startup_mb": 32768,
        "memory_demand_mb": 28672,
        "uptime_seconds": 5184000,
        "host_server": "HV-HOST02",
        "guest_os": "Windows Server 2022 Datacenter",
        "creation_time": (_now() - timedelta(days=1095)).isoformat(),
        "last_checkpoint": (_now() - timedelta(days=1)).isoformat(),
        "status_message": "All integration services operational",
        "integration_services_enabled": True,
        "cpu_usage_percent": 42.8,
        "disk_read_mbps": 256.1,
        "disk_write_mbps": 198.4,
        "network_receive_mbps": 15.2,
        "network_send_mbps": 8.7,
    },
    {
        "id": "d4e5f6a7-b8c9-0123-defa-234567890123",
        "name": "APP01",
        "state": "stopped",
        "cpu_count": 4,
        "memory_assigned_mb": 0,
        "memory_startup_mb": 8192,
        "memory_demand_mb": 0,
        "uptime_seconds": 0,
        "host_server": "HV-HOST01",
        "guest_os": "Ubuntu 22.04 LTS",
        "creation_time": (_now() - timedelta(days=180)).isoformat(),
        "last_checkpoint": (_now() - timedelta(days=30)).isoformat(),
        "status_message": "VM is stopped",
        "integration_services_enabled": False,
        "cpu_usage_percent": 0.0,
        "disk_read_mbps": 0.0,
        "disk_write_mbps": 0.0,
        "network_receive_mbps": 0.0,
        "network_send_mbps": 0.0,
    },
    {
        "id": "e5f6a7b8-c9d0-1234-efab-345678901234",
        "name": "TEST01",
        "state": "paused",
        "cpu_count": 2,
        "memory_assigned_mb": 4096,
        "memory_startup_mb": 4096,
        "memory_demand_mb": 0,
        "uptime_seconds": 0,
        "host_server": "HV-HOST02",
        "guest_os": "Windows 11 Enterprise",
        "creation_time": (_now() - timedelta(days=60)).isoformat(),
        "last_checkpoint": None,
        "status_message": "VM is paused",
        "integration_services_enabled": True,
        "cpu_usage_percent": 0.0,
        "disk_read_mbps": 0.0,
        "disk_write_mbps": 0.0,
        "network_receive_mbps": 0.0,
        "network_send_mbps": 0.0,
    },
    {
        "id": "f6a7b8c9-d0e1-2345-fabc-456789012345",
        "name": "FILE01",
        "state": "running",
        "cpu_count": 4,
        "memory_assigned_mb": 8192,
        "memory_startup_mb": 8192,
        "memory_demand_mb": 5120,
        "uptime_seconds": 7776000,
        "host_server": "HV-HOST02",
        "guest_os": "Windows Server 2022 Standard",
        "creation_time": (_now() - timedelta(days=540)).isoformat(),
        "last_checkpoint": (_now() - timedelta(days=14)).isoformat(),
        "status_message": "All integration services operational",
        "integration_services_enabled": True,
        "cpu_usage_percent": 8.2,
        "disk_read_mbps": 32.1,
        "disk_write_mbps": 28.5,
        "network_receive_mbps": 22.4,
        "network_send_mbps": 18.9,
    },
]

MOCK_NETWORKS = [
    {
        "id": "net-001",
        "name": "External Switch",
        "switch_type": "external",
        "vlan_id": None,
        "mac_address_spoofing": True,
        "allow_management_os": True,
        "status": "operational",
        "connected_vms": 4,
        "net_adapter": "Intel I219-LM",
    },
    {
        "id": "net-002",
        "name": "Internal Switch",
        "switch_type": "internal",
        "vlan_id": 100,
        "mac_address_spoofing": False,
        "allow_management_os": True,
        "status": "operational",
        "connected_vms": 2,
        "net_adapter": None,
    },
    {
        "id": "net-003",
        "name": "Management Network",
        "switch_type": "external",
        "vlan_id": 10,
        "mac_address_spoofing": True,
        "allow_management_os": True,
        "status": "operational",
        "connected_vms": 6,
        "net_adapter": "Broadcom NetXtreme",
    },
    {
        "id": "net-004",
        "name": "Isolated Lab",
        "switch_type": "private",
        "vlan_id": None,
        "mac_address_spoofing": False,
        "allow_management_os": False,
        "status": "operational",
        "connected_vms": 1,
        "net_adapter": None,
    },
]

MOCK_STORAGE = [
    {
        "id": "disk-001",
        "name": "DC01-System.vhdx",
        "path": "C:\\Hyper-V\\Virtual Hard Disks\\DC01-System.vhdx",
        "size_bytes": 128849018880,
        "used_bytes": 42949672960,
        "type": "vhdx",
        "vm_name": "DC01",
        "attached": True,
        "format": "dynamic",
    },
    {
        "id": "disk-002",
        "name": "DC01-Data.vhdx",
        "path": "C:\\Hyper-V\\Virtual Hard Disks\\DC01-Data.vhdx",
        "size_bytes": 536870912000,
        "used_bytes": 214748364800,
        "type": "vhdx",
        "vm_name": "DC01",
        "attached": True,
        "format": "dynamic",
    },
    {
        "id": "disk-003",
        "name": "WEB01-System.vhdx",
        "path": "D:\\Hyper-V\\Virtual Hard Disks\\WEB01-System.vhdx",
        "size_bytes": 128849018880,
        "used_bytes": 64424509440,
        "type": "vhdx",
        "vm_name": "WEB01",
        "attached": True,
        "format": "dynamic",
    },
    {
        "id": "disk-004",
        "name": "DB01-System.vhdx",
        "path": "E:\\Hyper-V\\Virtual Hard Disks\\DB01-System.vhdx",
        "size_bytes": 214748364800,
        "used_bytes": 107374182400,
        "type": "vhdx",
        "vm_name": "DB01",
        "attached": True,
        "format": "fixed",
    },
    {
        "id": "disk-005",
        "name": "DB01-Data.vhdx",
        "path": "E:\\Hyper-V\\Virtual Hard Disks\\DB01-Data.vhdx",
        "size_bytes": 1099511627776,
        "used_bytes": 659706976665,
        "type": "vhdx",
        "vm_name": "DB01",
        "attached": True,
        "format": "fixed",
    },
    {
        "id": "disk-006",
        "name": "DB01-Logs.vhdx",
        "path": "E:\\Hyper-V\\Virtual Hard Disks\\DB01-Logs.vhdx",
        "size_bytes": 107374182400,
        "used_bytes": 21474836480,
        "type": "vhdx",
        "vm_name": "DB01",
        "attached": True,
        "format": "fixed",
    },
    {
        "id": "disk-007",
        "name": "APP01-System.vhdx",
        "path": "D:\\Hyper-V\\Virtual Hard Disks\\APP01-System.vhdx",
        "size_bytes": 64424509440,
        "used_bytes": 21474836480,
        "type": "vhdx",
        "vm_name": "APP01",
        "attached": True,
        "format": "dynamic",
    },
    {
        "id": "disk-008",
        "name": "FILE01-System.vhdx",
        "path": "E:\\Hyper-V\\Virtual Hard Disks\\FILE01-System.vhdx",
        "size_bytes": 128849018880,
        "used_bytes": 85899345920,
        "type": "vhdx",
        "vm_name": "FILE01",
        "attached": True,
        "format": "dynamic",
    },
    {
        "id": "disk-009",
        "name": "FILE01-Data.vhdx",
        "path": "E:\\Hyper-V\\Virtual Hard Disks\\FILE01-Data.vhdx",
        "size_bytes": 2199023255552,
        "used_bytes": 1099511627776,
        "type": "vhdx",
        "vm_name": "FILE01",
        "attached": True,
        "format": "fixed",
    },
]

MOCK_CHECKPOINTS = [
    {
        "id": "cp-001",
        "name": "DC01 - Before Patch Tuesday",
        "vm_name": "DC01",
        "vm_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "checkpoint_type": "production",
        "creation_time": (_now() - timedelta(days=7)).isoformat(),
        "size_bytes": 2147483648,
        "parent_checkpoint_id": None,
        "notes": "Pre-July 2026 patch snapshot",
    },
    {
        "id": "cp-002",
        "name": "DC01 - After Patch Tuesday",
        "vm_name": "DC01",
        "vm_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "checkpoint_type": "production",
        "creation_time": (_now() - timedelta(days=5)).isoformat(),
        "size_bytes": 1073741824,
        "parent_checkpoint_id": "cp-001",
        "notes": "Post-patch validation checkpoint",
    },
    {
        "id": "cp-003",
        "name": "WEB01 - Pre-deploy v2.4",
        "vm_name": "WEB01",
        "vm_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
        "checkpoint_type": "standard",
        "creation_time": (_now() - timedelta(days=3)).isoformat(),
        "size_bytes": 4294967296,
        "parent_checkpoint_id": None,
        "notes": "Before deploying application v2.4",
    },
    {
        "id": "cp-004",
        "name": "DB01 - Nightly Backup",
        "vm_name": "DB01",
        "vm_id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
        "checkpoint_type": "production",
        "creation_time": (_now() - timedelta(hours=8)).isoformat(),
        "size_bytes": 8589934592,
        "parent_checkpoint_id": None,
        "notes": "Automated nightly production checkpoint",
    },
    {
        "id": "cp-005",
        "name": "FILE01 - Monthly",
        "vm_name": "FILE01",
        "vm_id": "f6a7b8c9-d0e1-2345-fabc-456789012345",
        "checkpoint_type": "production",
        "creation_time": (_now() - timedelta(days=14)).isoformat(),
        "size_bytes": 16106127360,
        "parent_checkpoint_id": None,
        "notes": "Monthly file server checkpoint",
    },
]


class MockHyperVProvider(HyperVProvider):
    """Mock Hyper-V provider returning realistic static data."""

    async def test_connection(self) -> dict:
        if MOCK_MODE == "offline":
            return {
                "connected": False,
                "error": "Connection refused: Hyper-V host unreachable",
                "latency_ms": 0,
            }
        if MOCK_MODE == "auth_failure":
            return {
                "connected": False,
                "error": "Access denied: Invalid credentials for Hyper-V host",
                "latency_ms": 0,
            }
        return {
            "connected": True,
            "latency_ms": random.randint(5, 25),
            "message": "Connected to Hyper-V host (mock)",
            "version": "10.0.20348",
            "hostname": "HV-HOST01",
        }

    async def get_summary(self) -> dict:
        if MOCK_MODE == "offline":
            return {"connected": False, "error": "Host unreachable", "total_vms": 0, "running": 0, "stopped": 0, "paused": 0, "total_cpu": 0, "total_memory_gb": 0, "used_memory_gb": 0, "total_storage_gb": 0, "used_storage_gb": 0}

        vms = MOCK_VMS
        running = sum(1 for v in vms if v["state"] == "running")
        stopped = sum(1 for v in vms if v["state"] == "stopped")
        paused = sum(1 for v in vms if v["state"] == "paused")
        saved = sum(1 for v in vms if v["state"] == "saved")
        total_cpu = sum(v["cpu_count"] for v in vms)
        total_mem = sum(v["memory_assigned_mb"] for v in vms)
        used_mem = sum(v["memory_demand_mb"] for v in vms)
        total_storage = sum(s["size_bytes"] for s in MOCK_STORAGE)
        used_storage = sum(s["used_bytes"] for s in MOCK_STORAGE)

        return {
            "connected": True,
            "hostname": "HV-HOST01",
            "version": "10.0.20348",
            "total_vms": len(vms),
            "running": running,
            "stopped": stopped,
            "paused": paused,
            "saved": saved,
            "total_cpu": total_cpu,
            "total_memory_gb": round(total_mem / 1024, 1),
            "used_memory_gb": round(used_mem / 1024, 1),
            "total_storage_gb": round(total_storage / (1024 ** 3), 1),
            "used_storage_gb": round(used_storage / (1024 ** 3), 1),
            "host_servers": ["HV-HOST01", "HV-HOST02"],
            "network_switches": len(MOCK_NETWORKS),
            "total_checkpoints": len(MOCK_CHECKPOINTS),
        }

    async def get_vms(self) -> dict:
        if MOCK_MODE == "offline":
            return {"connected": False, "error": "Host unreachable", "count": 0, "items": []}
        if MOCK_MODE == "empty":
            return {"connected": True, "count": 0, "items": []}
        return {"connected": True, "count": len(MOCK_VMS), "items": MOCK_VMS}

    async def get_vm_detail(self, vm_id: str) -> dict:
        if MOCK_MODE == "offline":
            return {"connected": False, "error": "Host unreachable"}
        for vm in MOCK_VMS:
            if vm["id"] == vm_id:
                return {"connected": True, "item": vm}
        return {"connected": False, "error": f"VM not found: {vm_id}"}

    async def start_vm(self, vm_id: str) -> dict:
        if MOCK_MODE == "offline":
            return {"connected": False, "error": "Host unreachable"}
        for vm in MOCK_VMS:
            if vm["id"] == vm_id:
                if vm["state"] == "running":
                    return {"success": False, "error": "VM is already running", "vm_name": vm["name"]}
                return {"success": True, "message": f"VM '{vm['name']}' started", "vm_name": vm["name"]}
        return {"success": False, "error": f"VM not found: {vm_id}"}

    async def stop_vm(self, vm_id: str, force: bool = False) -> dict:
        if MOCK_MODE == "offline":
            return {"connected": False, "error": "Host unreachable"}
        for vm in MOCK_VMS:
            if vm["id"] == vm_id:
                if vm["state"] == "stopped":
                    return {"success": False, "error": "VM is already stopped", "vm_name": vm["name"]}
                action = "force stopped" if force else "stopped"
                return {"success": True, "message": f"VM '{vm['name']}' {action}", "vm_name": vm["name"]}
        return {"success": False, "error": f"VM not found: {vm_id}"}

    async def restart_vm(self, vm_id: str) -> dict:
        if MOCK_MODE == "offline":
            return {"connected": False, "error": "Host unreachable"}
        for vm in MOCK_VMS:
            if vm["id"] == vm_id:
                if vm["state"] != "running":
                    return {"success": False, "error": "VM must be running to restart", "vm_name": vm["name"]}
                return {"success": True, "message": f"VM '{vm['name']}' restarting", "vm_name": vm["name"]}
        return {"success": False, "error": f"VM not found: {vm_id}"}

    async def pause_vm(self, vm_id: str) -> dict:
        if MOCK_MODE == "offline":
            return {"connected": False, "error": "Host unreachable"}
        for vm in MOCK_VMS:
            if vm["id"] == vm_id:
                if vm["state"] != "running":
                    return {"success": False, "error": "VM must be running to pause", "vm_name": vm["name"]}
                return {"success": True, "message": f"VM '{vm['name']}' paused", "vm_name": vm["name"]}
        return {"success": False, "error": f"VM not found: {vm_id}"}

    async def resume_vm(self, vm_id: str) -> dict:
        if MOCK_MODE == "offline":
            return {"connected": False, "error": "Host unreachable"}
        for vm in MOCK_VMS:
            if vm["id"] == vm_id:
                if vm["state"] != "paused":
                    return {"success": False, "error": "VM is not paused", "vm_name": vm["name"]}
                return {"success": True, "message": f"VM '{vm['name']}' resumed", "vm_name": vm["name"]}
        return {"success": False, "error": f"VM not found: {vm_id}"}

    async def get_networks(self) -> dict:
        if MOCK_MODE == "offline":
            return {"connected": False, "error": "Host unreachable", "count": 0, "items": []}
        if MOCK_MODE == "empty":
            return {"connected": True, "count": 0, "items": []}
        return {"connected": True, "count": len(MOCK_NETWORKS), "items": MOCK_NETWORKS}

    async def get_storage(self) -> dict:
        if MOCK_MODE == "offline":
            return {"connected": False, "error": "Host unreachable", "count": 0, "items": []}
        if MOCK_MODE == "empty":
            return {"connected": True, "count": 0, "items": []}
        return {"connected": True, "count": len(MOCK_STORAGE), "items": MOCK_STORAGE}

    async def get_checkpoints(self, vm_id: str | None = None) -> dict:
        if MOCK_MODE == "offline":
            return {"connected": False, "error": "Host unreachable", "count": 0, "items": []}
        items = MOCK_CHECKPOINTS
        if vm_id:
            items = [c for c in items if c["vm_id"] == vm_id]
        return {"connected": True, "count": len(items), "items": items}

    async def create_checkpoint(self, vm_id: str, name: str | None = None) -> dict:
        if MOCK_MODE == "offline":
            return {"connected": False, "error": "Host unreachable"}
        for vm in MOCK_VMS:
            if vm["id"] == vm_id:
                cp_name = name or f"{vm['name']} - {_now().strftime('%Y-%m-%d %H:%M')}"
                return {
                    "success": True,
                    "message": f"Checkpoint '{cp_name}' created",
                    "checkpoint": {
                        "id": f"cp-{random.randint(100,999)}",
                        "name": cp_name,
                        "vm_name": vm["name"],
                        "vm_id": vm_id,
                        "checkpoint_type": "production",
                        "creation_time": _now().isoformat(),
                        "size_bytes": 0,
                        "parent_checkpoint_id": None,
                        "notes": "",
                    },
                }
        return {"success": False, "error": f"VM not found: {vm_id}"}

    async def delete_checkpoint(self, vm_id: str, checkpoint_id: str) -> dict:
        if MOCK_MODE == "offline":
            return {"connected": False, "error": "Host unreachable"}
        for cp in MOCK_CHECKPOINTS:
            if cp["id"] == checkpoint_id:
                return {"success": True, "message": f"Checkpoint '{cp['name']}' deleted"}
        return {"success": False, "error": f"Checkpoint not found: {checkpoint_id}"}

    async def get_snapshots(self, vm_id: str | None = None) -> dict:
        return await self.get_checkpoints(vm_id)

    async def create_snapshot(self, vm_id: str, name: str | None = None) -> dict:
        return await self.create_checkpoint(vm_id, name)

    async def delete_snapshot(self, vm_id: str, snapshot_id: str) -> dict:
        return await self.delete_checkpoint(vm_id, snapshot_id)

    async def get_health(self) -> dict:
        if MOCK_MODE == "offline":
            return {"connected": False, "error": "Host unreachable", "status": "unavailable"}
        hosts = [
            {
                "name": "HV-HOST01",
                "status": "healthy",
                "cpu_percent": 34.2,
                "memory_percent": 62.1,
                "uptime_seconds": 2592000,
                "vm_count": 3,
                "version": "10.0.20348",
            },
            {
                "name": "HV-HOST02",
                "status": "healthy" if MOCK_MODE == "healthy" else "warning",
                "cpu_percent": 55.8 if MOCK_MODE == "healthy" else 89.3,
                "memory_percent": 78.4 if MOCK_MODE == "healthy" else 92.1,
                "uptime_seconds": 1296000,
                "vm_count": 3,
                "version": "10.0.20348",
            },
        ]
        overall = "healthy" if MOCK_MODE == "healthy" else "warning"
        return {
            "connected": True,
            "status": overall,
            "hosts": hosts,
            "cluster_summary": "All nodes operational" if MOCK_MODE == "healthy" else "HV-HOST02 memory pressure",
        }
