const API = "/api/v1/auth";

async function handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
        const body = await response.json().catch(() => null);
        const detail = body?.detail;
        throw new Error(detail ?? `Request failed (${response.status})`);
    }
    return response.json();
}

// ------------------------------------------------------------------ //
// Types                                                               //
// ------------------------------------------------------------------ //

export interface UserInfo {
    id: number;
    email: string;
    display_name: string;
    role: string;
    company_id: number | null;
    site_id: number | null;
    enabled: boolean;
}

export interface LoginResult {
    access_token: string;
    token_type: string;
    user: UserInfo;
}

export interface UserFull {
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

// ------------------------------------------------------------------ //
// Auth context helpers                                                 //
// ------------------------------------------------------------------ //

const TOKEN_KEY = "mc_token";
const USER_KEY = "mc_user";

export function getStoredToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser(): UserInfo | null {
    const raw = localStorage.getItem(USER_KEY);
    if (!raw) return null;
    try { return JSON.parse(raw); } catch { return null; }
}

export function storeAuth(token: string, user: UserInfo): void {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearAuth(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
}

// ------------------------------------------------------------------ //
// API                                                                 //
// ------------------------------------------------------------------ //

export const authApi = {
    async login(email: string, password: string): Promise<LoginResult> {
        const response = await fetch(`${API}/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password }),
        });
        return handleResponse<LoginResult>(response);
    },

    async getMe(token: string): Promise<UserFull> {
        const response = await fetch(`${API}/me`, {
            headers: { Authorization: `Bearer ${token}` },
        });
        return handleResponse<UserFull>(response);
    },

    async listUsers(token: string): Promise<UserFull[]> {
        const response = await fetch(`${API}/users`, {
            headers: { Authorization: `Bearer ${token}` },
        });
        return handleResponse<UserFull[]>(response);
    },

    async createUser(token: string, data: UserCreateInput): Promise<UserFull> {
        const response = await fetch(`${API}/users`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify(data),
        });
        return handleResponse<UserFull>(response);
    },

    async updateUser(token: string, userId: number, data: UserUpdateInput): Promise<UserFull> {
        const response = await fetch(`${API}/users/${userId}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify(data),
        });
        return handleResponse<UserFull>(response);
    },

    async deleteUser(token: string, userId: number): Promise<void> {
        const response = await fetch(`${API}/users/${userId}`, {
            method: "DELETE",
            headers: { Authorization: `Bearer ${token}` },
        });
        await handleResponse<undefined>(response);
    },
};
