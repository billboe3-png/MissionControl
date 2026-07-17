import { apiClient } from "../utils/apiClient";

const API = "/api/v1/proxmox";

export interface ProxmoxNode {
    name: string;
    status: string;
    cpu_percent: number;
    memory_total_mb: number;
    memory_used_mb: number;
    disk_total_gb: number;
    disk_used_gb: number;
    uptime_seconds: number;
    version: string;
    ssl_fingerprint: string;
}

export interface ProxmoxVm {
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

export interface ProxmoxLxc {
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
    cpu_usage_percent: number;
    disk_read_mbps: number;
    disk_write_mbps: number;
    network_receive_mbps: number;
    network_send_mbps: number;
    status_message: string;
}

export interface ProxmoxNetwork {
    id: string;
    name: string;
    switch_type: string;
    vlan_id: number | null;
    status: string;
    node: string;
    cidr: string;
    address: string;
    gateway: string | null;
    connected_vms: number;
    type: string;
}

export interface ProxmoxStorage {
    id: string;
    name: string;
    path: string;
    size_bytes: number;
    used_bytes: number;
    type: string;
    status: string;
    content: string;
    node: string;
}

export interface ProxmoxTask {
    id: string;
    node: string;
    type: string;
    user: string;
    status: string;
    start_time: string | null;
    end_time: string | null;
    upid: string;
}

export interface ProxmoxSnapshot {
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

export interface ProxmoxSummary {
    connected: boolean;
    cluster_name: string | null;
    version: string | null;
    nodes_online: number;
    nodes_total: number;
    total_vms: number;
    running: number;
    stopped: number;
    paused: number;
    total_lxc: number;
    running_lxc: number;
    stopped_lxc: number;
    total_cpu: number;
    total_memory_gb: number;
    used_memory_gb: number;
    total_storage_gb: number;
    used_storage_gb: number;
    storage_count: number;
    network_count: number;
    total_snapshots: number;
    error: string | null;
}

export interface ProxmoxHealthNode {
    name: string;
    status: string;
    cpu_percent: number;
    memory_percent: number;
    uptime_seconds: number;
    vm_count: number;
    version: string | null;
}

export interface ProxmoxHealth {
    connected: boolean;
    status: string;
    nodes: ProxmoxHealthNode[];
    cluster_summary: string | null;
    error: string | null;
}

export interface ProxmoxActionResponse {
    success: boolean;
    message: string | null;
    error: string | null;
    vm_name: string | null;
}

export const proxmoxApi = {
    async getSummary(): Promise<ProxmoxSummary> {
        return apiClient<ProxmoxSummary>(`${API}/overview`);
    },

    async getHealth(): Promise<ProxmoxHealth> {
        return apiClient<ProxmoxHealth>(`${API}/health`);
    },

    async testConnection(): Promise<{ connected: boolean; latency_ms: number; message: string | null; hostname: string | null; error: string | null }> {
        return apiClient(`${API}/test`);
    },

    async listNodes(): Promise<ProxmoxNode[]> {
        const data = await apiClient<{ items: ProxmoxNode[] }>(`${API}/nodes`);
        return data.items ?? [];
    },

    async listVms(): Promise<ProxmoxVm[]> {
        const data = await apiClient<{ items: ProxmoxVm[] }>(`${API}/vms`);
        return data.items ?? [];
    },

    async getVm(vmId: string): Promise<ProxmoxVm> {
        const data = await apiClient<{ item: ProxmoxVm }>(`${API}/vms/${vmId}`);
        return data.item;
    },

    async startVm(vmId: string): Promise<ProxmoxActionResponse> {
        return apiClient<ProxmoxActionResponse>(`${API}/vms/${vmId}/start`, { method: "POST" });
    },

    async stopVm(vmId: string, force = false): Promise<ProxmoxActionResponse> {
        return apiClient<ProxmoxActionResponse>(`${API}/vms/${vmId}/stop?force=${force}`, { method: "POST" });
    },

    async restartVm(vmId: string): Promise<ProxmoxActionResponse> {
        return apiClient<ProxmoxActionResponse>(`${API}/vms/${vmId}/restart`, { method: "POST" });
    },

    async pauseVm(vmId: string): Promise<ProxmoxActionResponse> {
        return apiClient<ProxmoxActionResponse>(`${API}/vms/${vmId}/pause`, { method: "POST" });
    },

    async resumeVm(vmId: string): Promise<ProxmoxActionResponse> {
        return apiClient<ProxmoxActionResponse>(`${API}/vms/${vmId}/resume`, { method: "POST" });
    },

    async listLxc(): Promise<ProxmoxLxc[]> {
        const data = await apiClient<{ items: ProxmoxLxc[] }>(`${API}/lxc`);
        return data.items ?? [];
    },

    async getLxc(vmId: string): Promise<ProxmoxLxc> {
        const data = await apiClient<{ item: ProxmoxLxc }>(`${API}/lxc/${vmId}`);
        return data.item;
    },

    async startLxc(vmId: string): Promise<ProxmoxActionResponse> {
        return apiClient<ProxmoxActionResponse>(`${API}/lxc/${vmId}/start`, { method: "POST" });
    },

    async stopLxc(vmId: string): Promise<ProxmoxActionResponse> {
        return apiClient<ProxmoxActionResponse>(`${API}/lxc/${vmId}/stop`, { method: "POST" });
    },

    async listNetworks(): Promise<ProxmoxNetwork[]> {
        const data = await apiClient<{ items: ProxmoxNetwork[] }>(`${API}/networks`);
        return data.items ?? [];
    },

    async listStorage(): Promise<ProxmoxStorage[]> {
        const data = await apiClient<{ items: ProxmoxStorage[] }>(`${API}/storage`);
        return data.items ?? [];
    },

    async listTasks(node?: string): Promise<ProxmoxTask[]> {
        const url = node ? `${API}/tasks?node=${node}` : `${API}/tasks`;
        const data = await apiClient<{ items: ProxmoxTask[] }>(url);
        return data.items ?? [];
    },

    async listSnapshots(vmId?: string): Promise<ProxmoxSnapshot[]> {
        const url = vmId ? `${API}/snapshots?vm_id=${vmId}` : `${API}/snapshots`;
        const data = await apiClient<{ items: ProxmoxSnapshot[] }>(url);
        return data.items ?? [];
    },

    async createSnapshot(vmId: string, name?: string): Promise<{ success: boolean; message: string | null; error: string | null }> {
        return apiClient(`${API}/snapshots`, {
            method: "POST",
            json: { vm_id: vmId, name },
        });
    },

    async deleteSnapshot(vmId: string, snapshotId: string): Promise<{ success: boolean; message: string | null; error: string | null }> {
        return apiClient(`${API}/vms/${vmId}/snapshots/${snapshotId}`, { method: "DELETE" });
    },
};
