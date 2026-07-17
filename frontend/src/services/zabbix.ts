import { apiClient } from "../utils/apiClient";

const API_BASE = "/api/v1/zabbix";

export interface ZabbixConnectionTestResult {
    connected: boolean;
    latency_ms: number | null;
    message: string | null;
    version: string | null;
    error: string | null;
}

export interface ZabbixSummary {
    connected: boolean;
    version: string;
    server_name: string;
    host_count: number;
    problem_count: number;
    critical_count: number;
    warning_count: number;
    ok_count: number;
    uptime_hours: number;
    api_latency_ms: number;
    error: string | null;
}

export interface ZabbixHost {
    hostid: string;
    host: string;
    name: string;
    status: string;
    available: string;
    interface: string;
    groups: string[];
    templates: string[];
    last_access: string | null;
}

export interface ZabbixHostsResponse {
    connected: boolean;
    hosts: ZabbixHost[];
    total_count: number;
    enabled_count: number;
    disabled_count: number;
    available_count: number;
    unavailable_count: number;
    error: string | null;
}

export interface ZabbixHostGroup {
    groupid: string;
    name: string;
    host_count: number;
}

export interface ZabbixHostGroupsResponse {
    connected: boolean;
    groups: ZabbixHostGroup[];
    total_count: number;
    error: string | null;
}

export interface ZabbixTrigger {
    triggerid: string;
    description: string;
    status: string;
    priority: string;
    value: string;
    hosts: string[];
}

export interface ZabbixTriggersResponse {
    connected: boolean;
    triggers: ZabbixTrigger[];
    total_count: number;
    enabled_count: number;
    disabled_count: number;
    problem_count: number;
    ok_count: number;
    error: string | null;
}

export interface ZabbixProblem {
    eventid: string;
    name: string;
    severity: string;
    status: string;
    acknowledged: boolean;
    host: string;
    timestamp: string;
}

export interface ZabbixProblemsResponse {
    connected: boolean;
    problems: ZabbixProblem[];
    total_count: number;
    severity_counts: Record<string, number>;
    acknowledged_count: number;
    unacknowledged_count: number;
    error: string | null;
}

export interface ZabbixEvent {
    eventid: string;
    name: string;
    severity: string;
    status: string;
    host: string;
    timestamp: string;
}

export interface ZabbixEventsResponse {
    connected: boolean;
    events: ZabbixEvent[];
    total_count: number;
    error: string | null;
}

export interface ZabbixItem {
    itemid: string;
    name: string;
    key_: string;
    status: string;
    type: string;
    last_value: string;
    host: string;
}

export interface ZabbixItemsResponse {
    connected: boolean;
    items: ZabbixItem[];
    total_count: number;
    supported_count: number;
    unsupported_count: number;
    error: string | null;
}

export interface ZabbixTemplate {
    templateid: string;
    name: string;
    hosts_count: number;
}

export interface ZabbixTemplatesResponse {
    connected: boolean;
    templates: ZabbixTemplate[];
    total_count: number;
    error: string | null;
}

export interface ZabbixDashboard {
    dashboardid: string;
    name: string;
    display_name: string;
    owner: string;
    pages: number;
}

export interface ZabbixDashboardsResponse {
    connected: boolean;
    dashboards: ZabbixDashboard[];
    total_count: number;
    error: string | null;
}

export interface ZabbixMap {
    sysmapid: string;
    name: string;
    width: number;
    height: number;
    elements: number;
}

export interface ZabbixMapsResponse {
    connected: boolean;
    maps: ZabbixMap[];
    total_count: number;
    error: string | null;
}

export interface ZabbixDatabaseHealth {
    status: string;
    type: string;
    size_mb: number;
}

export interface ZabbixHealthResponse {
    connected: boolean;
    status: string;
    version: string;
    server: string;
    uptime_hours: number;
    api_latency_ms: number;
    database: ZabbixDatabaseHealth;
    proxy_count: number;
    poller_items_per_sec: number;
    trigger_functions_per_sec: number;
    error: string | null;
}

export const zabbixApi = {
    testConnection: () => apiClient<ZabbixConnectionTestResult>(`${API_BASE}/test`, { method: "POST" }),
    getOverview: () => apiClient<ZabbixSummary>(`${API_BASE}/overview`),
    getHosts: () => apiClient<ZabbixHostsResponse>(`${API_BASE}/hosts`),
    getGroups: () => apiClient<ZabbixHostGroupsResponse>(`${API_BASE}/groups`),
    getTemplates: () => apiClient<ZabbixTemplatesResponse>(`${API_BASE}/templates`),
    getItems: () => apiClient<ZabbixItemsResponse>(`${API_BASE}/items`),
    getTriggers: () => apiClient<ZabbixTriggersResponse>(`${API_BASE}/triggers`),
    getProblems: () => apiClient<ZabbixProblemsResponse>(`${API_BASE}/problems`),
    getEvents: () => apiClient<ZabbixEventsResponse>(`${API_BASE}/events`),
    getMaps: () => apiClient<ZabbixMapsResponse>(`${API_BASE}/maps`),
    getDashboards: () => apiClient<ZabbixDashboardsResponse>(`${API_BASE}/dashboards`),
    getHealth: () => apiClient<ZabbixHealthResponse>(`${API_BASE}/health`),
};
