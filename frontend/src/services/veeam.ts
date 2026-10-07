import { apiClient } from "../utils/apiClient";

const API = "/api/v1/plugins/veeam";

function veeamQuery(serverId?: number | null, refresh: boolean = false): string {
    const params = new URLSearchParams();
    if (serverId != null) params.set("server_id", String(serverId));
    if (refresh) params.set("refresh", "true");
    const qs = params.toString();
    return qs ? `?${qs}` : '';
}

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

export interface VeeamJobDailyRun {
    creation_time?: string | null;
    end_time?: string | null;
    result: string;
    processed_bytes: number;
    read_bytes: number;
    stored_bytes: number;
    transferred_bytes?: number;
}

export interface VeeamJobDailyCell {
    processed_bytes: number;
    read_bytes: number;
    stored_bytes: number;
    transferred_bytes: number;
    session_count: number;
    success_count: number;
    warning_count: number;
    failed_count: number;
    result: string;
    runs?: VeeamJobDailyRun[];
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

/**
 * Emitted when the backend answers 404 for the selected server id — the row
 * was deleted (remote host removed / moved to another agent) while the page
 * still held the old id. VeeamServerContext listens for it and reloads the
 * server list so the selection can fall back to a live server.
 */
export const VEEAM_SERVER_MISSING_EVENT = "veeam:server-not-found";

async function veeamClient<T>(path: string, options?: Parameters<typeof apiClient>[1]): Promise<T> {
    try {
        return await apiClient<T>(path, options);
    } catch (err) {
        if (err instanceof Error && err.message === "Veeam server not found") {
            window.dispatchEvent(new CustomEvent(VEEAM_SERVER_MISSING_EVENT));
        }
        throw err;
    }
}

// ── API object ──────────────────────────────────────────────

export const veeamApi = {
    async getSummary(serverId?: number | null, refresh: boolean = false): Promise<VeeamSummary> {
        const qs = veeamQuery(serverId, refresh);
        return veeamClient<VeeamSummary>(`${API}/overview${qs}`);
    },

    async getHealth(serverId?: number | null): Promise<VeeamHealth> {
        const qs = serverId != null ? `?server_id=${serverId}` : '';
        return veeamClient<VeeamHealth>(`${API}/health${qs}`);
    },

    async testConnection(serverId?: number | null): Promise<VeeamConnectionTest> {
        const qs = serverId != null ? `?server_id=${serverId}` : '';
        return veeamClient<VeeamConnectionTest>(`${API}/test${qs}`);
    },

    async listJobs(serverId?: number | null, refresh: boolean = false): Promise<{ jobs: VeeamJob[]; totalCount: number }> {
        const qs = veeamQuery(serverId, refresh);
        const data = await veeamClient<{ jobs: VeeamJob[]; count: number }>(`${API}/jobs${qs}`);
        return { jobs: data.jobs ?? [], totalCount: data.count ?? 0 };
    },

    async getJob(jobId: string): Promise<VeeamJob> {
        const data = await veeamClient<{ job: VeeamJob }>(`${API}/jobs/${jobId}`);
        return data.job;
    },

    async startJob(jobId: string, serverId?: number | null): Promise<VeeamJobAction> {
        const qs = serverId != null ? `?server_id=${serverId}` : '';
        return veeamClient<VeeamJobAction>(`${API}/jobs/${jobId}/start${qs}`, { method: "POST" });
    },

    async stopJob(jobId: string, serverId?: number | null): Promise<VeeamJobAction> {
        const qs = serverId != null ? `?server_id=${serverId}` : '';
        return veeamClient<VeeamJobAction>(`${API}/jobs/${jobId}/stop${qs}`, { method: "POST" });
    },

    async listSessions(serverId?: number | null): Promise<VeeamSession[]> {
        const qs = serverId != null ? `?server_id=${serverId}` : '';
        const data = await veeamClient<{ sessions: VeeamSession[] }>(`${API}/sessions${qs}`);
        return data.sessions ?? [];
    },

    async listRepositories(serverId?: number | null, refresh: boolean = false): Promise<VeeamRepository[]> {
        const qs = veeamQuery(serverId, refresh);
        const data = await veeamClient<{ repositories: VeeamRepository[] }>(`${API}/repositories${qs}`);
        return data.repositories ?? [];
    },

    async listServers(serverId?: number | null): Promise<VeeamManagedServer[]> {
        const qs = serverId != null ? `?server_id=${serverId}` : '';
        const data = await veeamClient<{ servers: VeeamManagedServer[] }>(`${API}/servers${qs}`);
        return data.servers ?? [];
    },

    async listRestorePoints(vmId?: string, serverId?: number | null): Promise<VeeamRestorePoint[]> {
        const sep = vmId ? '&' : '?';
        const sid = serverId != null ? `${sep}server_id=${serverId}` : '';
        const url = vmId ? `${API}/restore-points?vm_id=${vmId}${sid}` : `${API}/restore-points${sid}`;
        const data = await veeamClient<{ restore_points: VeeamRestorePoint[] }>(url);
        return data.restore_points ?? [];
    },

    async getLicense(serverId?: number | null): Promise<VeeamLicense> {
        const qs = serverId != null ? `?server_id=${serverId}` : '';
        return veeamClient<VeeamLicense>(`${API}/license${qs}`);
    },

    async getCapacityTier(serverId?: number | null): Promise<VeeamCapacityTier> {
        const qs = serverId != null ? `?server_id=${serverId}` : '';
        return veeamClient<VeeamCapacityTier>(`${API}/capacity-tier${qs}`);
    },

    async getSessionStats(serverId?: number | null): Promise<VeeamSessionStatsResponse> {
        const qs = serverId != null ? `?server_id=${serverId}` : '';
        return veeamClient<VeeamSessionStatsResponse>(`${API}/sessions/stats${qs}`);
    },

    async getJobStats(serverId?: number | null): Promise<VeeamJobStatsResponse> {
        const qs = serverId != null ? `?server_id=${serverId}` : '';
        return veeamClient<VeeamJobStatsResponse>(`${API}/jobs/stats${qs}`);
    },

    async getJobStatsDaily(
        days: number = 7,
        serverId?: number | null,
        includeSystem: boolean = false,
        refresh: boolean = false,
    ): Promise<VeeamJobStatsDailyResponse> {
        const sid = serverId != null ? `&server_id=${serverId}` : '';
        const ref = refresh ? '&refresh=true' : '';
        return veeamClient<VeeamJobStatsDailyResponse>(
            `${API}/jobs/stats/daily?days=${days}&include_system=${includeSystem}${sid}${ref}`,
        );
    },
};
