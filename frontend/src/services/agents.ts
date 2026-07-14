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
    created_at: string | null;
    updated_at: string | null;
    registered_at: string | null;
}

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
    enabled?: boolean;
    tags?: string | null;
    notes?: string | null;
    heartbeat_interval?: number;
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
        const response = await fetch(API);
        if (!response.ok) throw new Error("Failed to load agents");
        return response.json();
    },

    async get(id: number): Promise<Agent> {
        const response = await fetch(`${API}/${id}`);
        if (!response.ok) throw new Error("Failed to load agent");
        return response.json();
    },

    async update(id: number, data: AgentUpdate): Promise<Agent> {
        const response = await fetch(`${API}/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        if (!response.ok) throw new Error("Failed to update agent");
        return response.json();
    },

    async remove(id: number): Promise<void> {
        const response = await fetch(`${API}/${id}`, {
            method: "DELETE",
        });
        if (!response.ok) throw new Error("Failed to delete agent");
    },

    async enable(id: number): Promise<Agent> {
        const response = await fetch(`${API}/${id}/enable`, {
            method: "POST",
        });
        if (!response.ok) throw new Error("Failed to enable agent");
        return response.json();
    },

    async disable(id: number): Promise<Agent> {
        const response = await fetch(`${API}/${id}/disable`, {
            method: "POST",
        });
        if (!response.ok) throw new Error("Failed to disable agent");
        return response.json();
    },

    async execute(
        agentId: number,
        command: AgentDispatchCommand
    ): Promise<AgentCommand> {
        const response = await fetch(`${API}/${agentId}/execute`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(command),
        });
        if (!response.ok)
            throw new Error("Failed to dispatch command");
        return response.json();
    },

    async getCommands(
        agentId: number,
        limit: number = 50
    ): Promise<AgentCommandListResponse> {
        const response = await fetch(
            `${API}/${agentId}/commands?limit=${limit}`
        );
        if (!response.ok)
            throw new Error("Failed to load commands");
        return response.json();
    },

    async getAllCommands(
        limit: number = 100
    ): Promise<AgentCommandListResponse> {
        const response = await fetch(
            `${API}/commands/all?limit=${limit}`
        );
        if (!response.ok)
            throw new Error("Failed to load commands");
        return response.json();
    },

    async getInventory(agentId: number): Promise<AgentInventory> {
        const response = await fetch(
            `${API}/${agentId}/inventory`
        );
        if (!response.ok)
            throw new Error("Failed to load inventory");
        return response.json();
    },
};
