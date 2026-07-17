"""
Mission Control Proxmox Mock Provider

Returns realistic static data for development and testing.
"""

import random
from datetime import UTC, datetime, timedelta

from .base_provider import ProxmoxProvider

MOCK_MODE = "healthy"


def set_mock_mode(mode: str) -> None:
    global MOCK_MODE
    MOCK_MODE = mode


def _now() -> datetime:
    return datetime.now(UTC)


MOCK_NODES = [
    {
        "name": "pve-node01",
        "status": "online",
        "cpu_percent": 34.2,
        "memory_total_mb": 131072,
        "memory_used_mb": 82641,
        "disk_total_gb": 1843,
        "disk_used_gb": 736,
        "uptime_seconds": 2592000,
        "version": "8.2.4",
        "ssl_fingerprint": "AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99",
    },
    {
        "name": "pve-node02",
        "status": "online",
        "cpu_percent": 55.8,
        "memory_total_mb": 131072,
        "memory_used_mb": 104857,
        "disk_total_gb": 1843,
        "disk_used_gb": 1097,
        "uptime_seconds": 1296000,
        "version": "8.2.4",
        "ssl_fingerprint": "AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:00",
    },
]

MOCK_VMS = [
    {
        "id": "100",
        "name": "web-prod-01",
        "state": "running",
        "cpu_count": 4,
        "memory_assigned_mb": 8192,
        "memory_startup_mb": 8192,
        "memory_demand_mb": 6144,
        "uptime_seconds": 2592000,
        "host_server": "pve-node01",
        "guest_os": "Ubuntu 24.04 LTS",
        "creation_time": (_now() - timedelta(days=90)).isoformat(),
        "cpu_usage_percent": 23.5,
        "disk_read_mbps": 45.2,
        "disk_write_mbps": 12.8,
        "network_receive_mbps": 89.1,
        "network_send_mbps": 34.6,
        "status_message": "",
        "integration_services_enabled": True,
        "last_checkpoint": (_now() - timedelta(hours=6)).isoformat(),
    },
    {
        "id": "101",
        "name": "web-prod-02",
        "state": "running",
        "cpu_count": 4,
        "memory_assigned_mb": 8192,
        "memory_startup_mb": 8192,
        "memory_demand_mb": 5632,
        "uptime_seconds": 2592000,
        "host_server": "pve-node01",
        "guest_os": "Ubuntu 24.04 LTS",
        "creation_time": (_now() - timedelta(days=90)).isoformat(),
        "cpu_usage_percent": 18.7,
        "disk_read_mbps": 32.1,
        "disk_write_mbps": 8.4,
        "network_receive_mbps": 76.3,
        "network_send_mbps": 28.9,
        "status_message": "",
        "integration_services_enabled": True,
        "last_checkpoint": (_now() - timedelta(hours=6)).isoformat(),
    },
    {
        "id": "102",
        "name": "db-prod-01",
        "state": "running",
        "cpu_count": 8,
        "memory_assigned_mb": 32768,
        "memory_startup_mb": 32768,
        "memory_demand_mb": 28672,
        "uptime_seconds": 2592000,
        "host_server": "pve-node01",
        "guest_os": "Debian 12",
        "creation_time": (_now() - timedelta(days=180)).isoformat(),
        "cpu_usage_percent": 42.1,
        "disk_read_mbps": 128.4,
        "disk_write_mbps": 96.7,
        "network_receive_mbps": 15.2,
        "network_send_mbps": 8.1,
        "status_message": "",
        "integration_services_enabled": True,
        "last_checkpoint": (_now() - timedelta(hours=12)).isoformat(),
    },
    {
        "id": "103",
        "name": "app-staging-01",
        "state": "stopped",
        "cpu_count": 2,
        "memory_assigned_mb": 4096,
        "memory_startup_mb": 4096,
        "memory_demand_mb": 0,
        "uptime_seconds": 0,
        "host_server": "pve-node02",
        "guest_os": "Ubuntu 22.04 LTS",
        "creation_time": (_now() - timedelta(days=45)).isoformat(),
        "cpu_usage_percent": 0.0,
        "disk_read_mbps": 0.0,
        "disk_write_mbps": 0.0,
        "network_receive_mbps": 0.0,
        "network_send_mbps": 0.0,
        "status_message": "",
        "integration_services_enabled": True,
        "last_checkpoint": None,
    },
    {
        "id": "104",
        "name": "monitoring-01",
        "state": "running",
        "cpu_count": 4,
        "memory_assigned_mb": 16384,
        "memory_startup_mb": 16384,
        "memory_demand_mb": 12288,
        "uptime_seconds": 864000,
        "host_server": "pve-node02",
        "guest_os": "Debian 12",
        "creation_time": (_now() - timedelta(days=60)).isoformat(),
        "cpu_usage_percent": 15.3,
        "disk_read_mbps": 22.1,
        "disk_write_mbps": 5.6,
        "network_receive_mbps": 45.8,
        "network_send_mbps": 12.3,
        "status_message": "",
        "integration_services_enabled": True,
        "last_checkpoint": (_now() - timedelta(days=2)).isoformat(),
    },
    {
        "id": "105",
        "name": "dev-sandbox-01",
        "state": "paused",
        "cpu_count": 2,
        "memory_assigned_mb": 4096,
        "memory_startup_mb": 4096,
        "memory_demand_mb": 2048,
        "uptime_seconds": 432000,
        "host_server": "pve-node02",
        "guest_os": "Ubuntu 24.04 LTS",
        "creation_time": (_now() - timedelta(days=30)).isoformat(),
        "cpu_usage_percent": 0.0,
        "disk_read_mbps": 0.0,
        "disk_write_mbps": 0.0,
        "network_receive_mbps": 0.0,
        "network_send_mbps": 0.0,
        "status_message": "",
        "integration_services_enabled": True,
        "last_checkpoint": None,
    },
]

