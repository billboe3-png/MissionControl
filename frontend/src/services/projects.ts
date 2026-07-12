const API = "/api/v1/projects";

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

export interface ProjectData {
    id: number;
    name: string;
    description: string | null;
    active: boolean;
    created_at: string;
    updated_at: string;
}

export interface ProjectListData {
    count: number;
    items: ProjectData[];
}

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

export const projectsApi = {
    async list(): Promise<ProjectListData> {
        const response = await fetch(API);
        return handleResponse<ProjectListData>(response);
    },

    async create(data: ProjectCreateInput): Promise<ProjectData> {
        const response = await fetch(API, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        return handleResponse<ProjectData>(response);
    },

    async update(id: number, data: ProjectUpdateInput): Promise<ProjectData> {
        const response = await fetch(`${API}/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        return handleResponse<ProjectData>(response);
    },

    async remove(id: number): Promise<void> {
        const response = await fetch(`${API}/${id}`, {
            method: "DELETE",
        });
        await handleResponse<undefined>(response);
    },
};
