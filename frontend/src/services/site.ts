import { apiClient } from "../utils/apiClient";

const API = "/api/v1/sites";

export interface SiteData {
    id: number;
    name: string;
    code: string;
    company_id: number | null;
    company_name: string | null;
    enabled: boolean;
    is_default: boolean;
}

/** The sites endpoint returns a paginated envelope, not a bare array. */
interface SiteListResponse {
    count: number;
    items: SiteData[];
}

export const sitesApi = {
    async list(): Promise<SiteData[]> {
        const res = await apiClient<SiteListResponse>(API);
        return res?.items ?? [];
    },
};