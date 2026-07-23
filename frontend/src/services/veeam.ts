import { apiClient } from "../utils/apiClient";

const API = "/api/v1/veeam";

// ── Interfaces ──────────────────────────────────────────────

export interface VeeamSummary {
    success: boolean;
    version: string | null;
    name: string | null;
    total_jobs: number;
    running_jobs: number;
    total_repositories: number;
    total_space_bytes: number;
    used_space_bytes: number;
    recent_sessions: number;
    sessions_success: number;
    sessions_warning: number;
    sessions_failed: number;
    error: string | null;
}

export interface VeeamJob {
    id: string;
    name: string;
    type: string;
    state: string;
    enabled: boolean;
    schedule: {
        kind: string;
    } | null;
    nextRunTime: string | null;
    lastRun: {
        id: string;
        state: string;
        result: { result: string; message: string } | null;
        creationTime: string;
        endTime: string | null;
        progressPercent: number;
    } | null;
    includedObjects: {
        objectsInJob: number;
    } | null;
}

export interface VeeamSession {
    id: string;
    jobId: string;
    name: string;
    sessionType: string;
    state: string;
    result: {
        result: string;
        message: string;
        isCanceled: boolean;
    } | null;
    creationTime: string | null;
    endTime: string | null;
    progressPercent: number;
    platformName?: string;
    resourceId?: string;
    resourceReference?: string;
}

export interface VeeamSessionStat {
    session_id: string;
    job_id: string;
    job_name: string;
    creation_time: string;
    end_time: string;
    state: string;
    processed_bytes: number;
    read_bytes: number;
    transferred_bytes: number;
}

export interface VeeamSessionStatsResponse {
    success: boolean;
    stats: VeeamSessionStat[];
    server_names?: string[];
    ssh_available: boolean;
    count: number;
    message: string | null;
    error: string | null;
}

export interface VeeamJobStat {
    job_name: string;
    session_count: number;
    total_bytes: number;
    processed_bytes: number;
    read_bytes: number;
    stored_bytes: number;
    avg_speed: number;
    last_run: string;
    success_count: number;
    warning_count: number;
    failed_count: number;
}

export interface VeeamJobStatsResponse {
    success: boolean;
    jobs: VeeamJobStat[];
    ssh_available: boolean;
    count: number;
    message: string | null;
    error: string | null;
}

export interface VeeamJobDailyCell {
    processed_bytes: number;
    read_bytes: number;
    stored_bytes: number;
    session_count: number;
    success_count: number;
    warning_count: number;
    failed_count: number;
    result: string;
}

export interface VeeamJobDailyRow {
    job_name: string;
    server_name?: string;
    daily: Record<string, VeeamJobDailyCell>;
}

export interface VeeamJobStatsDailyResponse {
    success: boolean;
    jobs: VeeamJobDailyRow[];
    dates: string[];
    server_names?: string[];
    ssh_available: boolean;
    count: number;
    message: string | null;
    error: string | null;
}

export interface VeeamRepository {
    id: string;
    name: string;
    type: string;
    description: string;
    repository: {
        path: string;
        capacityBytes?: number;
        usedSpaceBytes?: number;
        freeSpaceBytes?: number;
    };
    hostId: string;
    status?: string;
}

export interface VeeamManagedServer {
    id: string;
    name: string;
    type: string;
    status: string;
    description: string;
    server_name?: string;
    credentialsStorageType?: string;
}

export interface VeeamRestorePoint {
    id: string;
    vm_id: string;
    vm_name: string;
    type: string;
    creation_time: string | null;
    size_bytes: number;
    point_type: string;
}

export interface VeeamLicense {
    success: boolean;
    license: {
        status: string;
        type: string;
        expirationDate: string;
        socketCount: number;
        usedSockets: number;
        instanceCount: number;
        usedInstances: number;
    } | null;
    error: string | null;
}

