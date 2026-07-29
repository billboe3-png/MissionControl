import { apiClient } from "../utils/apiClient";

const PLUGIN_BASE = "/api/v1/plugins/zabbix";

export interface ZabbixPluginServer {
    id: number;
    name: string;
    url: string;
    enabled: boolean;
    status: string;
    version: string | null;
    last_sync_at: string | null;
    last_error: string | null;
}

export interface ZabbixPluginHost {
    id: number;
    server_id: number;
    zabbix_hostid: string;
    host: string;
    name: string;
    status: string;
    available: string;
    interface_ip: string | null;
    last_seen_at: string | null;
}

export interface ZabbixPluginProblem {
    id: number;
    server_id: number;
    zabbix_eventid: string;
    name: string;
    severity: string;
    acknowledged: boolean;
    host: string | null;
    timestamp: string | null;
}

export interface ZabbixPluginEvent {
    id: number;
    server_id: number;
    zabbix_eventid: string;
    name: string;
    severity: string;
    status: string;
    host: string | null;
    timestamp: string | null;
}

export interface ZabbixPluginSummary {
    host_count: number;
    available_count: number;
    unavailable_count: number;
    problem_count: number;
    severity_counts: Record<string, number>;
}

export const zabbixPluginApi = {
    listServers: () => apiClient<ZabbixPluginServer[]>(`${PLUGIN_BASE}/servers`),
    listHosts: (serverId?: number) => {
        const params = serverId ? `?server_id=${serverId}` : "";
        return apiClient<ZabbixPluginHost[]>(`${PLUGIN_BASE}/hosts${params}`);
    },
    listProblems: (serverId?: number) => {
        const params = serverId ? `?server_id=${serverId}` : "";
        return apiClient<ZabbixPluginProblem[]>(`${PLUGIN_BASE}/problems${params}`);
    },
    listEvents: (serverId?: number, limit = 50) => {
        const params = new URLSearchParams();
        if (serverId) params.set("server_id", String(serverId));
        params.set("limit", String(limit));
        return apiClient<ZabbixPluginEvent[]>(`${PLUGIN_BASE}/events?${params}`);
    },
    getSummary: (serverId?: number) => {
        const params = serverId ? `?server_id=${serverId}` : "";
        return apiClient<ZabbixPluginSummary>(`${PLUGIN_BASE}/summary${params}`);
    },
};
