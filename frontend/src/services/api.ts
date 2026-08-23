import { DashboardResponse } from "../types/dashboard";
import { apiClient } from "../utils/apiClient";

const API = "/api/v1";

export interface SubsystemCheck {
  component: string;
  status: string;
  latency_ms: number;
  last_check: string;
  details?: string;
}

export interface SubsystemsResponse {
  subsystems: Record<string, SubsystemCheck>;
}

export const api = {
    async changePassword(current_password: string, new_password: string): Promise<{status: string}> {
        return apiClient<{status: string}>(`${API}/auth/change-password`, {
            method: "POST",
            json: { current_password, new_password },
        });
    },
    async getDashboard(): Promise<DashboardResponse> {
        return apiClient<DashboardResponse>(`${API}/dashboard`);
    },
    async getSubsystems(): Promise<SubsystemsResponse> {
        return apiClient<SubsystemsResponse>(`${API}/health/subsystems`);
    },
};
