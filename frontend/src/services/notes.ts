const API = "/api/v1/notes";

export interface NoteCreateInput {
    project_id: number;
    title: string;
    content: string;
}

export interface NoteUpdateInput {
    project_id?: number;
    title?: string;
    content?: string;
}

export interface NoteData {
    id: number;
    title: string;
    content: string;
    created_at: string;
    updated_at: string;
}

export interface NoteListData {
    count: number;
    items: NoteData[];
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

export const notesApi = {
    async list(): Promise<NoteListData> {
        const response = await fetch(API);
        return handleResponse<NoteListData>(response);
    },

    async create(data: NoteCreateInput): Promise<NoteData> {
        const response = await fetch(API, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        return handleResponse<NoteData>(response);
    },

    async update(id: number, data: NoteUpdateInput): Promise<NoteData> {
        const response = await fetch(`${API}/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        return handleResponse<NoteData>(response);
    },

    async remove(id: number): Promise<void> {
        const response = await fetch(`${API}/${id}`, {
            method: "DELETE",
        });
        await handleResponse<undefined>(response);
    },
};
