const API = "/api/v1/integrations";

export interface IntegrationProfile {
    id: number;
    name: string;
    integration_type: string;
    description: string | null;
    enabled: boolean;
    base_url: string | null;
    username: string | null;
    tenant_id: string | null;
    client_id: string | null;
    authority_url: string | null;
    domain: string | null;
    base_dn: string | null;
    use_ssl: boolean;
    verify_ssl: boolean;
    timeout: number;
    poll_interval: number;
    last_test: string | null;
    last_success: string | null;
    last_error: string | null;
    created_at: string | null;
    updated_at: string | null;
}

export interface IntegrationProfileCreate {
    name: string;
    integration_type: string;
    description?: string;
    enabled?: boolean;
    base_url?: string;
    username?: string;
    password?: string;
    tenant_id?: string;
    client_id?: string;
    client_secret?: string;
    authority_url?: string;
    domain?: string;
    base_dn?: string;
    use_ssl?: boolean;
    verify_ssl?: boolean;
    timeout?: number;
    poll_interval?: number;
}

export type IntegrationProfileUpdate = Partial<IntegrationProfileCreate>;

export interface IntegrationTestResponse {
    success: boolean;
    latency_ms: number | null;
    message: string | null;
    version: string | null;
    error: string | null;
    details: Record<string, unknown> | null;
}

export const integrationsApi = {
    async list(): Promise<IntegrationProfile[]> {
        const response = await fetch(API);
        if (!response.ok) throw new Error("Failed to load integrations");
        const data = await response.json();
        return data.items ?? [];
    },

    async get(id: number): Promise<IntegrationProfile> {
        const response = await fetch(`${API}/${id}`);
        if (!response.ok) throw new Error("Failed to load integration");
        return response.json();
    },

    async create(input: IntegrationProfileCreate): Promise<IntegrationProfile> {
        const response = await fetch(API, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(input),
        });
        if (!response.ok) throw new Error("Failed to create integration");
        return response.json();
    },

    async update(id: number, input: IntegrationProfileUpdate): Promise<IntegrationProfile> {
        const response = await fetch(`${API}/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(input),
        });
        if (!response.ok) throw new Error("Failed to update integration");
        return response.json();
    },

    async remove(id: number): Promise<void> {
        const response = await fetch(`${API}/${id}`, { method: "DELETE" });
        if (!response.ok) throw new Error("Failed to delete integration");
    },

    async test(id: number): Promise<IntegrationTestResponse> {
        const response = await fetch(`${API}/${id}/test`, { method: "POST" });
        if (!response.ok) throw new Error("Connection test failed");
        return response.json();
    },

    async enable(id: number): Promise<IntegrationProfile> {
        const response = await fetch(`${API}/${id}/enable`, { method: "POST" });
        if (!response.ok) throw new Error("Failed to enable integration");
        return response.json();
    },

    async disable(id: number): Promise<IntegrationProfile> {
        const response = await fetch(`${API}/${id}/disable`, { method: "POST" });
        if (!response.ok) throw new Error("Failed to disable integration");
        return response.json();
    },
};
