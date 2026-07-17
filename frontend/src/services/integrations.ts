import { apiClient } from "../utils/apiClient";

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
        const data = await apiClient<{ items: IntegrationProfile[] }>(API);
        return data.items ?? [];
    },

    async get(id: number): Promise<IntegrationProfile> {
        return apiClient<IntegrationProfile>(`${API}/${id}`);
    },

    async create(input: IntegrationProfileCreate): Promise<IntegrationProfile> {
        return apiClient<IntegrationProfile>(API, {
            method: "POST",
            json: input,
        });
    },

    async update(id: number, input: IntegrationProfileUpdate): Promise<IntegrationProfile> {
        return apiClient<IntegrationProfile>(`${API}/${id}`, {
            method: "PUT",
            json: input,
        });
    },

    async remove(id: number): Promise<void> {
        return apiClient<void>(`${API}/${id}`, { method: "DELETE" });
    },

    async test(id: number): Promise<IntegrationTestResponse> {
        return apiClient<IntegrationTestResponse>(`${API}/${id}/test`, { method: "POST" });
    },

    async enable(id: number): Promise<IntegrationProfile> {
        return apiClient<IntegrationProfile>(`${API}/${id}/enable`, { method: "POST" });
    },

    async disable(id: number): Promise<IntegrationProfile> {
        return apiClient<IntegrationProfile>(`${API}/${id}/disable`, { method: "POST" });
    },
};
