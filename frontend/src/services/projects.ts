import { apiClient } from "../utils/apiClient";

const API = "/api/v1/projects";

export interface Project {
    id: number;
    name: string;
    description: string | null;
    active: boolean;
    task_count: number;
    note_count: number;
    created_at: string;
    updated_at: string;
}

export interface ProjectListResponse {
    count: number;
    items: Project[];
}

export interface ProjectCreateInput {
    name: string;
    description?: string;
    active?: boolean;
}

export interface ProjectUpdateInput {
    name?: string;
    description?: string;
    active?: boolean;
}

export const projectsApi = {
    async list(): Promise<ProjectListResponse> {
        return apiClient<ProjectListResponse>(API);
    },

    async get(id: number): Promise<Project> {
        return apiClient<Project>(`${API}/${id}`);
    },

    async create(data: ProjectCreateInput): Promise<Project> {
        return apiClient<Project>(API, {
            method: "POST",
            json: data,
        });
    },

    async update(id: number, data: ProjectUpdateInput): Promise<Project> {
        return apiClient<Project>(`${API}/${id}`, {
            method: "PUT",
            json: data,
        });
    },

    async close(id: number): Promise<void> {
        return apiClient<void>(`${API}/${id}/close`, {
            method: "POST",
        });
    },

    async remove(id: number): Promise<void> {
        return apiClient<void>(`${API}/${id}`, {
            method: "DELETE",
        });
    },
};
