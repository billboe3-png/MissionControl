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
    async getDashboard(): Promise<DashboardResponse> {
        return apiClient<DashboardResponse>(`${API}/dashboard`);
    },
    async getSubsystems(): Promise<SubsystemsResponse> {
        return apiClient<SubsystemsResponse>(`${API}/health/subsystems`);
    },
};
