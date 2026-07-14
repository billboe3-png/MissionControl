"""
Mission Control Virtualization Domain Models

Shared data models for all virtualization providers.
Hyper-V, Proxmox, VMware, KVM all emit these models.
"""

from pydantic import BaseModel


class VirtualMachine(BaseModel):
    """Standard virtual machine representation."""

    id: str
    name: str
    state: str
    cpu_count: int = 0
    memory_assigned_mb: int = 0
    memory_startup_mb: int = 0
    memory_demand_mb: int = 0
    uptime_seconds: int = 0
    host_server: str = ""
    guest_os: str = ""
    creation_time: str | None = None
    last_checkpoint: str | None = None
    status_message: str = ""
    integration_services_enabled: bool = False
    cpu_usage_percent: float = 0.0
    disk_read_mbps: float = 0.0
    disk_write_mbps: float = 0.0
    network_receive_mbps: float = 0.0
    network_send_mbps: float = 0.0


class VirtualHost(BaseModel):
    """Standard virtualization host representation."""

    name: str
    status: str = "unknown"
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    uptime_seconds: int = 0
    vm_count: int = 0
    version: str | None = None


class VirtualNetwork(BaseModel):
    """Standard virtual network/switch representation."""

    id: str
    name: str
    switch_type: str = ""
    vlan_id: int | None = None
    mac_address_spoofing: bool = False
    allow_management_os: bool = True
    status: str = "unknown"
    connected_vms: int = 0
    net_adapter: str | None = None


class VirtualStorage(BaseModel):
    """Standard virtual storage/disk representation."""

    id: str
    name: str
    path: str = ""
    size_bytes: int = 0
    used_bytes: int = 0
    type: str = ""
    vm_name: str | None = None
    attached: bool = True
    format: str | None = None


class Snapshot(BaseModel):
    """Standard checkpoint/snapshot representation."""

    id: str
    name: str
    vm_name: str
    vm_id: str | None = None
    checkpoint_type: str = "standard"
    creation_time: str | None = None
    size_bytes: int = 0
    parent_checkpoint_id: str | None = None
    notes: str | None = None
