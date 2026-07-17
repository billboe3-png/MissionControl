"""
Mission Control Hyper-V Schemas

Pydantic request/response models for the Hyper-V API.
"""

from pydantic import BaseModel

# ------------------------------------------------------------------ #
# VM                                                                  #
# ------------------------------------------------------------------ #


class HyperVVmResponse(BaseModel):
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


class HyperVVmListResponse(BaseModel):
    count: int
    items: list[HyperVVmResponse]


class HyperVVmDetailResponse(BaseModel):
    item: HyperVVmResponse


class HyperVVmActionResponse(BaseModel):
    success: bool
    message: str | None = None
    error: str | None = None
    vm_name: str | None = None


# ------------------------------------------------------------------ #
# Network                                                             #
# ------------------------------------------------------------------ #


class HyperVNetworkResponse(BaseModel):
    id: str
    name: str
    switch_type: str
    vlan_id: int | None = None
    mac_address_spoofing: bool = False
    allow_management_os: bool = True
    status: str
    connected_vms: int = 0
    net_adapter: str | None = None


class HyperVNetworkListResponse(BaseModel):
    count: int
    items: list[HyperVNetworkResponse]


# ------------------------------------------------------------------ #
# Storage                                                             #
# ------------------------------------------------------------------ #


class HyperVStorageResponse(BaseModel):
    id: str
    name: str
    path: str
    size_bytes: int
    used_bytes: int
    type: str
    vm_name: str | None = None
    attached: bool
    format: str | None = None


class HyperVStorageListResponse(BaseModel):
    count: int
    items: list[HyperVStorageResponse]


# ------------------------------------------------------------------ #
# Checkpoint                                                          #
# ------------------------------------------------------------------ #


class HyperVCheckpointResponse(BaseModel):
    id: str
    name: str
    vm_name: str
    vm_id: str | None = None
    checkpoint_type: str
    creation_time: str | None = None
    size_bytes: int
    parent_checkpoint_id: str | None = None
    notes: str | None = None


class HyperVCheckpointListResponse(BaseModel):
    count: int
    items: list[HyperVCheckpointResponse]


class HyperVCheckpointCreateRequest(BaseModel):
    vm_id: str
    name: str | None = None


class HyperVCheckpointActionResponse(BaseModel):
    success: bool
    message: str | None = None
    error: str | None = None
    checkpoint: dict | None = None


# ------------------------------------------------------------------ #
# Hosts                                                               #
# ------------------------------------------------------------------ #


class HyperVHostInfo(BaseModel):
    id: int
    name: str
    host: str


class HyperVHostListResponse(BaseModel):
    hosts: list[HyperVHostInfo]


# ------------------------------------------------------------------ #
# Summary & Health                                                    #
# ------------------------------------------------------------------ #


class HyperVSummaryResponse(BaseModel):
    connected: bool
    hostname: str | None = None
    version: str | None = None
    total_vms: int = 0
    running: int = 0
    stopped: int = 0
    paused: int = 0
    saved: int = 0
    total_cpu: int = 0
    total_memory_gb: float = 0.0
    used_memory_gb: float = 0.0
    total_storage_gb: float = 0.0
    used_storage_gb: float = 0.0
    host_servers: list[str] = []
    network_switches: int = 0
    total_checkpoints: int = 0
    error: str | None = None


class HyperVHealthHostResponse(BaseModel):
    name: str
    status: str
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    uptime_seconds: int = 0
    vm_count: int = 0
    version: str | None = None


class HyperVHealthResponse(BaseModel):
    connected: bool
    status: str
    hosts: list[HyperVHealthHostResponse] = []
    cluster_summary: str | None = None
    error: str | None = None


class HyperVConnectionTestResponse(BaseModel):
    connected: bool
    latency_ms: int = 0
    message: str | None = None
    version: str | None = None
    hostname: str | None = None
    error: str | None = None


# ------------------------------------------------------------------ #
# Replication                                                         #
# ------------------------------------------------------------------ #


class HyperVReplicationItem(BaseModel):
    vm_name: str
    replica_server: str
    replica_port: int = 443
    state: str
    health: str
    frequency_seconds: int = 0
    last_replication_time: str | None = None
    last_result_code: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0


class HyperVReplicationResponse(BaseModel):
    connected: bool
    replicating: int = 0
    total: int = 0
    items: list[HyperVReplicationItem] = []
    error: str | None = None
