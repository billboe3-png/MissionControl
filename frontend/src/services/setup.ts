import { apiClient } from "../utils/apiClient";

const API = "/api/v1/setup";

export interface SetupStatus {
    setup_required: boolean;
}

export interface BootstrapInput {
    company_name: string;
    company_code?: string;
    site_name: string;
    site_timezone?: string;
    admin_display_name: string;
    admin_email: string;
    admin_password: string;
    admin_confirm_password: string;
}

export interface BootstrapResult {
    company_id: number;
    site_id: number;
    admin_id: number;
    message: string;
}

export const setupApi = {
    async getStatus(): Promise<SetupStatus> {
        return apiClient<SetupStatus>(`${API}/status`);
    },

    async bootstrap(data: BootstrapInput): Promise<BootstrapResult> {
        return apiClient<BootstrapResult>(`${API}/bootstrap`, {
            method: "POST",
            json: data,
        });
    },
};
