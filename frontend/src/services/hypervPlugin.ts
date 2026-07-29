import { apiClient } from "../utils/apiClient";

const PLUGIN_BASE = "/api/v1/plugins/hyperv";

export interface HyperVHost {
    id: number;
    name: string;
    hostname: string;
    transport: string;
    port: number;
    enabled: boolean;
    status: string;
    version: string | null;
    last_sync_at: string | null;
    last_error: string | null;
}

export interface HyperVVM {
    id: number;
    host_id: number;
    vm_id: string;
    name: string;
    state: string;
    cpu_count: number;
    memory_assigned_mb: number;
    uptime_seconds: number;
    host_server: string;
    guest_os: string | null;
    cpu_usage_percent: number;
    last_seen_at: string | null;
}

export interface HyperVNetwork {
    id: number;
    host_id: number;
    switch_id: string;
    name: string;
    switch_type: string;
    allow_management_os: boolean;
    status: string;
    connected_vms: number;
}

export interface HyperVVolume {
    id: number;
    host_id: number;
    disk_id: string;
    name: string;
    path: string;
    size_bytes: number;
    used_bytes: number;
    type: string;
    vm_name: string | null;
}

export interface HyperVCheckpoint {
    id: number;
    host_id: number;
    checkpoint_id: string;
    vm_id: string;
    vm_name: string;
    name: string;
    checkpoint_type: string;
    creation_time: string | null;
    size_bytes: number;
}

export interface HyperVSummary {
    vm_count: number;
    running_count: number;
    stopped_count: number;
    paused_count: number;
    checkpoint_count: number;
    host_count: number;
}

export interface HyperVHealth {
    hosts: Array<{
        id: number;
        name: string;
        status: string;
        last_sync_at: string | null;
        last_error: string | null;
    }>;
    total: number;
    healthy: number;
}

const qp = (params: Record<string, string | number | undefined>) => {
    const s = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== "") s.set(k, String(v));
    });
    const str = s.toString();
    return str ? `?${str}` : "";
};

export const hypervPluginApi = {
    getSummary: (hostId?: number) =>
        apiClient<HyperVSummary>(`${PLUGIN_BASE}/summary${qp({ host_id: hostId })}`),
    listHosts: () => apiClient<HyperVHost[]>(`${PLUGIN_BASE}/hosts`),
    listVms: (hostId?: number) =>
        apiClient<HyperVVM[]>(`${PLUGIN_BASE}/vms${qp({ host_id: hostId })}`),
    listNetworks: (hostId?: number) =>
        apiClient<HyperVNetwork[]>(`${PLUGIN_BASE}/networks${qp({ host_id: hostId })}`),
    listVolumes: (hostId?: number) =>
        apiClient<HyperVVolume[]>(`${PLUGIN_BASE}/volumes${qp({ host_id: hostId })}`),
    listCheckpoints: (hostId?: number, vmId?: string) =>
        apiClient<HyperVCheckpoint[]>(
            `${PLUGIN_BASE}/checkpoints${qp({ host_id: hostId, vm_id: vmId })}`
        ),
    getHealth: (hostId?: number) =>
        apiClient<HyperVHealth>(`${PLUGIN_BASE}/health${qp({ host_id: hostId })}`),
};
