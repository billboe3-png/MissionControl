/**
 * Mission Control API Client
 *
 * Sprint:
 * 0.1.1 - Dashboard Foundation
 */

export const API_BASE =
    import.meta.env.VITE_API_URL ?? "/api/v1";

export interface DashboardResponse {
    application: {
        name: string;
        tagline: string;
        version: string;
    };

    generated: string;

    health: {
        backend: {
            status: string;
        };
        database: {
            status: string;
        };
        redis: {
            status: string;
        };
    };

    projects: {
        count: number;
        items: unknown[];
    };

    tasks: {
        count: number;
        items: unknown[];
    };

    notes: {
        count: number;
        items: unknown[];
    };

    resume: unknown;

    parking_lot: {
        count: number;
        items: unknown[];
    };

    integrations: {
        docker: {
            enabled: boolean;
            status: string;
        };

        ssh: {
            enabled: boolean;
            status: string;
        };

        zabbix: {
            enabled: boolean;
            status: string;
        };

        github: {
            enabled: boolean;
            status: string;
        };
    };
}

class ApiClient {
    private async request<T>(endpoint: string): Promise<T> {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                Accept: "application/json",
            },
        });

        if (!response.ok) {
            throw new Error(
                `API request failed (${response.status} ${response.statusText})`
            );
        }

        return response.json() as Promise<T>;
    }

    async getDashboard(): Promise<DashboardResponse> {
        return this.request<DashboardResponse>("/dashboard");
    }
}

export const api = new ApiClient();