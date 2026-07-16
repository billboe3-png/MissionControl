const API = "/api/v1/remote";

async function handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
        const body = await response.json().catch(() => null);
        const detail = body?.detail;
        throw new Error(detail ?? `Request failed (${response.status})`);
    }
    if (response.status === 204) {
        return undefined as T;
    }
    return response.json();
}

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
        const response = await fetch(`${API}/hosts${params}`);
        return handleResponse<HostListData>(response);
    },

    async get(id: number): Promise<HostData> {
        const response = await fetch(`${API}/hosts/${id}`);
        return handleResponse<HostData>(response);
    },

    async create(data: HostCreateInput): Promise<HostData> {
        const response = await fetch(`${API}/hosts`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        return handleResponse<HostData>(response);
    },

    async update(id: number, data: HostUpdateInput): Promise<HostData> {
        const response = await fetch(`${API}/hosts/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        return handleResponse<HostData>(response);
    },

    async remove(id: number): Promise<void> {
        const response = await fetch(`${API}/hosts/${id}`, {
            method: "DELETE",
        });
        await handleResponse<undefined>(response);
    },
};

export const credentialsApi = {
    async list(): Promise<CredentialListData> {
        const response = await fetch(`${API}/credentials`);
        return handleResponse<CredentialListData>(response);
    },

    async get(id: number): Promise<CredentialData> {
        const response = await fetch(`${API}/credentials/${id}`);
        return handleResponse<CredentialData>(response);
    },

    async create(data: CredentialCreateInput): Promise<CredentialData> {
        const response = await fetch(`${API}/credentials`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        return handleResponse<CredentialData>(response);
    },

    async update(id: number, data: CredentialUpdateInput): Promise<CredentialData> {
        const response = await fetch(`${API}/credentials/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        return handleResponse<CredentialData>(response);
    },

    async remove(id: number): Promise<void> {
        const response = await fetch(`${API}/credentials/${id}`, {
            method: "DELETE",
        });
        await handleResponse<undefined>(response);
    },
};

export const remoteApi = {
    async testConnection(data: TestConnectionRequest): Promise<TestConnectionResponse> {
        const response = await fetch(`${API}/test`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        return handleResponse<TestConnectionResponse>(response);
    },

    async executeCommand(data: ExecuteCommandRequest): Promise<ExecuteCommandResponse> {
        const response = await fetch(`${API}/execute`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        return handleResponse<ExecuteCommandResponse>(response);
    },

    async *executeCommandStream(
        data: ExecuteCommandRequest,
    ): AsyncGenerator<{ type: string; data?: string; message?: string; exit_code?: number }> {
        const response = await fetch(`${API}/execute/stream`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        if (!response.ok) {
            const body = await response.json().catch(() => null);
            throw new Error(body?.detail ?? `Request failed (${response.status})`);
        }
        const reader = response.body!.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
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
        const response = await fetch(`${API}/history${qs ? `?${qs}` : ""}`);
        return handleResponse<HistoryListData>(response);
    },
};
