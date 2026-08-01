import { apiClient } from "../utils/apiClient";

const API = "/api/v1/agents";

export interface Agent {
    id: number;
    name: string;
    hostname: string;
    status: string;
    operating_system: string | null;
    os_version: string | null;
    ip_address: string | null;
    agent_version: string | null;
    enabled: boolean;
    health: string;
    cpu_percent: number | null;
    memory_percent: number | null;
    disk_percent: number | null;
    last_heartbeat: string | null;
    heartbeat_interval: number;
    tags: string | null;
    notes: string | null;
    active_plugins: string | null;
    enabled_plugins: string | null;
    api_key_masked: string | null;
    created_at: string | null;
    updated_at: string | null;
    registered_at: string | null;
}

export type SiteRecord = {
  timezone?: string | null;
};

export interface AgentListResponse {
    count: number;
    online: number;
    offline: number;
    items: Agent[];
}

export interface AgentCommand {
    id: number;
    agent_id: number;
    command_type: string;
    command: string;
    status: string;
    stdout: string | null;
    stderr: string | null;
    exit_code: number | null;
    success: boolean | null;
    duration_ms: number | null;
    file_path: string | null;
    file_name: string | null;
    error_message: string | null;
    timeout: number;
    requested_by: string | null;
    created_at: string | null;
    started_at: string | null;
    completed_at: string | null;
}

export interface AgentCommandListResponse {
    count: number;
    items: AgentCommand[];
}

export interface AgentInventory {
    agent_id: number;
    agent_name: string;
    hostname: string;
    operating_system: string | null;
    os_version: string | null;
    cpu_percent: number | null;
    memory_percent: number | null;
    disk_percent: number | null;
    inventory: Record<string, unknown> | null;
}

export interface AgentUpdate {
    name?: string;
    hostname?: string;
    operating_system?: string | null;
    os_version?: string | null;
    ip_address?: string | null;
    agent_version?: string | null;
    enabled?: boolean;
    tags?: string | null;
    notes?: string | null;
    heartbeat_interval?: number;
    enabled_plugins?: string | null;
}

export interface AgentDispatchCommand {
    command_type: string;
    command: string;
    timeout?: number;
    file_path?: string;
    file_name?: string;
    file_content_b64?: string;
    requested_by?: string;
}

export const agentsApi = {
    async list(): Promise<AgentListResponse> {
        return apiClient<AgentListResponse>(API);
    },

    async get(id: number): Promise<Agent> {
        return apiClient<Agent>(`${API}/${id}`);
    },

    async update(id: number, data: AgentUpdate): Promise<Agent> {
        return apiClient<Agent>(`${API}/${id}`, {
            method: "PUT",
            json: data,
        });
    },

    async remove(id: number): Promise<void> {
        return apiClient<void>(`${API}/${id}`, {
            method: "DELETE",
        });
    },

    async enable(id: number): Promise<Agent> {
        return apiClient<Agent>(`${API}/${id}/enable`, {
            method: "POST",
        });
    },

    async disable(id: number): Promise<Agent> {
        return apiClient<Agent>(`${API}/${id}/disable`, {
            method: "POST",
        });
    },

    async execute(
        agentId: number,
        command: AgentDispatchCommand
    ): Promise<AgentCommand> {
        return apiClient<AgentCommand>(`${API}/${agentId}/execute`, {
            method: "POST",
            json: command,
        });
    },

    async getCommands(
        agentId: number,
        limit: number = 50
    ): Promise<AgentCommandListResponse> {
        return apiClient<AgentCommandListResponse>(
            `${API}/${agentId}/commands?limit=${limit}`
        );
    },

    async getAllCommands(
        limit: number = 100
    ): Promise<AgentCommandListResponse> {
        return apiClient<AgentCommandListResponse>(
            `${API}/commands/all?limit=${limit}`
        );
    },

    async getInventory(agentId: number): Promise<AgentInventory> {
        return apiClient<AgentInventory>(
            `${API}/${agentId}/inventory`
        );
    },

    async downloadBundle(agentId: number): Promise<Blob> {
        return apiClient<Blob>(
            `${API}/${agentId}/bundles/download`,
            { method: "POST" }
        );
    },

    async create(data: AgentUpdate & { hostname: string }): Promise<Agent> {
        return apiClient<Agent>(API, {
            method: "POST",
            json: data,
        });
    },

    async revealApiKey(agentId: number): Promise<{ api_key: string }> {
        return await apiClient<{ api_key: string }>(`${API}/${agentId}/api-key`);
    },
};

export type AgentUpdateInput = AgentUpdate & { hostname: string; operating_system?: string | null; os_version?: string | null; ip_address?: string | null; agent_version?: string | null };

export const downloadAgentBundle = async (
    agentId: number,
    _platform?: "linux" | "windows",
): Promise<void> => {
    const token = localStorage.getItem("mc_token");
    const headers: Record<string, string> = {};
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }
    const path = agentId && agentId > 0
        ? `/api/v1/agents/${agentId}/bundles/download`
        : `/api/v1/agents/bundles/download`;
    const response = await fetch(path, { method: "POST", headers, credentials: "same-origin", cache: "no-store" });
    if (!response.ok) {
        const detail = await response.json().catch(() => null);
        throw new Error(detail?.detail ?? `Request failed (${response.status})`);
    }
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `mission-control-agent-${agentId > 0 ? agentId : "global"}-${Date.now()}.zip`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
};
