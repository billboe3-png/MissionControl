const API = "/api/v1/tasks";

export interface TaskCreateInput {
    project_id: number;
    title: string;
    description?: string;
    status?: string;
    priority?: string;
}

export interface TaskUpdateInput {
    project_id?: number;
    title?: string;
    description?: string;
    status?: string;
    priority?: string;
}

export interface TaskData {
    id: number;
    project_id: number;
    title: string;
    description: string | null;
    status: string;
    priority: string;
    created_at: string;
    updated_at: string;
}

export interface TaskListData {
    count: number;
    items: TaskData[];
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

export const tasksApi = {
    async list(): Promise<TaskListData> {
        const response = await fetch(API);
        return handleResponse<TaskListData>(response);
    },

    async create(data: TaskCreateInput): Promise<TaskData> {
        const response = await fetch(API, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        return handleResponse<TaskData>(response);
    },

    async update(id: number, data: TaskUpdateInput): Promise<TaskData> {
        const response = await fetch(`${API}/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        return handleResponse<TaskData>(response);
    },

    async remove(id: number): Promise<void> {
        const response = await fetch(`${API}/${id}`, {
            method: "DELETE",
        });
        await handleResponse<undefined>(response);
    },
};
