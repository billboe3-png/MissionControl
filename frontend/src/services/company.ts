import { apiClient } from "../utils/apiClient";

const API = "/api/v1/companies";

// ------------------------------------------------------------------ //
// Types                                                               //
// ------------------------------------------------------------------ //

export interface CompanyData {
    id: number;
    uuid: string;
    name: string;
    display_name: string;
    status: string;
    license_type: string | null;
    max_sites: number;
    max_agents: number;
    max_users: number;
    primary_contact: string | null;
    contact_email: string | null;
    contact_phone: string | null;
    timezone: string | null;
    logo_url: string | null;
    theme: string | null;
    notes: string | null;
    enabled: boolean;
    is_global: boolean;
    site_count: number;
    agent_count: number;
    integration_count: number;
    created_at: string | null;
    updated_at: string | null;
}

export interface CompanyListData {
    count: number;
    items: CompanyData[];
}

export interface CompanyCreateInput {
    name: string;
    display_name: string;
    status?: string;
    license_type?: string;
    max_sites?: number;
    max_agents?: number;
    max_users?: number;
    primary_contact?: string;
    contact_email?: string;
    contact_phone?: string;
    timezone?: string;
    logo_url?: string;
    theme?: string;
    notes?: string;
    enabled?: boolean;
}

export interface CompanyUpdateInput {
    name?: string;
    display_name?: string;
    status?: string;
    license_type?: string;
    max_sites?: number;
    max_agents?: number;
    max_users?: number;
    primary_contact?: string;
    contact_email?: string;
    contact_phone?: string;
    timezone?: string;
    logo_url?: string;
    theme?: string;
    notes?: string;
    enabled?: boolean;
}

// ------------------------------------------------------------------ //
// API                                                                 //
// ------------------------------------------------------------------ //

export const companiesApi = {
    async list(): Promise<CompanyData[]> {
        return apiClient<CompanyData[]>(API);
    },

    async listSummary(): Promise<CompanyData[]> {
        return apiClient<CompanyData[]>(`${API}/summary`);
    },

    async get(id: number): Promise<CompanyData> {
        return apiClient<CompanyData>(`${API}/${id}`);
    },

    async create(data: CompanyCreateInput): Promise<CompanyData> {
        return apiClient<CompanyData>(API, {
            method: "POST",
            json: data,
        });
    },

    async update(id: number, data: CompanyUpdateInput): Promise<CompanyData> {
        return apiClient<CompanyData>(`${API}/${id}`, {
            method: "PUT",
            json: data,
        });
    },

    async remove(id: number): Promise<void> {
        return apiClient<void>(`${API}/${id}`, {
            method: "DELETE",
        });
    },
};