MOCK_LXC = [
    {
        "id": "200",
        "name": "dns-resolver",
        "state": "running",
        "cpu_count": 2,
        "memory_assigned_mb": 1024,
        "memory_startup_mb": 1024,
        "memory_demand_mb": 512,
        "uptime_seconds": 2592000,
        "host_server": "pve-node01",
        "guest_os": "Debian 12",
        "creation_time": (_now() - timedelta(days=120)).isoformat(),
        "cpu_usage_percent": 2.1,
        "status_message": "",
        "disk_read_mbps": 0.5,
        "disk_write_mbps": 0.2,
        "network_receive_mbps": 12.4,
        "network_send_mbps": 11.8,
    },
    {
        "id": "201",
        "name": "log-aggregator",
        "state": "running",
        "cpu_count": 4,
        "memory_assigned_mb": 4096,
        "memory_startup_mb": 4096,
        "memory_demand_mb": 3072,
        "uptime_seconds": 2592000,
        "host_server": "pve-node01",
        "guest_os": "Ubuntu 22.04 LTS",
        "creation_time": (_now() - timedelta(days=90)).isoformat(),
        "cpu_usage_percent": 8.5,
        "status_message": "",
        "disk_read_mbps": 15.3,
        "disk_write_mbps": 8.7,
        "network_receive_mbps": 45.2,
        "network_send_mbps": 2.1,
    },
    {
        "id": "202",
        "name": "ci-runner-01",
        "state": "stopped",
        "cpu_count": 4,
        "memory_assigned_mb": 8192,
        "memory_startup_mb": 8192,
        "memory_demand_mb": 0,
        "uptime_seconds": 0,
        "host_server": "pve-node02",
        "guest_os": "Ubuntu 24.04 LTS",
        "creation_time": (_now() - timedelta(days=30)).isoformat(),
        "cpu_usage_percent": 0.0,
        "status_message": "",
        "disk_read_mbps": 0.0,
        "disk_write_mbps": 0.0,
        "network_receive_mbps": 0.0,
        "network_send_mbps": 0.0,
    },
    {
        "id": "203",
        "name": "backup-proxy",
        "state": "running",
        "cpu_count": 2,
        "memory_assigned_mb": 2048,
        "memory_startup_mb": 2048,
        "memory_demand_mb": 1024,
        "uptime_seconds": 864000,
        "host_server": "pve-node02",
        "guest_os": "Debian 12",
        "creation_time": (_now() - timedelta(days=60)).isoformat(),
        "cpu_usage_percent": 4.2,
        "status_message": "",
        "disk_read_mbps": 32.1,
        "disk_write_mbps": 45.6,
        "network_receive_mbps": 5.2,
        "network_send_mbps": 28.4,
    },
]

