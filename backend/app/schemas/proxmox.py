"""
Mission Control Proxmox Schemas

Pydantic request/response models for the Proxmox API.
"""

from pydantic import BaseModel

# ------------------------------------------------------------------ #
# VM                                                                  #
# ------------------------------------------------------------------ #


class ProxmoxVmResponse(BaseModel):
    id: str
    name: str
    state: str
    cpu_count: int
    memory_assigned_mb: int
    memory_startup_mb: int
    memory_demand_mb: int
    uptime_seconds: int
    host_server: str
    guest_os: str
    creation_time: str | None = None
    last_checkpoint: str | None = None
    status_message: str
    integration_services_enabled: bool
    cpu_usage_percent: float = 0.0
    disk_read_mbps: float = 0.0
    disk_write_mbps: float = 0.0
    network_receive_mbps: float = 0.0
    network_send_mbps: float = 0.0


class ProxmoxVmListResponse(BaseModel):
    count: int
    items: list[ProxmoxVmResponse]


class ProxmoxVmDetailResponse(BaseModel):
    item: ProxmoxVmResponse


class ProxmoxVmActionResponse(BaseModel):
    success: bool
    message: str | None = None
    error: str | None = None
    vm_name: str | None = None


# ------------------------------------------------------------------ #
# LXC Containers                                                      #
# ------------------------------------------------------------------ #


class ProxmoxLxcResponse(BaseModel):
    id: str
    name: str
    state: str
    cpu_count: int
    memory_assigned_mb: int
    memory_startup_mb: int
    memory_demand_mb: int
    uptime_seconds: int
    host_server: str
    guest_os: str
    creation_time: str | None = None
    cpu_usage_percent: float = 0.0
    disk_read_mbps: float = 0.0
    disk_write_mbps: float = 0.0
    network_receive_mbps: float = 0.0
    network_send_mbps: float = 0.0
    status_message: str


class ProxmoxLxcListResponse(BaseModel):
    count: int
    items: list[ProxmoxLxcResponse]


class ProxmoxLxcDetailResponse(BaseModel):
    item: ProxmoxLxcResponse


class ProxmoxLxcActionResponse(BaseModel):
    success: bool
    message: str | None = None
    error: str | None = None
    vm_name: str | None = None


class ProxmoxLxcTemplateResponse(BaseModel):
    id: str
    name: str
    file: str
    node: str
    size_bytes: int = 0
    os: str = ""
    description: str = ""
    version: str = ""
    arch: str = ""


class ProxmoxLxcTemplateListResponse(BaseModel):
    count: int
    items: list[ProxmoxLxcTemplateResponse]


class ProxmoxLxcCreateRequest(BaseModel):
    node: str
    vmid: str | None = None
    ostemplate: str
    hostname: str = "mission-control"
    cores: int = 2
    memory: int = 4096
    swap: int = 0
    disk: int = 8
    storage: str = "local-lvm"
    password: str | None = None
    unprivileged: bool = True
    nesting: bool = True
    net_bridge: str = "vmbr0"
    net_ip: str = "dhcp"
    nameserver: str | None = None
    searchdomain: str | None = None
    description: str | None = None


class ProxmoxLxcCreateResponse(BaseModel):
    success: bool
    vmid: str | None = None
    node: str | None = None
    message: str | None = None
    error: str | None = None


class ProxmoxLxcCloneRequest(BaseModel):
    new_vmid: str | None = None
    hostname: str | None = None


class ProxmoxLxcDeleteResponse(BaseModel):
    success: bool
    message: str | None = None
    error: str | None = None


# ------------------------------------------------------------------ #
# Node                                                                #
# ------------------------------------------------------------------ #


class ProxmoxNodeResponse(BaseModel):
    name: str
    status: str
    cpu_percent: float = 0.0
    memory_total_mb: int = 0
    memory_used_mb: int = 0
    disk_total_gb: float = 0.0
    disk_used_gb: float = 0.0
    uptime_seconds: int = 0
    version: str = ""
    ssl_fingerprint: str = ""


class ProxmoxNodeListResponse(BaseModel):
    count: int
    items: list[ProxmoxNodeResponse]


# ------------------------------------------------------------------ #
# Network                                                             #
# ------------------------------------------------------------------ #


class ProxmoxNetworkResponse(BaseModel):
    id: str
    name: str
    switch_type: str
    vlan_id: int | None = None
    status: str
    node: str
    cidr: str = ""
    address: str = ""
    gateway: str | None = None
    connected_vms: int = 0
    type: str = "unknown"


class ProxmoxNetworkListResponse(BaseModel):
    count: int
    items: list[ProxmoxNetworkResponse]


# ------------------------------------------------------------------ #
# Storage                                                             #
# ------------------------------------------------------------------ #


class ProxmoxStorageResponse(BaseModel):
    id: str
    name: str
    path: str
    size_bytes: int
    used_bytes: int
    type: str
    status: str = "available"
    content: str = ""
    node: str = ""


class ProxmoxStorageListResponse(BaseModel):
    count: int
    items: list[ProxmoxStorageResponse]


# ------------------------------------------------------------------ #
# Task                                                                #
# ------------------------------------------------------------------ #


class ProxmoxTaskResponse(BaseModel):
    id: str
    node: str
    type: str
    user: str
    status: str
    start_time: str | None = None
    end_time: str | None = None
    upid: str = ""


class ProxmoxTaskListResponse(BaseModel):
    count: int
    items: list[ProxmoxTaskResponse]


# ------------------------------------------------------------------ #
# Snapshot                                                            #
# ------------------------------------------------------------------ #


class ProxmoxSnapshotResponse(BaseModel):
    id: str
    name: str
    vm_name: str
    vm_id: str | None = None
    checkpoint_type: str = "snapshot"
    creation_time: str | None = None
    size_bytes: int = 0
    parent_checkpoint_id: str | None = None
    notes: str | None = None


class ProxmoxSnapshotListResponse(BaseModel):
    count: int
    items: list[ProxmoxSnapshotResponse]


class ProxmoxSnapshotCreateRequest(BaseModel):
    vm_id: str
    name: str | None = None


class ProxmoxSnapshotActionResponse(BaseModel):
    success: bool
    message: str | None = None
    error: str | None = None
    snapshot: dict | None = None


# ------------------------------------------------------------------ #
# Summary & Health                                                    #
# ------------------------------------------------------------------ #


class ProxmoxSummaryResponse(BaseModel):
    connected: bool
    cluster_name: str | None = None
    version: str | None = None
    nodes_online: int = 0
    nodes_total: int = 0
    total_vms: int = 0
    running: int = 0
    stopped: int = 0
    paused: int = 0
    total_lxc: int = 0
    running_lxc: int = 0
    stopped_lxc: int = 0
    total_cpu: int = 0
    total_memory_gb: float = 0.0
    used_memory_gb: float = 0.0
    total_storage_gb: float = 0.0
    used_storage_gb: float = 0.0
    storage_count: int = 0
    network_count: int = 0
    total_snapshots: int = 0
    error: str | None = None


class ProxmoxHealthNodeResponse(BaseModel):
    name: str
    status: str
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    uptime_seconds: int = 0
    vm_count: int = 0
    version: str | None = None


class ProxmoxHealthResponse(BaseModel):
    connected: bool
    status: str
    nodes: list[ProxmoxHealthNodeResponse] = []
    cluster_summary: str | None = None
    error: str | None = None


class ProxmoxConnectionTestResponse(BaseModel):
    connected: bool
    latency_ms: int = 0
    message: str | None = None
    version: str | None = None
    hostname: str | None = None
    error: str | None = None
