import { apiClient } from "../utils/apiClient";

const API = "/api/v1/tasks";

export interface Task {
  id: number;
  project_id: number;
  title: string;
  description: string | null;
  status: string;
  priority: string;
  assignee: string | null;
  due_date: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface TaskListResponse {
  count: number;
  items: Task[];
}

export interface TaskCreateInput {
  project_id: number;
  title: string;
  description?: string;
  status?: string;
  priority?: string;
  assignee?: string;
  due_date?: string;
}

export interface TaskUpdateInput {
  project_id?: number;
  title?: string;
  description?: string;
  status?: string;
  priority?: string;
  assignee?: string;
  due_date?: string;
}

export const tasksApi = {
  async list(): Promise<TaskListResponse> {
    return apiClient<TaskListResponse>(API);
  },

  async get(id: number): Promise<Task> {
    return apiClient<Task>(`${API}/${id}`);
  },

  async create(data: TaskCreateInput): Promise<Task> {
    return apiClient<Task>(API, {
      method: "POST",
      json: data,
    });
  },

  async update(id: number, data: TaskUpdateInput): Promise<Task> {
    return apiClient<Task>(`${API}/${id}`, {
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
