"""
Mission Control Proxmox Production Provider

Connects to Proxmox VE via the official REST API.
Configuration is injected from IntegrationProfile — never reads config.py.
"""

import logging

import httpx

from .base_provider import ProxmoxProvider

logger = logging.getLogger(__name__)


async def _api_call(
    base_url: str,
    token: str,
    method: str,
    path: str,
    timeout: int = 30,
    verify_ssl: bool = True,
    **params,
) -> dict:
    """Execute an API call against the Proxmox VE REST API."""
    url = f"{base_url.rstrip('/')}/api2/json{path}"
    headers = {"Authorization": f"PVEAPIToken={token}"}
    try:
        async with httpx.AsyncClient(verify=verify_ssl, timeout=timeout) as client:
            resp = await client.request(method, url, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()
            return {"success": True, "data": data.get("data", data)}
    except httpx.TimeoutException:
        return {"success": False, "data": None, "error": "Request timed out"}
    except httpx.HTTPStatusError as e:
        return {"success": False, "data": None, "error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
    except Exception as e:
        return {"success": False, "data": None, "error": str(e)}


class ProxmoxRESTProvider(ProxmoxProvider):
    """Production Proxmox provider using the official REST API.

    Configuration is injected from IntegrationProfile fields:
      - base_url: Proxmox VE server URL (https://pve.example.com:8006)
      - username: API token ID (e.g. 'user@pve!tokenname')
      - encrypted_secret: API token secret (decrypted before injection)
      - timeout: operation timeout
      - verify_ssl: verify TLS certificates
    """

    def __init__(
        self,
        base_url: str,
        token: str,
        timeout: int = 30,
        verify_ssl: bool = True,
    ) -> None:
        self._base_url = base_url
        self._token = token
        self._timeout = timeout
        self._verify_ssl = verify_ssl

    async def _get(self, path: str, **params) -> dict:
        return await _api_call(
            self._base_url, self._token, "GET", path,
            self._timeout, self._verify_ssl, **params,
        )

    async def _post(self, path: str, **params) -> dict:
        return await _api_call(
            self._base_url, self._token, "POST", path,
            self._timeout, self._verify_ssl, **params,
        )

    async def _delete(self, path: str, **params) -> dict:
        return await _api_call(
            self._base_url, self._token, "DELETE", path,
            self._timeout, self._verify_ssl, **params,
        )

    async def test_connection(self) -> dict:
        result = await self._get("/version")
        if not result["success"]:
            return {"connected": False, "error": result["error"], "latency_ms": 0}
        data = result["data"]
        return {
            "connected": True,
            "latency_ms": 0,
            "message": f"Connected to Proxmox VE {data.get('version', 'unknown')}",
            "version": data.get("version", "unknown"),
            "hostname": self._base_url,
        }

    async def get_summary(self) -> dict:
        nodes_r = await self._get("/nodes")
        vms_r = await self._get("/cluster/resources", type="vm")
        storage_r = await self._get("/cluster/resources", type="storage")

        if not nodes_r["success"]:
            return {"connected": False, "error": nodes_r["error"], "total_vms": 0, "running": 0, "stopped": 0, "paused": 0, "total_cpu": 0, "total_memory_gb": 0, "used_memory_gb": 0, "total_storage_gb": 0, "used_storage_gb": 0}

        nodes = nodes_r["data"] or []
        vms = [v for v in (vms_r["data"] or []) if v.get("type") == "qemu"]
        lxcs = [v for v in (vms_r["data"] or []) if v.get("type") == "lxc"]
        storages = storage_r["data"] or []

        running = sum(1 for v in vms if v.get("status") == "running")
        stopped = sum(1 for v in vms if v.get("status") == "stopped")
        paused = sum(1 for v in vms if v.get("status") == "paused")
        total_cpu = sum(v.get("cpus", 0) or 0 for v in vms)
        total_mem = sum(v.get("maxmem", 0) or 0 for v in vms)
        used_mem = sum(v.get("mem", 0) or 0 for v in vms)
        total_disk = sum(v.get("maxdisk", 0) or 0 for v in storages)
        used_disk = sum(v.get("disk", 0) or 0 for v in storages)

        return {
            "connected": True,
            "cluster_name": "pve-cluster",
            "version": nodes[0].get("version", "") if nodes else "",
            "nodes_online": sum(1 for n in nodes if n.get("status") == "online"),
            "nodes_total": len(nodes),
            "total_vms": len(vms),
            "running": running,
            "stopped": stopped,
            "paused": paused,
            "total_lxc": len(lxcs),
            "running_lxc": sum(1 for c in lxcs if c.get("status") == "running"),
            "stopped_lxc": sum(1 for c in lxcs if c.get("status") == "stopped"),
            "total_cpu": total_cpu,
            "total_memory_gb": round(total_mem / (1024 ** 3), 1) if total_mem else 0,
            "used_memory_gb": round(used_mem / (1024 ** 3), 1) if used_mem else 0,
            "total_storage_gb": round(total_disk / (1024 ** 3), 1) if total_disk else 0,
            "used_storage_gb": round(used_disk / (1024 ** 3), 1) if used_disk else 0,
            "storage_count": len(storages),
            "network_count": 0,
            "total_snapshots": 0,
        }

    async def get_nodes(self) -> dict:
        result = await self._get("/nodes")
        if not result["success"]:
            return {"connected": False, "error": result["error"], "count": 0, "items": []}
        items = [
            {
                "name": n.get("node", ""),
                "status": n.get("status", "unknown"),
                "cpu_percent": round((n.get("cpu", 0) or 0) * 100, 1),
                "memory_total_mb": round((n.get("maxmem", 0) or 0) / 1048576),
                "memory_used_mb": round((n.get("mem", 0) or 0) / 1048576),
                "disk_total_gb": round((n.get("maxdisk", 0) or 0) / (1024 ** 3), 1),
                "disk_used_gb": round((n.get("disk", 0) or 0) / (1024 ** 3), 1),
                "uptime_seconds": n.get("uptime", 0) or 0,
                "version": n.get("version", ""),
                "ssl_fingerprint": n.get("ssl_fingerprint", ""),
            }
            for n in (result["data"] or [])
        ]
        return {"connected": True, "count": len(items), "items": items}

    async def get_vms(self) -> dict:
        result = await self._get("/cluster/resources", type="vm")
        if not result["success"]:
            return {"connected": False, "error": result["error"], "count": 0, "items": []}
        items = [
            {
                "id": str(v.get("vmid", "")),
                "name": v.get("name", ""),
                "state": v.get("status", "unknown"),
                "cpu_count": v.get("cpus", 0) or 0,
                "memory_assigned_mb": round((v.get("maxmem", 0) or 0) / 1048576),
                "memory_startup_mb": round((v.get("maxmem", 0) or 0) / 1048576),
                "memory_demand_mb": round((v.get("mem", 0) or 0) / 1048576),
                "uptime_seconds": v.get("uptime", 0) or 0,
                "host_server": v.get("node", ""),
                "guest_os": "",
                "creation_time": None,
                "cpu_usage_percent": round((v.get("cpu", 0) or 0) * 100, 1),
                "disk_read_mbps": 0.0,
                "disk_write_mbps": 0.0,
                "network_receive_mbps": 0.0,
                "network_send_mbps": 0.0,
                "status_message": "",
                "integration_services_enabled": True,
                "last_checkpoint": None,
            }
            for v in (result["data"] or [])
            if v.get("type") == "qemu"
        ]
        return {"connected": True, "count": len(items), "items": items}

    async def get_vm_detail(self, vm_id: str) -> dict:
        nodes_r = await self._get("/nodes")
        if not nodes_r["success"]:
            return {"connected": False, "error": nodes_r["error"]}
        for node in nodes_r["data"] or []:
            vm_r = await self._get(f"/nodes/{node['node']}/qemu/{vm_id}/config", current=1)
            if vm_r["success"] and vm_r["data"]:
                data = vm_r["data"]
                status_r = await self._get(f"/nodes/{node['node']}/qemu/{vm_id}/status/current")
                status = status_r["data"].get("status", "unknown") if status_r["success"] else "unknown"
                return {
                    "connected": True,
                    "item": {
                        "id": vm_id,
                        "name": data.get("name", ""),
                        "state": status,
                        "cpu_count": data.get("cores", 0) or 0,
                        "memory_assigned_mb": round((data.get("memory", 0) or 0) / 1048576),
                        "memory_startup_mb": round((data.get("memory", 0) or 0) / 1048576),
                        "memory_demand_mb": 0,
                        "uptime_seconds": 0,
                        "host_server": node["node"],
                        "guest_os": data.get("ostype", ""),
                        "creation_time": None,
                        "cpu_usage_percent": 0.0,
                        "status_message": "",
                        "integration_services_enabled": True,
                        "last_checkpoint": None,
                    },
                }
        return {"connected": False, "error": f"VM not found: {vm_id}"}

    async def start_vm(self, vm_id: str) -> dict:
        res_r = await self._get("/cluster/resources", type="vm")
        if not res_r["success"]:
            return {"connected": False, "error": res_r["error"]}
        target = next((v for v in (res_r["data"] or []) if str(v.get("vmid")) == vm_id and v.get("type") == "qemu"), None)
        if not target:
            return {"success": False, "error": f"VM not found: {vm_id}"}
        node = target.get("node", "")
        if target.get("status") == "running":
            return {"success": True, "message": "VM already running"}
        result = await self._post(f"/nodes/{node}/qemu/{vm_id}/status/start")
        if not result["success"]:
            return {"success": False, "error": result.get("error", "Failed to start VM")}
        return {"success": True, "message": "VM started"}

    async def stop_vm(self, vm_id: str, force: bool = False) -> dict:
        res_r = await self._get("/cluster/resources", type="vm")
        if not res_r["success"]:
            return {"connected": False, "error": res_r["error"]}
        target = next((v for v in (res_r["data"] or []) if str(v.get("vmid")) == vm_id and v.get("type") == "qemu"), None)
        if not target:
            return {"success": False, "error": f"VM not found: {vm_id}"}
        node = target.get("node", "")
        if target.get("status") == "stopped":
            return {"success": True, "message": "VM already stopped"}
        action = "stop" if force else "shutdown"
        result = await self._post(f"/nodes/{node}/qemu/{vm_id}/status/{action}")
        if not result["success"]:
            return {"success": False, "error": result.get("error", f"Failed to {action} VM")}
        return {"success": True, "message": f"VM {action} initiated"}

    async def restart_vm(self, vm_id: str) -> dict:
        res_r = await self._get("/cluster/resources", type="vm")
        if not res_r["success"]:
            return {"connected": False, "error": res_r["error"]}
        target = next((v for v in (res_r["data"] or []) if str(v.get("vmid")) == vm_id and v.get("type") == "qemu"), None)
        if not target:
            return {"success": False, "error": f"VM not found: {vm_id}"}
        node = target.get("node", "")
        result = await self._post(f"/nodes/{node}/qemu/{vm_id}/status/reboot")
        if not result["success"]:
            return {"success": False, "error": result.get("error", "Failed to reboot VM")}
        return {"success": True, "message": "VM reboot initiated"}

    async def pause_vm(self, vm_id: str) -> dict:
        res_r = await self._get("/cluster/resources", type="vm")
        if not res_r["success"]:
            return {"connected": False, "error": res_r["error"]}
        target = next((v for v in (res_r["data"] or []) if str(v.get("vmid")) == vm_id and v.get("type") == "qemu"), None)
        if not target:
            return {"success": False, "error": f"VM not found: {vm_id}"}
        node = target.get("node", "")
        if target.get("status") != "running":
            return {"success": False, "error": "VM must be running to suspend"}
        result = await self._post(f"/nodes/{node}/qemu/{vm_id}/status/suspend")
        if not result["success"]:
            return {"success": False, "error": result.get("error", "Failed to suspend VM")}
        return {"success": True, "message": "VM suspended"}

    async def resume_vm(self, vm_id: str) -> dict:
        return await self.start_vm(vm_id)

    async def get_networks(self) -> dict:
        nodes_r = await self._get("/nodes")
        if not nodes_r["success"]:
            return {"connected": False, "error": nodes_r["error"], "count": 0, "items": []}
        all_items = []
        for node in nodes_r["data"] or []:
            result = await self._get(f"/nodes/{node['node']}/network")
            if result["success"]:
                for iface in result["data"] or []:
                    all_items.append({
                        "id": f"{node['node']}/{iface.get('iface', '')}",
                        "name": iface.get("iface", ""),
                        "switch_type": iface.get("type", "unknown"),
                        "vlan_id": iface.get("vlan"),
                        "status": "operational" if iface.get("active") else "inactive",
                        "node": node["node"],
                        "cidr": iface.get("cidr", ""),
                        "address": iface.get("address", ""),
                        "gateway": iface.get("gateway"),
                        "connected_vms": 0,
                        "type": iface.get("type", "unknown"),
                    })
        return {"connected": True, "count": len(all_items), "items": all_items}

    async def get_storage(self) -> dict:
        result = await self._get("/cluster/resources", type="storage")
        if not result["success"]:
            return {"connected": False, "error": result["error"], "count": 0, "items": []}
        items = [
            {
                "id": s.get("storage", ""),
                "name": s.get("storage", ""),
                "path": "",
                "size_bytes": s.get("maxdisk", 0) or 0,
                "used_bytes": s.get("disk", 0) or 0,
                "type": s.get("type", ""),
                "status": "available" if s.get("active") else "inactive",
                "content": "",
                "node": s.get("node", ""),
            }
            for s in (result["data"] or [])
        ]
        return {"connected": True, "count": len(items), "items": items}

    async def get_snapshots(self, vm_id: str | None = None) -> dict:
        if not vm_id:
            return {"connected": True, "count": 0, "items": []}
        nodes_r = await self._get("/nodes")
        if not nodes_r["success"]:
            return {"connected": False, "error": nodes_r["error"], "count": 0, "items": []}
        all_items = []
        for node in nodes_r["data"] or []:
            result = await self._get(f"/nodes/{node['node']}/qemu/{vm_id}/snapshots")
            if result["success"]:
                for snap in result["data"] or []:
                    all_items.append({
                        "id": snap.get("name", ""),
                        "name": snap.get("name", ""),
                        "vm_name": "",
                        "vm_id": vm_id,
                        "checkpoint_type": "snapshot",
                        "creation_time": snap.get("snaptime"),
                        "size_bytes": 0,
                        "parent_checkpoint_id": None,
                        "notes": snap.get("notes", ""),
                    })
        return {"connected": True, "count": len(all_items), "items": all_items}

    async def create_snapshot(self, vm_id: str, name: str | None = None) -> dict:
        snap_name = name or f"snap-{vm_id}"
        nodes_r = await self._get("/nodes")
        if not nodes_r["success"]:
            return {"connected": False, "error": nodes_r["error"]}
        for node in nodes_r["data"] or []:
            result = await self._post(
                f"/nodes/{node['node']}/qemu/{vm_id}/snapshot",
                snapname=snap_name,
            )
            if result["success"]:
                return {
                    "success": True,
                    "message": f"Snapshot '{snap_name}' created",
                    "snapshot": {"id": snap_name, "name": snap_name, "vm_id": vm_id},
                }
        return {"success": False, "error": f"VM not found: {vm_id}"}

    async def delete_snapshot(self, vm_id: str, snapshot_id: str) -> dict:
        nodes_r = await self._get("/nodes")
        if not nodes_r["success"]:
            return {"connected": False, "error": nodes_r["error"]}
        for node in nodes_r["data"] or []:
            result = await self._delete(
                f"/nodes/{node['node']}/qemu/{vm_id}/snapshot/{snapshot_id}",
            )
            if result["success"]:
                return {"success": True, "message": f"Snapshot '{snapshot_id}' deleted"}
        return {"success": False, "error": f"Snapshot not found: {snapshot_id}"}

    async def get_health(self) -> dict:
        result = await self._get("/nodes")
        if not result["success"]:
            return {"connected": False, "error": result["error"], "status": "unavailable"}
        nodes = [
            {
                "name": n.get("node", ""),
                "status": "healthy" if n.get("status") == "online" else "offline",
                "cpu_percent": round((n.get("cpu", 0) or 0) * 100, 1),
                "memory_percent": round((n.get("mem", 0) or 0) / (n.get("maxmem", 1) or 1) * 100, 1),
                "uptime_seconds": n.get("uptime", 0) or 0,
                "vm_count": 0,
                "version": n.get("version", ""),
            }
            for n in (result["data"] or [])
        ]
        all_online = all(n["status"] == "healthy" for n in nodes)
        return {
            "connected": True,
            "status": "healthy" if all_online else "warning",
            "nodes": nodes,
            "cluster_summary": "All nodes operational" if all_online else "Some nodes offline",
        }

    async def get_tasks(self, node: str | None = None) -> dict:
        target_node = node
        if not target_node:
            nodes_r = await self._get("/nodes")
            if nodes_r["success"] and nodes_r["data"]:
                target_node = nodes_r["data"][0]["node"]
        if not target_node:
            return {"connected": True, "count": 0, "items": []}
        result = await self._get(f"/nodes/{target_node}/tasks", limit=20)
        if not result["success"]:
            return {"connected": False, "error": result["error"], "count": 0, "items": []}
        items = [
            {
                "id": t.get("upid", ""),
                "node": target_node,
                "type": t.get("type", ""),
                "user": t.get("user", ""),
                "status": t.get("status", ""),
                "start_time": t.get("starttime"),
                "end_time": t.get("endtime"),
                "upid": t.get("upid", ""),
            }
            for t in (result["data"] or [])
        ]
        return {"connected": True, "count": len(items), "items": items}

    async def start_lxc(self, vm_id: str) -> dict:
        res_r = await self._get("/cluster/resources", type="vm")
        if not res_r["success"]:
            return {"connected": False, "error": res_r["error"]}
        target = next((c for c in (res_r["data"] or []) if str(c.get("vmid")) == vm_id and c.get("type") == "lxc"), None)
        if not target:
            return {"success": False, "error": f"LXC container not found: {vm_id}"}
        node = target.get("node", "")
        if target.get("status") == "running":
            return {"success": True, "message": "Container already running"}
        result = await self._post(f"/nodes/{node}/lxc/{vm_id}/status/start")
        if not result["success"]:
            return {"success": False, "error": result.get("error", "Failed to start container")}
        return {"success": True, "message": "Container started"}

    async def stop_lxc(self, vm_id: str) -> dict:
        res_r = await self._get("/cluster/resources", type="vm")
        if not res_r["success"]:
            return {"connected": False, "error": res_r["error"]}
        target = next((c for c in (res_r["data"] or []) if str(c.get("vmid")) == vm_id and c.get("type") == "lxc"), None)
        if not target:
            return {"success": False, "error": f"LXC container not found: {vm_id}"}
        node = target.get("node", "")
        if target.get("status") == "stopped":
            return {"success": True, "message": "Container already stopped"}
        result = await self._post(f"/nodes/{node}/lxc/{vm_id}/status/stop")
        if not result["success"]:
            return {"success": False, "error": result.get("error", "Failed to stop container")}
        return {"success": True, "message": "Container stopped"}

    async def get_lxc_containers(self) -> dict:
        result = await self._get("/cluster/resources", type="vm")
        if not result["success"]:
            return {"connected": False, "error": result["error"], "count": 0, "items": []}
        items = [
            {
                "id": str(c.get("vmid", "")),
                "name": c.get("name", ""),
                "state": c.get("status", "unknown"),
                "cpu_count": c.get("cpus", 0) or 0,
                "memory_assigned_mb": round((c.get("maxmem", 0) or 0) / 1048576),
                "memory_startup_mb": round((c.get("maxmem", 0) or 0) / 1048576),
                "memory_demand_mb": round((c.get("mem", 0) or 0) / 1048576),
                "uptime_seconds": c.get("uptime", 0) or 0,
                "host_server": c.get("node", ""),
                "guest_os": "",
                "creation_time": None,
                "cpu_usage_percent": round((c.get("cpu", 0) or 0) * 100, 1),
                "disk_read_mbps": 0.0,
                "disk_write_mbps": 0.0,
                "network_receive_mbps": 0.0,
                "network_send_mbps": 0.0,
                "status_message": "",
            }
            for c in (result["data"] or [])
            if c.get("type") == "lxc"
        ]
        return {"connected": True, "count": len(items), "items": items}

    async def get_lxc_detail(self, vm_id: str) -> dict:
        nodes_r = await self._get("/nodes")
        if not nodes_r["success"]:
            return {"connected": False, "error": nodes_r["error"]}
        for node in nodes_r["data"] or []:
            result = await self._get(f"/nodes/{node['node']}/lxc/{vm_id}/config")
            if result["success"] and result["data"]:
                data = result["data"]
                return {
                    "connected": True,
                    "item": {
                        "id": vm_id,
                        "name": data.get("hostname", ""),
                        "state": "running",
                        "cpu_count": data.get("cores", 0) or 0,
                        "memory_assigned_mb": round((data.get("memory", 0) or 0) / 1048576),
                        "memory_startup_mb": round((data.get("memory", 0) or 0) / 1048576),
                        "memory_demand_mb": 0,
                        "uptime_seconds": 0,
                        "host_server": node["node"],
                        "guest_os": data.get("ostype", ""),
                        "creation_time": None,
                        "cpu_usage_percent": 0.0,
                        "status_message": "",
                    },
                }
        return {"connected": False, "error": f"LXC container not found: {vm_id}"}
