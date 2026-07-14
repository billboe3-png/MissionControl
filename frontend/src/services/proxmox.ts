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
        const response = await fetch(`${API}/overview`);
        if (!response.ok) throw new Error("Failed to load Proxmox overview");
        return response.json();
    },

    async getHealth(): Promise<ProxmoxHealth> {
        const response = await fetch(`${API}/health`);
        if (!response.ok) throw new Error("Failed to load Proxmox health");
        return response.json();
    },

    async testConnection(): Promise<{ connected: boolean; latency_ms: number; message: string | null; hostname: string | null; error: string | null }> {
        const response = await fetch(`${API}/test`);
        if (!response.ok) throw new Error("Connection test failed");
        return response.json();
    },

    async listNodes(): Promise<ProxmoxNode[]> {
        const response = await fetch(`${API}/nodes`);
        if (!response.ok) throw new Error("Failed to load nodes");
        const data = await response.json();
        return data.items ?? [];
    },

    async listVms(): Promise<ProxmoxVm[]> {
        const response = await fetch(`${API}/vms`);
        if (!response.ok) throw new Error("Failed to load VMs");
        const data = await response.json();
        return data.items ?? [];
    },

    async getVm(vmId: string): Promise<ProxmoxVm> {
        const response = await fetch(`${API}/vms/${vmId}`);
        if (!response.ok) throw new Error("Failed to load VM");
        const data = await response.json();
        return data.item;
    },

    async startVm(vmId: string): Promise<ProxmoxActionResponse> {
        const response = await fetch(`${API}/vms/${vmId}/start`, { method: "POST" });
        if (!response.ok) throw new Error("Failed to start VM");
        return response.json();
    },

    async stopVm(vmId: string, force = false): Promise<ProxmoxActionResponse> {
        const response = await fetch(`${API}/vms/${vmId}/stop?force=${force}`, { method: "POST" });
        if (!response.ok) throw new Error("Failed to stop VM");
        return response.json();
    },

    async restartVm(vmId: string): Promise<ProxmoxActionResponse> {
        const response = await fetch(`${API}/vms/${vmId}/restart`, { method: "POST" });
        if (!response.ok) throw new Error("Failed to restart VM");
        return response.json();
    },

    async pauseVm(vmId: string): Promise<ProxmoxActionResponse> {
        const response = await fetch(`${API}/vms/${vmId}/pause`, { method: "POST" });
        if (!response.ok) throw new Error("Failed to suspend VM");
        return response.json();
    },

    async resumeVm(vmId: string): Promise<ProxmoxActionResponse> {
        const response = await fetch(`${API}/vms/${vmId}/resume`, { method: "POST" });
        if (!response.ok) throw new Error("Failed to resume VM");
        return response.json();
    },

    async listLxc(): Promise<ProxmoxLxc[]> {
        const response = await fetch(`${API}/lxc`);
        if (!response.ok) throw new Error("Failed to load LXC containers");
        const data = await response.json();
        return data.items ?? [];
    },

    async getLxc(vmId: string): Promise<ProxmoxLxc> {
        const response = await fetch(`${API}/lxc/${vmId}`);
        if (!response.ok) throw new Error("Failed to load LXC container");
        const data = await response.json();
        return data.item;
    },

    async startLxc(vmId: string): Promise<ProxmoxActionResponse> {
        const response = await fetch(`${API}/lxc/${vmId}/start`, { method: "POST" });
        if (!response.ok) throw new Error("Failed to start LXC container");
        return response.json();
    },

    async stopLxc(vmId: string): Promise<ProxmoxActionResponse> {
        const response = await fetch(`${API}/lxc/${vmId}/stop`, { method: "POST" });
        if (!response.ok) throw new Error("Failed to stop LXC container");
        return response.json();
    },

    async listNetworks(): Promise<ProxmoxNetwork[]> {
        const response = await fetch(`${API}/networks`);
        if (!response.ok) throw new Error("Failed to load networks");
        const data = await response.json();
        return data.items ?? [];
    },

    async listStorage(): Promise<ProxmoxStorage[]> {
        const response = await fetch(`${API}/storage`);
        if (!response.ok) throw new Error("Failed to load storage");
        const data = await response.json();
        return data.items ?? [];
    },

    async listTasks(node?: string): Promise<ProxmoxTask[]> {
        const url = node ? `${API}/tasks?node=${node}` : `${API}/tasks`;
        const response = await fetch(url);
        if (!response.ok) throw new Error("Failed to load tasks");
        const data = await response.json();
        return data.items ?? [];
    },

    async listSnapshots(vmId?: string): Promise<ProxmoxSnapshot[]> {
        const url = vmId ? `${API}/snapshots?vm_id=${vmId}` : `${API}/snapshots`;
        const response = await fetch(url);
        if (!response.ok) throw new Error("Failed to load snapshots");
        const data = await response.json();
        return data.items ?? [];
    },

    async createSnapshot(vmId: string, name?: string): Promise<{ success: boolean; message: string | null; error: string | null }> {
        const response = await fetch(`${API}/snapshots`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ vm_id: vmId, name }),
        });
        if (!response.ok) throw new Error("Failed to create snapshot");
        return response.json();
    },

    async deleteSnapshot(vmId: string, snapshotId: string): Promise<{ success: boolean; message: string | null; error: string | null }> {
        const response = await fetch(`${API}/vms/${vmId}/snapshots/${snapshotId}`, { method: "DELETE" });
        if (!response.ok) throw new Error("Failed to delete snapshot");
        return response.json();
    },
};
