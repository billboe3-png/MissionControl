import { apiClient } from "../utils/apiClient";

const PLUGIN_BASE = "/api/v1/plugins/git";

export interface GitRepository {
    id: number;
    name: string;
    path: string;
    remote_url: string | null;
    enabled: boolean;
    status: string;
    last_sync_at: string | null;
    last_error: string | null;
}

export interface GitBranch {
    id: number;
    repo_id: number;
    name: string;
    is_current: boolean;
    is_remote: boolean;
    ahead_of_remote: number;
    behind_remote: number;
    last_commit_id: string | null;
    last_commit_message: string | null;
    last_commit_author: string | null;
    last_commit_date: string | null;
}

export interface GitCommit {
    id: number;
    repo_id: number;
    commit_id: string;
    short_id: string;
    message: string;
    author: string;
    email: string | null;
    date: string;
    branch: string | null;
    is_merge: boolean;
}

export interface GitRemote {
    id: number;
    repo_id: number;
    name: string;
    url: string;
    push_url: string | null;
}

export interface GitSummary {
    repo_count: number;
    branch_count: number;
    commit_count: number;
    remote_count: number;
    dirty_repos: number;
    healthy_repos: number;
}

export interface GitHealth {
    repos: Array<{
        id: number;
        name: string;
        status: string;
        last_sync_at: string | null;
        last_error: string | null;
    }>;
    total: number;
    healthy: number;
}

const qp = (params: Record<string, string | number | undefined>) => {
    const s = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== "") s.set(k, String(v));
    });
    const str = s.toString();
    return str ? `?${str}` : "";
};

export const gitPluginApi = {
    getSummary: () => apiClient<GitSummary>(`${PLUGIN_BASE}/summary`),
    listRepositories: () => apiClient<GitRepository[]>(`${PLUGIN_BASE}/repositories`),
    listBranches: (repoId?: number) =>
        apiClient<GitBranch[]>(`${PLUGIN_BASE}/branches${qp({ repo_id: repoId })}`),
    listCommits: (repoId?: number, limit: number = 50) =>
        apiClient<GitCommit[]>(`${PLUGIN_BASE}/commits${qp({ repo_id: repoId, limit: limit.toString() as any })}`),
    listRemotes: (repoId?: number) =>
        apiClient<GitRemote[]>(`${PLUGIN_BASE}/remotes${qp({ repo_id: repoId })}`),
    getHealth: () => apiClient<GitHealth>(`${PLUGIN_BASE}/health`),
};
