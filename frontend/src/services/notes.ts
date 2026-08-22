import { apiClient } from "../utils/apiClient";

const API = "/api/v1/notes";

export interface Note {
  id: number;
  project_id: number;
  title: string;
  content: string;
  updated_at: string;
  created_at: string;
}

export interface NoteListResponse {
  count: number;
  items: Note[];
}

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

export const notesApi = {
  async list(): Promise<NoteListResponse> {
    return apiClient<NoteListResponse>(API);
  },

  async get(id: number): Promise<Note> {
    return apiClient<Note>(`${API}/${id}`);
  },

  async create(data: NoteCreateInput): Promise<Note> {
    return apiClient<Note>(API, {
      method: "POST",
      json: data,
    });
  },

  async update(id: number, data: NoteUpdateInput): Promise<Note> {
    return apiClient<Note>(`${API}/${id}`, {
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
