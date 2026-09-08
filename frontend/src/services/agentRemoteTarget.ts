import { apiClient } from "../utils/apiClient";

const API = "/api/v1/agents";

export interface RemoteTarget {
    id: number;
    agent_id: number;
    name: string;
    hostname: string;
    protocol: "psremoting" | "ssh" | "winrm";
    port: number;
    username: string;
    enabled: boolean;
    tags: string | null;
    target_plugins: string | null;
    notes: string | null;
    last_collected_at: string | null;
    last_status: string;
    last_error: string | null;
    created_at: string;
    updated_at: string;
}

export interface RemoteTargetCreate {
    name: string;
    hostname: string;
    protocol: string;
    port?: number;
    username: string;
    password?: string;
    ssh_key?: string;
    enabled?: boolean;
    tags?: string;
    target_plugins?: string;
    notes?: string;
}

export interface RemoteTargetUpdate {
    name?: string;
    hostname?: string;
    protocol?: string;
    port?: number;
    username?: string;
    password?: string;
    ssh_key?: string;
    enabled?: boolean;
    tags?: string;
    target_plugins?: string;
    notes?: string;
}

export interface RemoteInventory {
    agent_id: number;
    agent_name: string;
    hostname: string;
    remote_targets: Record<string, {
        hostname: string;
        protocol: string;
        collected_at: string | null;
        status: string;
        error: string | null;
        inventory: Record<string, unknown>;
    }>;
}

export const agentRemoteTargetApi = {
    async listTargets(agentId: number): Promise<RemoteTarget[]> {
        const data = await apiClient<{ targets: RemoteTarget[] }>(
            `${API}/${agentId}/remote-targets`
        );
        return data.targets ?? [];
    },

    async getTarget(agentId: number, targetId: number): Promise<RemoteTarget> {
        return apiClient<RemoteTarget>(
            `${API}/${agentId}/remote-targets/${targetId}`
        );
    },

    async createTarget(
        agentId: number,
        payload: RemoteTargetCreate
    ): Promise<RemoteTarget> {
        return apiClient<RemoteTarget>(
            `${API}/${agentId}/remote-targets`,
            { method: "POST", json: payload }
        );
    },

    async updateTarget(
        agentId: number,
        targetId: number,
        payload: RemoteTargetUpdate
    ): Promise<RemoteTarget> {
        return apiClient<RemoteTarget>(
            `${API}/${agentId}/remote-targets/${targetId}`,
            { method: "PUT", json: payload }
        );
    },

    async deleteTarget(agentId: number, targetId: number): Promise<void> {
        await apiClient(`${API}/${agentId}/remote-targets/${targetId}`, {
            method: "DELETE",
        });
    },

    async testTarget(
        agentId: number,
        targetId: number
    ): Promise<{ connected: boolean; error?: string; message?: string }> {
        return apiClient(
            `${API}/${agentId}/remote-targets/${targetId}/test`,
            { method: "POST" }
        );
    },

    async getRemoteInventory(agentId: number): Promise<RemoteInventory> {
        return apiClient<RemoteInventory>(
            `${API}/${agentId}/remote-inventory`
        );
    },
};
