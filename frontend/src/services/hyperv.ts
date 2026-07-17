import { apiClient } from "../utils/apiClient";

const API = "/api/v1/hyperv";

export interface HyperVHost {
    id: number;
    name: string;
    host: string;
}

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
    memory_used_gb: number;
    memory_total_gb: number;
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

export interface HyperVReplicationItem {
    vm_name: string;
    replica_server: string;
    replica_port: number;
    state: string;
    health: string;
    frequency_seconds: number;
    last_replication_time: string | null;
    last_result_code: number;
    bytes_sent: number;
    bytes_received: number;
}

export interface HyperVReplication {
    connected: boolean;
    replicating: number;
    total: number;
    items: HyperVReplicationItem[];
    error: string | null;
}

function hostParam(hostId: number | null): string {
    return hostId ? `?host_id=${hostId}` : "";
}

function hostParamAmp(hostId: number | null): string {
    return hostId ? `&host_id=${hostId}` : "";
}

export const hypervApi = {
    async listHosts(): Promise<HyperVHost[]> {
        const data = await apiClient<{ hosts: HyperVHost[] }>(`${API}/hosts`);
        return data.hosts ?? [];
    },

    async getSummary(hostId: number | null = null): Promise<HyperVSummary> {
        return apiClient<HyperVSummary>(`${API}/overview${hostParam(hostId)}`);
    },

    async getHealth(hostId: number | null = null): Promise<HyperVHealth> {
        return apiClient<HyperVHealth>(`${API}/health${hostParam(hostId)}`);
    },

    async testConnection(hostId: number | null = null): Promise<{ connected: boolean; latency_ms: number; message: string | null; hostname: string | null; error: string | null }> {
        return apiClient(`${API}/test${hostParam(hostId)}`);
    },

    async listVms(hostId: number | null = null): Promise<HyperVVm[]> {
        const data = await apiClient<{ items: HyperVVm[] }>(`${API}/vms${hostParam(hostId)}`);
        return data.items ?? [];
    },

    async getVm(vmId: string, hostId: number | null = null): Promise<HyperVVm> {
        const data = await apiClient<{ item: HyperVVm }>(`${API}/vms/${vmId}${hostParamAmp(hostId)}`);
        return data.item;
    },

    async startVm(vmId: string, hostId: number | null = null): Promise<HyperVActionResponse> {
        return apiClient<HyperVActionResponse>(`${API}/vms/${vmId}/start${hostParam(hostId)}`, { method: "POST" });
    },

    async stopVm(vmId: string, force = false, hostId: number | null = null): Promise<HyperVActionResponse> {
        return apiClient<HyperVActionResponse>(`${API}/vms/${vmId}/stop?force=${force}${hostParamAmp(hostId)}`, { method: "POST" });
    },

    async restartVm(vmId: string, hostId: number | null = null): Promise<HyperVActionResponse> {
        return apiClient<HyperVActionResponse>(`${API}/vms/${vmId}/restart${hostParam(hostId)}`, { method: "POST" });
    },

    async pauseVm(vmId: string, hostId: number | null = null): Promise<HyperVActionResponse> {
        return apiClient<HyperVActionResponse>(`${API}/vms/${vmId}/pause${hostParam(hostId)}`, { method: "POST" });
    },

    async resumeVm(vmId: string, hostId: number | null = null): Promise<HyperVActionResponse> {
        return apiClient<HyperVActionResponse>(`${API}/vms/${vmId}/resume${hostParam(hostId)}`, { method: "POST" });
    },

    async listNetworks(hostId: number | null = null): Promise<HyperVNetwork[]> {
        const data = await apiClient<{ items: HyperVNetwork[] }>(`${API}/networks${hostParam(hostId)}`);
        return data.items ?? [];
    },

    async listStorage(hostId: number | null = null): Promise<HyperVStorage[]> {
        const data = await apiClient<{ items: HyperVStorage[] }>(`${API}/storage${hostParam(hostId)}`);
        return data.items ?? [];
    },

    async listCheckpoints(vmId?: string, hostId: number | null = null): Promise<HyperVCheckpoint[]> {
        let url = `${API}/checkpoints`;
        const params: string[] = [];
        if (vmId) params.push(`vm_id=${vmId}`);
        if (hostId) params.push(`host_id=${hostId}`);
        if (params.length) url += `?${params.join("&")}`;
        const data = await apiClient<{ items: HyperVCheckpoint[] }>(url);
        return data.items ?? [];
    },

    async createCheckpoint(vmId: string, name?: string, hostId: number | null = null): Promise<{ success: boolean; message: string | null; error: string | null }> {
        let url = `${API}/checkpoints`;
        if (hostId) url += `?host_id=${hostId}`;
        return apiClient(url, {
            method: "POST",
            json: { vm_id: vmId, name },
        });
    },

    async deleteCheckpoint(vmId: string, checkpointId: string, hostId: number | null = null): Promise<{ success: boolean; message: string | null; error: string | null }> {
        return apiClient(`${API}/vms/${vmId}/checkpoints/${checkpointId}${hostParam(hostId)}`, { method: "DELETE" });
    },

    async getReplication(hostId: number | null = null): Promise<HyperVReplication> {
        return apiClient<HyperVReplication>(`${API}/replication${hostParam(hostId)}`);
    },
};