MOCK_STORAGE = [
    {
        "id": "local-lvm",
        "name": "local-lvm",
        "path": "/dev/pve/data",
        "size_bytes": 989855485952,
        "used_bytes": 494927742976,
        "type": "lvm",
        "status": "available",
        "content": "images,rootdir",
        "node": "pve-node01",
    },
    {
        "id": "local",
        "name": "local",
        "path": "/var/lib/vz",
        "size_bytes": 107374182400,
        "used_bytes": 32212254720,
        "type": "dir",
        "status": "available",
        "content": "iso,vztmpl,backup",
        "node": "pve-node01",
    },
    {
        "id": "ceph-ssd",
        "name": "ceph-ssd",
        "path": "/dev/rbd0",
        "size_bytes": 2199023255552,
        "used_bytes": 879609302221,
        "type": "rbd",
        "status": "available",
        "content": "images,rootdir",
        "node": "pve-node01",
    },
    {
        "id": "local-lvm-02",
        "name": "local-lvm",
        "path": "/dev/pve/data",
        "size_bytes": 989855485952,
        "used_bytes": 692898840166,
        "type": "lvm",
        "status": "available",
        "content": "images,rootdir",
        "node": "pve-node02",
    },
    {
        "id": "local-02",
        "name": "local",
        "path": "/var/lib/vz",
        "size_bytes": 107374182400,
        "used_bytes": 21474836480,
        "type": "dir",
        "status": "available",
        "content": "iso,vztmpl,backup",
        "node": "pve-node02",
    },
    {
        "id": "ceph-ssd-02",
        "name": "ceph-ssd",
        "path": "/dev/rbd0",
        "size_bytes": 2199023255552,
        "used_bytes": 1099511627776,
        "type": "rbd",
        "status": "available",
        "content": "images,rootdir",
        "node": "pve-node02",
    },
]

MOCK_NETWORKS = [
    {
        "id": "vmbr0",
        "name": "vmbr0",
        "switch_type": "bridge",
        "vlan_id": None,
        "status": "operational",
        "node": "pve-node01",
        "cidr": "10.0.0.0/24",
        "address": "10.0.0.10",
        "gateway": "10.0.0.1",
        "connected_vms": 4,
        "type": "bridge",
    },
    {
        "id": "vmbr1",
        "name": "vmbr1",
        "switch_type": "bridge",
        "vlan_id": 100,
        "status": "operational",
        "node": "pve-node01",
        "cidr": "10.0.100.0/24",
        "address": "10.0.100.1",
        "gateway": None,
        "connected_vms": 2,
        "type": "bridge",
    },
    {
        "id": "vmbr0-02",
        "name": "vmbr0",
        "switch_type": "bridge",
        "vlan_id": None,
        "status": "operational",
        "node": "pve-node02",
        "cidr": "10.0.0.0/24",
        "address": "10.0.0.11",
        "gateway": "10.0.0.1",
        "connected_vms": 3,
        "type": "bridge",
    },
    {
        "id": "vmbr2",
        "name": "vmbr2",
        "switch_type": "bond",
        "vlan_id": None,
        "status": "operational",
        "node": "pve-node02",
        "cidr": "10.0.200.0/24",
        "address": "10.0.200.1",
        "gateway": None,
        "connected_vms": 1,
        "type": "bond",
    },
]