export interface VeeamHealth {
    healthy: boolean;
    version: string | null;
    name: string | null;
    error: string | null;
}

export interface VeeamConnectionTest {
    connected: boolean;
    version: string | null;
    name: string | null;
    server_id: string | null;
    error: string | null;
}

export interface VeeamJobAction {
    success: boolean;
    message: string | null;
    error: string | null;
}

export interface VeeamObjectStorage {
    id: string;
    name: string;
    type: string;
    bucket: string;
    region: string;
    used_bytes: number;
    status: string;
}

export interface VeeamCapacityTier {
    success: boolean;
    object_storages: VeeamObjectStorage[];
    count: number;
    error: string | null;
}

// ── Helpers ─────────────────────────────────────────────────

export function formatBytes(bytes: number): string {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB", "TB", "PB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

// ── API object ──────────────────────────────────────────────

export const veeamApi = {
    async getSummary(): Promise<VeeamSummary> {
        return apiClient<VeeamSummary>(`${API}/overview`);
    },

    async getHealth(): Promise<VeeamHealth> {
        return apiClient<VeeamHealth>(`${API}/health`);
    },

    async testConnection(): Promise<VeeamConnectionTest> {
        return apiClient<VeeamConnectionTest>(`${API}/test`);
    },

    async listJobs(): Promise<{ jobs: VeeamJob[]; totalCount: number }> {
        const data = await apiClient<{ jobs: VeeamJob[]; count: number }>(`${API}/jobs`);
        return { jobs: data.jobs ?? [], totalCount: data.count ?? 0 };
    },

    async getJob(jobId: string): Promise<VeeamJob> {
        const data = await apiClient<{ job: VeeamJob }>(`${API}/jobs/${jobId}`);
        return data.job;
    },

    async startJob(jobId: string): Promise<VeeamJobAction> {
        return apiClient<VeeamJobAction>(`${API}/jobs/${jobId}/start`, { method: "POST" });
    },

    async stopJob(jobId: string): Promise<VeeamJobAction> {
        return apiClient<VeeamJobAction>(`${API}/jobs/${jobId}/stop`, { method: "POST" });
    },

    async listSessions(): Promise<VeeamSession[]> {
        const data = await apiClient<{ sessions: VeeamSession[] }>(`${API}/sessions`);
        return data.sessions ?? [];
    },

    async listRepositories(): Promise<VeeamRepository[]> {
        const data = await apiClient<{ repositories: VeeamRepository[] }>(`${API}/repositories`);
        return data.repositories ?? [];
    },

    async listServers(): Promise<VeeamManagedServer[]> {
        const data = await apiClient<{ servers: VeeamManagedServer[] }>(`${API}/servers`);
        return data.servers ?? [];
    },

    async listRestorePoints(vmId?: string): Promise<VeeamRestorePoint[]> {
        const url = vmId ? `${API}/restore-points?vm_id=${vmId}` : `${API}/restore-points`;
        const data = await apiClient<{ restore_points: VeeamRestorePoint[] }>(url);
        return data.restore_points ?? [];
    },

    async getLicense(): Promise<VeeamLicense> {
        return apiClient<VeeamLicense>(`${API}/license`);
    },

    async getCapacityTier(): Promise<VeeamCapacityTier> {
        return apiClient<VeeamCapacityTier>(`${API}/capacity-tier`);
    },

    async getSessionStats(): Promise<VeeamSessionStatsResponse> {
        return apiClient<VeeamSessionStatsResponse>(`${API}/sessions/stats`);
    },

    async getJobStats(): Promise<VeeamJobStatsResponse> {
        return apiClient<VeeamJobStatsResponse>(`${API}/jobs/stats`);
    },

    async getJobStatsDaily(days: number = 7): Promise<VeeamJobStatsDailyResponse> {
        return apiClient<VeeamJobStatsDailyResponse>(`${API}/jobs/stats/daily?days=${days}`);
    },
};
