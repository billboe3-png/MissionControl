import { apiClient } from "../utils/apiClient";

const API = "/api/v1/plugins/mikrotik";

export interface MikroTikServer {
  id: number;
  name: string;
  host: string;
  ssh_port: number;
  telnet_enabled: boolean;
  telnet_port: number | null;
  username: string;
  api_enabled: boolean;
  api_port: number | null;
  enabled: boolean;
  status: string;
  last_error: string | null;
  version: string | null;
  board_name: string | null;
  cpu_load: string | null;
  memory_usage_pct: number | null;
  uptime: string | null;
  last_sync_at: string | null;
  created_at: string | null;
}

export interface MikroTikInterface {
  name: string;
  type: string | null;
  status: string | null;
  link_status: string | null;
  rx_bytes: number;
  tx_bytes: number;
  rx_packets: number;
  tx_packets: number;
  mac: string | null;
  mtu: number | null;
  last_seen: string | null;
}

export interface MikroTikFirewallRule {
  chain: string;
  action: string | null;
  comment: string | null;
  disabled: boolean;
  bytes: number;
  packets: number;
}

export interface MikroTikDhcpLease {
  address: string | null;
  mac: string;
  host_name: string | null;
  status: string | null;
  expires: string | null;
}

export const mikrotikApi = {
  async listServers(): Promise<MikroTikServer[]> {
    return apiClient<MikroTikServer[]>(`${API}/servers`);
  },

  async getServer(serverId: number): Promise<MikroTikServer> {
    return apiClient<MikroTikServer>(`${API}/servers/${serverId}`);
  },

  async createServer(payload: Partial<MikroTikServer>): Promise<MikroTikServer> {
    return apiClient<MikroTikServer>(`${API}/servers`, {
      method: "POST",
      json: payload,
    });
  },

  async updateServer(serverId: number, payload: Partial<MikroTikServer>): Promise<MikroTikServer> {
    return apiClient<MikroTikServer>(`${API}/servers/${serverId}`, {
      method: "PUT",
      json: payload,
    });
  },

  async deleteServer(serverId: number): Promise<{ success: boolean }> {
    return apiClient<{ success: boolean }>(`${API}/servers/${serverId}`, {
      method: "DELETE",
    });
  },

  async testServer(serverId: number): Promise<{ connected: boolean; version: string; error?: string }> {
    return apiClient(`${API}/servers/${serverId}/test`, { method: "POST" });
  },

  async getInterfaces(serverId: number): Promise<{ success: boolean; interfaces: MikroTikInterface[] }> {
    return apiClient<{ success: boolean; interfaces: MikroTikInterface[] }>(`${API}/servers/${serverId}/interfaces`);
  },

  async getFirewall(serverId: number): Promise<{ success: boolean; rules: MikroTikFirewallRule[] }> {
    return apiClient<{ success: boolean; rules: MikroTikFirewallRule[] }>(`${API}/servers/${serverId}/firewall`);
  },

  async getDhcp(serverId: number): Promise<{ success: boolean; leases: MikroTikDhcpLease[] }> {
    return apiClient<{ success: boolean; leases: MikroTikDhcpLease[] }>(`${API}/servers/${serverId}/dhcp`);
  },

  async getSystem(serverId: number): Promise<{ success: boolean; info: Record<string, string> }> {
    return apiClient<{ success: boolean; info: Record<string, string> }>(`${API}/servers/${serverId}/system`);
  },

  async executeCommand(serverId: number, command: string, telnet = false): Promise<{ success: boolean; output: string }> {
    return apiClient<{ success: boolean; output: string }>(`${API}/servers/${serverId}/execute`, {
      method: "POST",
      json: { command, telnet },
    });
  },

  async backupConfig(serverId: number): Promise<{ success: boolean; message: string }> {
    return apiClient<{ success: boolean; message: string }>(`${API}/servers/${serverId}/backup`, {
      method: "POST",
    });
  },

  getWebfigUrl(serverId: number, path = ""): string {
    return `${API}/servers/${serverId}/webfig/${path}`;
  },
};
