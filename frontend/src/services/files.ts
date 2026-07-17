import { apiClient } from "../utils/apiClient";

const API = "/api/v1/remote/files";

export interface FileListItem {
    name: string;
    path: string;
    is_directory: boolean;
    size_bytes: number | null;
    modified_at: string | null;
    permissions: string | null;
}

export interface FileListResponse {
    path: string;
    items: FileListItem[];
}

export interface FileTransferResponse {
    success: boolean;
    message: string;
    remote_path: string;
    size_bytes?: number | null;
}

export interface FileDownloadResponse extends FileTransferResponse {
    content_base64?: string | null;
}

export interface SessionMetricsResponse {
    active_ssh_sessions: number;
    active_winrm_sessions: number;
    connection_pool_size: number;
    connection_pool_used: number;
    average_latency_ms: number;
    total_commands_executed: number;
    total_commands_failed: number;
    last_activity: string | null;
}

export const filesApi = {
    async list(hostId: number, path: string): Promise<FileListResponse> {
        return apiClient<FileListResponse>(
            `${API}/list?host_id=${hostId}&path=${encodeURIComponent(path)}`
        );
    },

    async upload(
        hostId: number,
        remotePath: string,
        content: string
    ): Promise<FileTransferResponse> {
        return apiClient<FileTransferResponse>(`${API}/upload`, {
            method: "POST",
            json: {
                host_id: hostId,
                remote_path: remotePath,
                content_base64: content,
            },
        });
    },

    async download(
        hostId: number,
        remotePath: string
    ): Promise<FileDownloadResponse> {
        return apiClient<FileDownloadResponse>(`${API}/download`, {
            method: "POST",
            json: {
                host_id: hostId,
                remote_path: remotePath,
            },
        });
    },

    async mkdir(
        hostId: number,
        remotePath: string
    ): Promise<FileTransferResponse> {
        return apiClient<FileTransferResponse>(`${API}/mkdir`, {
            method: "POST",
            json: {
                host_id: hostId,
                remote_path: remotePath,
            },
        });
    },

    async remove(
        hostId: number,
        remotePath: string
    ): Promise<FileTransferResponse> {
        return apiClient<FileTransferResponse>(`${API}/delete`, {
            method: "POST",
            json: {
                host_id: hostId,
                remote_path: remotePath,
            },
        });
    },

    async metrics(): Promise<SessionMetricsResponse> {
        return apiClient<SessionMetricsResponse>(`/api/v1/remote/metrics`);
    },
};
