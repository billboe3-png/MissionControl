const API = "/api/v1/hyperv";

export interface HyperVVm {
    id: string;
    name: string;
    state: string;
    cpu_count: number;
    memory_assigned_mb: number;
    memory_startup_mb: number;
    memory_demand_mb: number;
    uptime_seconds: number;
    host_server: string;
    guest_os: string;
    creation_time: string | null;
    last_checkpoint: string | null;
    status_message: string;
    integration_services_enabled: boolean;
    cpu_usage_percent: number;
    disk_read_mbps: number;
    disk_write_mbps: number;
    network_receive_mbps: number;
    network_send_mbps: number;
}

export interface HyperVNetwork {
    id: string;
    name: string;
    switch_type: string;
    vlan_id: number | null;
    mac_address_spoofing: boolean;
    allow_management_os: boolean;
    status: string;
    connected_vms: number;
    net_adapter: string | null;
}

export interface HyperVStorage {
    id: string;
    name: string;
    path: string;
    size_bytes: number;
    used_bytes: number;
    type: string;
    vm_name: string | null;
    attached: boolean;
    format: string | null;
}

export interface HyperVCheckpoint {
    id: string;
    name: string;
    vm_name: string;
    vm_id: string | null;
    checkpoint_type: string;
    creation_time: string | null;
    size_bytes: number;
    parent_checkpoint_id: string | null;
    notes: string | null;
}

export interface HyperVSummary {
    connected: boolean;
    hostname: string | null;
    version: string | null;
    total_vms: number;
    running: number;
    stopped: number;
    paused: number;
    saved: number;
    total_cpu: number;
    total_memory_gb: number;
    used_memory_gb: number;
    total_storage_gb: number;
    used_storage_gb: number;
    host_servers: string[];
    network_switches: number;
    total_checkpoints: number;
    error: string | null;
}

export interface HyperVHealthHost {
    name: string;
    status: string;
    cpu_percent: number;
    memory_percent: number;
    uptime_seconds: number;
    vm_count: number;
    version: string | null;
}

export interface HyperVHealth {
    connected: boolean;
    status: string;
    hosts: HyperVHealthHost[];
    cluster_summary: string | null;
    error: string | null;
}

export interface HyperVActionResponse {
    success: boolean;
    message: string | null;
    error: string | null;
    vm_name: string | null;
}

export const hypervApi = {
    async getSummary(): Promise<HyperVSummary> {
        const response = await fetch(`${API}/overview`);
        if (!response.ok) throw new Error("Failed to load Hyper-V overview");
        return response.json();
    },

    async getHealth(): Promise<HyperVHealth> {
        const response = await fetch(`${API}/health`);
        if (!response.ok) throw new Error("Failed to load Hyper-V health");
        return response.json();
    },

    async testConnection(): Promise<{ connected: boolean; latency_ms: number; message: string | null; hostname: string | null; error: string | null }> {
        const response = await fetch(`${API}/test`);
        if (!response.ok) throw new Error("Connection test failed");
        return response.json();
    },

    async listVms(): Promise<HyperVVm[]> {
        const response = await fetch(`${API}/vms`);
        if (!response.ok) throw new Error("Failed to load VMs");
        const data = await response.json();
        return data.items ?? [];
    },

    async getVm(vmId: string): Promise<HyperVVm> {
        const response = await fetch(`${API}/vms/${vmId}`);
        if (!response.ok) throw new Error("Failed to load VM");
        const data = await response.json();
        return data.item;
    },

    async startVm(vmId: string): Promise<HyperVActionResponse> {
        const response = await fetch(`${API}/vms/${vmId}/start`, { method: "POST" });
        if (!response.ok) throw new Error("Failed to start VM");
        return response.json();
    },

    async stopVm(vmId: string, force = false): Promise<HyperVActionResponse> {
        const response = await fetch(`${API}/vms/${vmId}/stop?force=${force}`, { method: "POST" });
        if (!response.ok) throw new Error("Failed to stop VM");
        return response.json();
    },

    async restartVm(vmId: string): Promise<HyperVActionResponse> {
        const response = await fetch(`${API}/vms/${vmId}/restart`, { method: "POST" });
        if (!response.ok) throw new Error("Failed to restart VM");
        return response.json();
    },

    async pauseVm(vmId: string): Promise<HyperVActionResponse> {
        const response = await fetch(`${API}/vms/${vmId}/pause`, { method: "POST" });
        if (!response.ok) throw new Error("Failed to pause VM");
        return response.json();
    },

    async resumeVm(vmId: string): Promise<HyperVActionResponse> {
        const response = await fetch(`${API}/vms/${vmId}/resume`, { method: "POST" });
        if (!response.ok) throw new Error("Failed to resume VM");
        return response.json();
    },

    async listNetworks(): Promise<HyperVNetwork[]> {
        const response = await fetch(`${API}/networks`);
        if (!response.ok) throw new Error("Failed to load networks");
        const data = await response.json();
        return data.items ?? [];
    },

    async listStorage(): Promise<HyperVStorage[]> {
        const response = await fetch(`${API}/storage`);
        if (!response.ok) throw new Error("Failed to load storage");
        const data = await response.json();
        return data.items ?? [];
    },

    async listCheckpoints(vmId?: string): Promise<HyperVCheckpoint[]> {
        const url = vmId ? `${API}/checkpoints?vm_id=${vmId}` : `${API}/checkpoints`;
        const response = await fetch(url);
        if (!response.ok) throw new Error("Failed to load checkpoints");
        const data = await response.json();
        return data.items ?? [];
    },

    async createCheckpoint(vmId: string, name?: string): Promise<{ success: boolean; message: string | null; error: string | null }> {
        const response = await fetch(`${API}/checkpoints`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ vm_id: vmId, name }),
        });
        if (!response.ok) throw new Error("Failed to create checkpoint");
        return response.json();
    },

    async deleteCheckpoint(vmId: string, checkpointId: string): Promise<{ success: boolean; message: string | null; error: string | null }> {
        const response = await fetch(`${API}/vms/${vmId}/checkpoints/${checkpointId}`, { method: "DELETE" });
        if (!response.ok) throw new Error("Failed to delete checkpoint");
        return response.json();
    },
};
