import { apiClient } from "../utils/apiClient";

const PLUGIN_BASE = "/api/v1/plugins/unifi";

export interface UniFiController {
    id: number;
    name: string;
    url: string;
    controller_type: string;
    enabled: boolean;
    organization_name: string | null;
    version: string | null;
    status: string;
    last_sync_at: string | null;
    last_error: string | null;
}

export interface UniFiSite {
    id: number;
    controller_id: number;
    unifi_id: string;
    name: string;
    description: string | null;
    timezone: string | null;
    isp_name: string | null;
    wan_status: string;
    num_devices: number;
    num_clients: number;
}

export interface UniFiDevice {
    id: number;
    controller_id: number;
    site_id: string;
    unifi_id: string;
    name: string;
    model: string;
    serial: string | null;
    mac_address: string | null;
    ip_address: string | null;
    firmware_version: string | null;
    adoption_state: string;
    status: string;
    uptime_seconds: number;
    cpu_utilization: number;
    memory_utilization: number;
    temperature_c: number;
    device_type: string;
    last_seen_at: string | null;
}

export interface UniFiClient {
    id: number;
    controller_id: number;
    site_id: string;
    unifi_id: string;
    hostname: string | null;
    mac_address: string;
    ip_address: string | null;
    vlan: string | null;
    connected_ap_name: string | null;
    connected_switch_name: string | null;
    rx_bytes: number;
    tx_bytes: number;
    is_wired: boolean;
    is_guest: boolean;
    last_seen_at: string | null;
}

export interface UniFiAlert {
    id: number;
    controller_id: number;
    site_id: string;
    unifi_id: string;
    severity: string;
    device_name: string | null;
    device_id: string | null;
    message: string;
    timestamp: string | null;
    is_acknowledged: boolean;
}

export interface UniFiWirelessNetwork {
    id: number;
    controller_id: number;
    site_id: string;
    unifi_id: string;
    ssid: string;
    security: string;
    vlan: string | null;
    is_guest: boolean;
    is_hidden: boolean;
    has_alerts: boolean;
}

export interface UniFiSummary {
    controller_count: number;
    controllers_healthy: number;
    site_count: number;
    device_count: number;
    online_devices: number;
    offline_devices: number;
    client_count: number;
    alert_count: number;
    unacknowledged_alerts: number;
    wireless_network_count: number;
    ap_count: number;
    online_ap: number;
    switch_count: number;
    online_switch: number;
    gateway_count: number;
    online_gateway: number;
}

const qp = (params: Record<string, string | number | undefined>) => {
    const s = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== "") s.set(k, String(v));
    });
    const str = s.toString();
    return str ? `?${str}` : "";
};

export const unifiPluginApi = {
    getSummary: () => apiClient<UniFiSummary>(`${PLUGIN_BASE}/summary`),
    listControllers: () => apiClient<UniFiController[]>(`${PLUGIN_BASE}/controllers`),
    listSites: (controllerId?: number) =>
        apiClient<UniFiSite[]>(`${PLUGIN_BASE}/sites${qp({ controller_id: controllerId })}`),
    listDevices: (controllerId?: number, siteId?: string, deviceType?: string) =>
        apiClient<UniFiDevice[]>(
            `${PLUGIN_BASE}/devices${qp({ controller_id: controllerId, site_id: siteId, device_type: deviceType })}`,
        ),
    listClients: (controllerId?: number, siteId?: string) =>
        apiClient<UniFiClient[]>(`${PLUGIN_BASE}/clients${qp({ controller_id: controllerId, site_id: siteId })}`),
    listAlerts: (controllerId?: number, siteId?: string) =>
        apiClient<UniFiAlert[]>(`${PLUGIN_BASE}/alerts${qp({ controller_id: controllerId, site_id: siteId })}`),
    listWireless: (controllerId?: number, siteId?: string) =>
        apiClient<UniFiWirelessNetwork[]>(
            `${PLUGIN_BASE}/wireless${qp({ controller_id: controllerId, site_id: siteId })}`,
        ),
    listSwitches: (controllerId?: number) =>
        apiClient<UniFiDevice[]>(`${PLUGIN_BASE}/switches${qp({ controller_id: controllerId })}`),
    listGateways: (controllerId?: number) =>
        apiClient<UniFiDevice[]>(`${PLUGIN_BASE}/gateways${qp({ controller_id: controllerId })}`),
    listAccessPoints: (controllerId?: number) =>
        apiClient<UniFiDevice[]>(`${PLUGIN_BASE}/access-points${qp({ controller_id: controllerId })}`),
    getDevicesByStatus: () =>
        apiClient<Record<string, number>>(`${PLUGIN_BASE}/devices-by-status`),
    getDevicesByType: () =>
        apiClient<Record<string, number>>(`${PLUGIN_BASE}/devices-by-type`),
    getHealth: () => apiClient<Record<string, unknown>>(`${PLUGIN_BASE}/health`),
};
