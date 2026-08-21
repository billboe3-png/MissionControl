import { apiClient } from "../utils/apiClient";

const API = "/api/v1/remote";

// ------------------------------------------------------------------ //
// Host Types                                                          //
// ------------------------------------------------------------------ //

export interface HostCreateInput {
    name: string;
    hostname: string;
    ip_address?: string;
    operating_system?: string;
    connection_type?: string;
    port?: number;
    enabled?: boolean;
    credential_profile_id?: number | null;
}

export interface HostUpdateInput {
    name?: string;
    hostname?: string;
    ip_address?: string;
    operating_system?: string;
    connection_type?: string;
    port?: number;
    enabled?: boolean;
    credential_profile_id?: number | null;
}

export interface HostData {
    id: number;
    name: string;
    hostname: string;
    ip_address: string | null;
    operating_system: string | null;
    connection_type: string;
    port: number;
    enabled: boolean;
    credential_profile_id: number | null;
    credential_profile_name: string | null;
    created_at: string;
    updated_at: string;
}

export interface HostListData {
    count: number;
    items: HostData[];
}

// ------------------------------------------------------------------ //
// Credential Profile Types                                            //
// ------------------------------------------------------------------ //

export interface CredentialCreateInput {
    name: string;
    authentication_type?: string;
    username: string;
    password?: string;
    ssh_key?: string;
    passphrase?: string;
    description?: string;
}

export interface CredentialUpdateInput {
    name?: string;
    authentication_type?: string;
    username?: string;
    password?: string;
    ssh_key?: string;
    passphrase?: string;
    description?: string;
}

export interface CredentialData {
    id: number;
    name: string;
    authentication_type: string;
    username: string;
    description: string | null;
    created_at: string;
    updated_at: string;
}

export interface CredentialListData {
    count: number;
    items: CredentialData[];
}

// ------------------------------------------------------------------ //
// Command Types                                                       //
// ------------------------------------------------------------------ //

export interface TestConnectionRequest {
    host_id: number;
}

export interface TestConnectionResponse {
    success: boolean;
    latency_ms: number;
    message: string;
    host: string;
    connection_type: string;
    timestamp: string;
}

export interface ExecuteCommandRequest {
    host_id: number;
    command: string;
    shell?: string;
    agent_id?: number;
}

export interface ExecuteCommandResponse {
    host: string;
    connection_type: string;
    command: string;
    stdout: string;
    stderr: string;
    exit_code: number;
    success: boolean;
    duration_ms: number;
    timestamp: string;
}

export interface CommandHistoryData {
    id: number;
    host_id: number;
    host_name: string | null;
    command: string;
    shell: string;
    stdout: string | null;
    stderr: string | null;
    exit_code: number | null;
    success: boolean;
    duration_ms: number | null;
    started_at: string;
    completed_at: string | null;
    executed_by: string | null;
}

export interface HistoryListData {
    count: number;
    items: CommandHistoryData[];
}

// ------------------------------------------------------------------ //
// API Functions                                                       //
// ------------------------------------------------------------------ //

export const hostsApi = {
    async list(search?: string): Promise<HostListData> {
        const params = search ? `?search=${encodeURIComponent(search)}` : "";
        return apiClient<HostListData>(`${API}/hosts${params}`);
    },

    async get(id: number): Promise<HostData> {
        return apiClient<HostData>(`${API}/hosts/${id}`);
    },

    async create(data: HostCreateInput): Promise<HostData> {
        return apiClient<HostData>(`${API}/hosts`, {
            method: "POST",
            json: data,
        });
    },

    async update(id: number, data: HostUpdateInput): Promise<HostData> {
        return apiClient<HostData>(`${API}/hosts/${id}`, {
            method: "PUT",
            json: data,
        });
    },

    async remove(id: number): Promise<void> {
        return apiClient<void>(`${API}/hosts/${id}`, {
            method: "DELETE",
        });
    },
};

export const credentialsApi = {
    async list(): Promise<CredentialListData> {
        return apiClient<CredentialListData>(`${API}/credentials`);
    },

    async get(id: number): Promise<CredentialData> {
        return apiClient<CredentialData>(`${API}/credentials/${id}`);
    },

    async create(data: CredentialCreateInput): Promise<CredentialData> {
        return apiClient<CredentialData>(`${API}/credentials`, {
            method: "POST",
            json: data,
        });
    },

    async update(id: number, data: CredentialUpdateInput): Promise<CredentialData> {
        return apiClient<CredentialData>(`${API}/credentials/${id}`, {
            method: "PUT",
            json: data,
        });
    },

    async remove(id: number): Promise<void> {
        return apiClient<void>(`${API}/credentials/${id}`, {
            method: "DELETE",
        });
    },
};

export const remoteApi = {
    async testConnection(data: TestConnectionRequest): Promise<TestConnectionResponse> {
        return apiClient<TestConnectionResponse>(`${API}/test`, {
            method: "POST",
            json: data,
        });
    },

    async executeCommand(data: ExecuteCommandRequest): Promise<ExecuteCommandResponse> {
        return apiClient<ExecuteCommandResponse>(`${API}/execute`, {
            method: "POST",
            json: data,
        });
    },

    async *executeCommandStream(
        data: ExecuteCommandRequest,
        signal?: AbortSignal,
    ): AsyncGenerator<{ type: string; data?: string; message?: string; exit_code?: number }> {
        const token = localStorage.getItem("mc_token");
        const headers: Record<string, string> = { "Content-Type": "application/json" };
        if (token) headers["Authorization"] = `Bearer ${token}`;
        const response = await fetch(`${API}/execute/stream`, {
            method: "POST",
            headers,
            body: JSON.stringify(data),
            signal,
        });
        if (!response.ok) {
            const body = await response.json().catch(() => null);
            throw new Error(body?.detail ?? `Request failed (${response.status})`);
        }
        const reader = response.body!.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        try {
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop()!;
                for (const line of lines) {
                    if (line.startsWith("data: ")) {
                        try {
                            yield JSON.parse(line.slice(6));
                        } catch { /* skip malformed */ }
                    }
                }
            }
        } catch (e: unknown) {
            if (e instanceof DOMException && e.name === "AbortError") {
                yield { type: "exit", exit_code: 130, message: "Cancelled" };
                return;
            }
            throw e;
        }
    },

    async getHistory(
        search?: string,
        hostId?: number,
        success?: boolean,
        limit?: number
    ): Promise<HistoryListData> {
        const params = new URLSearchParams();
        if (search) params.set("search", search);
        if (hostId !== undefined) params.set("host_id", String(hostId));
        if (success !== undefined) params.set("success", String(success));
        if (limit !== undefined) params.set("limit", String(limit));
        const qs = params.toString();
        return apiClient<HistoryListData>(`${API}/history${qs ? `?${qs}` : ""}`);
    },
};
