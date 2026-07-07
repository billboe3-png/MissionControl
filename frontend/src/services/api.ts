export interface DashboardResponse {
    application: {
        name: string;
        tagline: string;
        version: string;
    };

    generated: string;

    summary: {
        containers_running: number;
        containers_total: number;
        docker_engine: string;
        projects: number;
        tasks: number;
        notes: number;
        resume_available: boolean;
    };

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

    resume: {
        available: boolean;
        title: string | null;
        description: string | null;
    };

    parking_lot: {
        count: number;
        items: unknown[];
    };

    integrations: {
        docker: {
            engine: string;
            compose: string;
            container_count: number;
            docker_version: string;

            containers: {
                id: string;
                name: string;
                image: string;
                status: string;
            }[];
        };

        ssh: {
            enabled: boolean;
            status: string;
        };

        github: {
            enabled: boolean;
            status: string;
        };

        zabbix: {
            enabled: boolean;
            status: string;
        };
    };
}

const API = "/api/v1";

export const api = {
    async getDashboard(): Promise<DashboardResponse> {
        const response = await fetch(`${API}/dashboard`);

        if (!response.ok) {
            throw new Error("Unable to load dashboard.");
        }

        return response.json();
    },
};