MOCK_TASKS = [
    {
        "id": "UPID:pve-node01::00000001::vzdump::root@pam",
        "node": "pve-node01",
        "type": "vzdump",
        "user": "root@pam",
        "status": "ok",
        "start_time": (_now() - timedelta(hours=2)).isoformat(),
        "end_time": (_now() - timedelta(hours=1, minutes=50)).isoformat(),
        "upid": "00000001",
    },
    {
        "id": "UPID:pve-node01::00000002::qmstart::root@pam",
        "node": "pve-node01",
        "type": "qmstart",
        "user": "root@pam",
        "status": "ok",
        "start_time": (_now() - timedelta(hours=6)).isoformat(),
        "end_time": (_now() - timedelta(hours=6) + timedelta(seconds=5)).isoformat(),
        "upid": "00000002",
    },
    {
        "id": "UPID:pve-node02::00000003::vzdump::root@pam",
        "node": "pve-node02",
        "type": "vzdump",
        "user": "root@pam",
        "status": "running",
        "start_time": (_now() - timedelta(minutes=15)).isoformat(),
        "end_time": None,
        "upid": "00000003",
    },
    {
        "id": "UPID:pve-node02::00000004::qmigrate::root@pam",
        "node": "pve-node02",
        "type": "qmigrate",
        "user": "root@pam",
        "status": "ok",
        "start_time": (_now() - timedelta(hours=12)).isoformat(),
        "end_time": (_now() - timedelta(hours=12) + timedelta(minutes=8)).isoformat(),
        "upid": "00000004",
    },
    {
        "id": "UPID:pve-node01::00000005::qmshutdown::root@pam",
        "node": "pve-node01",
        "type": "qmshutdown",
        "user": "root@pam",
        "status": "ok",
        "start_time": (_now() - timedelta(days=1)).isoformat(),
        "end_time": (_now() - timedelta(days=1) + timedelta(seconds=12)).isoformat(),
        "upid": "00000005",
    },
]

MOCK_SNAPSHOTS = [
    {
        "id": "snap-1719000000",
        "name": "pre-upgrade-2.5",
        "vm_name": "web-prod-01",
        "vm_id": "100",
        "checkpoint_type": "snapshot",
        "creation_time": (_now() - timedelta(days=7)).isoformat(),
        "size_bytes": 1073741824,
        "parent_checkpoint_id": None,
        "notes": "Before upgrade to v2.5",
    },
    {
        "id": "snap-1719100000",
        "name": "post-patch-july",
        "vm_name": "web-prod-01",
        "vm_id": "100",
        "checkpoint_type": "snapshot",
        "creation_time": (_now() - timedelta(days=5)).isoformat(),
        "size_bytes": 536870912,
        "parent_checkpoint_id": "snap-1719000000",
        "notes": "After July security patches",
    },
    {
        "id": "snap-1719200000",
        "name": "db-backup-pre-migration",
        "vm_name": "db-prod-01",
        "vm_id": "102",
        "checkpoint_type": "snapshot",
        "creation_time": (_now() - timedelta(days=3)).isoformat(),
        "size_bytes": 2147483648,
        "parent_checkpoint_id": None,
        "notes": "Before DB schema migration",
    },
]


