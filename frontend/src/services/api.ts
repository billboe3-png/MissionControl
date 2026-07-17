import { DashboardResponse } from "../types/dashboard";
import { apiClient } from "../utils/apiClient";

const API = "/api/v1";

export const api = {
    async getDashboard(): Promise<DashboardResponse> {
        return apiClient<DashboardResponse>(`${API}/dashboard`);
    },
};
