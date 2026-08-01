import { apiClient } from "../utils/apiClient";

const API = "/api/v1/resume";

export interface Resume {
    id: number;
    title: string;
    description: string | null;
    available: boolean;
    created_at: string;
    updated_at: string;
}

export interface ResumeListResponse {
    count: number;
    items: Resume[];
}

export interface ResumeCreateInput {
    title: string;
    description?: string;
    available?: boolean;
}

export interface ResumeUpdateInput {
    title?: string;
    description?: string;
    available?: boolean;
}

export const resumesApi = {
    async list(): Promise<ResumeListResponse> {
        return apiClient<ResumeListResponse>(API);
    },

    async get(id: number): Promise<Resume> {
        return apiClient<Resume>(`${API}/${id}`);
    },

    async create(data: ResumeCreateInput): Promise<Resume> {
        return apiClient<Resume>(API, {
            method: "POST",
            json: data,
        });
    },

    async update(id: number, data: ResumeUpdateInput): Promise<Resume> {
        return apiClient<Resume>(`${API}/${id}`, {
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