class MockProxmoxProvider(ProxmoxProvider):
    """Mock Proxmox provider returning realistic static data."""

    async def test_connection(self) -> dict:
        if MOCK_MODE == "offline":
            return {
                "connected": False,
                "error": "Connection refused: Proxmox host unreachable",
                "latency_ms": 0,
            }
        if MOCK_MODE == "auth_failure":
            return {
                "connected": False,
                "error": "Authentication failed: Invalid API token or credentials",
                "latency_ms": 0,
            }
        return {
            "connected": True,
            "latency_ms": random.randint(3, 15),
            "message": "Connected to Proxmox VE cluster (mock)",
            "version": "8.2.4",
            "hostname": "pve-cluster01",
        }

    async def get_summary(self) -> dict:
        if MOCK_MODE == "offline":
            return {
                "connected": False,
                "error": "Host unreachable",
                "total_vms": 0,
                "running": 0,
                "stopped": 0,
                "paused": 0,
                "total_cpu": 0,
                "total_memory_gb": 0,
                "used_memory_gb": 0,
                "total_storage_gb": 0,
                "used_storage_gb": 0,
            }

        vms = MOCK_VMS
        lxc = MOCK_LXC
        running_vms = sum(1 for v in vms if v["state"] == "running")
        stopped_vms = sum(1 for v in vms if v["state"] == "stopped")
        paused_vms = sum(1 for v in vms if v["state"] == "paused")
        running_lxc = sum(1 for c in lxc if c["state"] == "running")
        stopped_lxc = sum(1 for c in lxc if c["state"] == "stopped")
        total_cpu = sum(v["cpu_count"] for v in vms) + sum(c["cpu_count"] for c in lxc)
        total_mem = sum(v["memory_assigned_mb"] for v in vms) + sum(c["memory_assigned_mb"] for c in lxc)
        used_mem = sum(v["memory_demand_mb"] for v in vms) + sum(c["memory_demand_mb"] for c in lxc)
        total_storage = sum(s["size_bytes"] for s in MOCK_STORAGE)
        used_storage = sum(s["used_bytes"] for s in MOCK_STORAGE)

        return {
            "connected": True,
            "cluster_name": "pve-cluster01",
            "version": "8.2.4",
            "nodes_online": sum(1 for n in MOCK_NODES if n["status"] == "online"),
            "nodes_total": len(MOCK_NODES),
            "total_vms": len(vms),
            "running": running_vms,
            "stopped": stopped_vms,
            "paused": paused_vms,
            "total_lxc": len(lxc),
            "running_lxc": running_lxc,
            "stopped_lxc": stopped_lxc,
            "total_cpu": total_cpu,
            "total_memory_gb": round(total_mem / 1024, 1),
            "used_memory_gb": round(used_mem / 1024, 1),
            "total_storage_gb": round(total_storage / (1024 ** 3), 1),
            "used_storage_gb": round(used_storage / (1024 ** 3), 1),
            "storage_count": len(MOCK_STORAGE),
            "network_count": len(MOCK_NETWORKS),
            "total_snapshots": len(MOCK_SNAPSHOTS),
        }

    async def get_nodes(self) -> dict:
        if MOCK_MODE == "offline":
            return {"connected": False, "error": "Host unreachable", "count": 0, "items": []}
        return {"connected": True, "count": len(MOCK_NODES), "items": MOCK_NODES}

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

    async def get_lxc_containers(self) -> dict:
        if MOCK_MODE == "offline":
            return {"connected": False, "error": "Host unreachable", "count": 0, "items": []}
        if MOCK_MODE == "empty":
            return {"connected": True, "count": 0, "items": []}
        return {"connected": True, "count": len(MOCK_LXC), "items": MOCK_LXC}

    async def get_lxc_detail(self, vm_id: str) -> dict:
        if MOCK_MODE == "offline":
            return {"connected": False, "error": "Host unreachable"}
        for c in MOCK_LXC:
            if c["id"] == vm_id:
                return {"connected": True, "item": c}
        return {"connected": False, "error": f"LXC container not found: {vm_id}"}

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
                action = "stopped (ACPI)" if not force else "stopped (force)"
                return {"success": True, "message": f"VM '{vm['name']}' {action}", "vm_name": vm["name"]}
        return {"success": False, "error": f"VM not found: {vm_id}"}

    async def restart_vm(self, vm_id: str) -> dict:
        if MOCK_MODE == "offline":
            return {"connected": False, "error": "Host unreachable"}
        for vm in MOCK_VMS:
            if vm["id"] == vm_id:
                if vm["state"] != "running":
                    return {"success": False, "error": "VM must be running to restart", "vm_name": vm["name"]}
                return {"success": True, "message": f"VM '{vm['name']}' rebooting", "vm_name": vm["name"]}
        return {"success": False, "error": f"VM not found: {vm_id}"}

    async def pause_vm(self, vm_id: str) -> dict:
        if MOCK_MODE == "offline":
            return {"connected": False, "error": "Host unreachable"}
        for vm in MOCK_VMS:
            if vm["id"] == vm_id:
                if vm["state"] != "running":
                    return {"success": False, "error": "VM must be running to suspend", "vm_name": vm["name"]}
                return {"success": True, "message": f"VM '{vm['name']}' suspended", "vm_name": vm["name"]}
        return {"success": False, "error": f"VM not found: {vm_id}"}

    async def resume_vm(self, vm_id: str) -> dict:
        if MOCK_MODE == "offline":
            return {"connected": False, "error": "Host unreachable"}
        for vm in MOCK_VMS:
            if vm["id"] == vm_id:
                if vm["state"] != "paused":
                    return {"success": False, "error": "VM is not suspended", "vm_name": vm["name"]}
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

    async def get_snapshots(self, vm_id: str | None = None) -> dict:
        if MOCK_MODE == "offline":
            return {"connected": False, "error": "Host unreachable", "count": 0, "items": []}
        items = MOCK_SNAPSHOTS
        if vm_id:
            items = [s for s in items if s["vm_id"] == vm_id]
        return {"connected": True, "count": len(items), "items": items}

    async def create_snapshot(self, vm_id: str, name: str | None = None) -> dict:
        if MOCK_MODE == "offline":
            return {"connected": False, "error": "Host unreachable"}
        for vm in MOCK_VMS:
            if vm["id"] == vm_id:
                snap_name = name or f"{vm['name']} - {_now().strftime('%Y-%m-%d %H:%M')}"
                return {
                    "success": True,
                    "message": f"Snapshot '{snap_name}' created",
                    "snapshot": {
                        "id": f"snap/{random.randint(1000000,9999999)}",
                        "name": snap_name,
                        "vm_name": vm["name"],
                        "vm_id": vm_id,
                        "checkpoint_type": "snapshot",
                        "creation_time": _now().isoformat(),
                        "size_bytes": 0,
                        "parent_checkpoint_id": None,
                        "notes": "",
                    },
                }
        return {"success": False, "error": f"VM not found: {vm_id}"}

    async def delete_snapshot(self, vm_id: str, snapshot_id: str) -> dict:
        if MOCK_MODE == "offline":
            return {"connected": False, "error": "Host unreachable"}
        for s in MOCK_SNAPSHOTS:
            if s["id"] == snapshot_id:
                return {"success": True, "message": f"Snapshot '{s['name']}' deleted"}
        return {"success": False, "error": f"Snapshot not found: {snapshot_id}"}

    async def get_health(self) -> dict:
        if MOCK_MODE == "offline":
            return {"connected": False, "error": "Host unreachable", "status": "unavailable"}
        nodes = [
            {
                "name": n["name"],
                "status": "healthy" if MOCK_MODE == "healthy" else "warning",
                "cpu_percent": n["cpu_percent"] if MOCK_MODE == "healthy" else 92.5,
                "memory_percent": round(n["memory_used_mb"] / n["memory_total_mb"] * 100, 1),
                "uptime_seconds": n["uptime_seconds"],
                "vm_count": sum(1 for v in MOCK_VMS if v["host_server"] == n["name"]),
                "version": n["version"],
            }
            for n in MOCK_NODES
        ]
        overall = "healthy" if MOCK_MODE == "healthy" else "warning"
        return {
            "connected": True,
            "status": overall,
            "nodes": nodes,
            "cluster_summary": "All nodes operational" if MOCK_MODE == "healthy" else "pve-node02 memory pressure",
        }

    async def get_tasks(self, node: str | None = None) -> dict:
        if MOCK_MODE == "offline":
            return {"connected": False, "error": "Host unreachable", "count": 0, "items": []}
        items = MOCK_TASKS
        if node:
            items = [t for t in items if t["node"] == node]
        return {"connected": True, "count": len(items), "items": items}

    async def start_lxc(self, vm_id: str) -> dict:
        if MOCK_MODE == "offline":
            return {"connected": False, "error": "Host unreachable"}
        for c in MOCK_LXC:
            if c["id"] == vm_id:
                if c["state"] == "running":
                    return {"success": False, "error": "Container is already running", "vm_name": c["name"]}
                return {"success": True, "message": f"Container '{c['name']}' started", "vm_name": c["name"]}
        return {"success": False, "error": f"LXC container not found: {vm_id}"}

    async def stop_lxc(self, vm_id: str) -> dict:
        if MOCK_MODE == "offline":
            return {"connected": False, "error": "Host unreachable"}
        for c in MOCK_LXC:
            if c["id"] == vm_id:
                if c["state"] == "stopped":
                    return {"success": False, "error": "Container is already stopped", "vm_name": c["name"]}
                return {"success": True, "message": f"Container '{c['name']}' stopped", "vm_name": c["name"]}
        return {"success": False, "error": f"LXC container not found: {vm_id}"}
