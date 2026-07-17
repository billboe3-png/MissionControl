import { apiClient } from "../utils/apiClient";

const API = "/api/v1/auth";

export interface UserData {
    id: number;
    email: string;
    display_name: string;
    role: string;
    company_id: number | null;
    site_id: number | null;
    enabled: boolean;
    last_login: string | null;
    created_at: string | null;
}

export interface UserCreateInput {
    email: string;
    display_name: string;
    password: string;
    role?: string;
    company_id?: number | null;
    site_id?: number | null;
}

export interface UserUpdateInput {
    display_name?: string;
    role?: string;
    enabled?: boolean;
    company_id?: number | null;
    site_id?: number | null;
}

export const usersApi = {
    async list(): Promise<UserData[]> {
        return apiClient<UserData[]>(`${API}/users`);
    },

    async create(data: UserCreateInput): Promise<UserData> {
        return apiClient<UserData>(`${API}/users`, {
            method: "POST",
            json: data,
        });
    },

    async update(userId: number, data: UserUpdateInput): Promise<UserData> {
        return apiClient<UserData>(`${API}/users/${userId}`, {
            method: "PUT",
            json: data,
        });
    },

    async remove(userId: number): Promise<void> {
        return apiClient<void>(`${API}/users/${userId}`, {
            method: "DELETE",
        });
    },
};
