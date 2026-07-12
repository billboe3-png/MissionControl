import { DashboardResponse } from "../types/dashboard";

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
