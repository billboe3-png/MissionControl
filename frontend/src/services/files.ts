const API = "/api/v1/remote/files";

async function handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
        const body = await response.json().catch(() => null);
        const detail = body?.detail;
        throw new Error(detail ?? `Request failed (${response.status})`);
    }
    return response.json();
}

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
        const response = await fetch(
            `${API}/list?host_id=${hostId}&path=${encodeURIComponent(path)}`
        );
        return handleResponse<FileListResponse>(response);
    },

    async upload(
        hostId: number,
        remotePath: string,
        content: string
    ): Promise<FileTransferResponse> {
        const response = await fetch(`${API}/upload`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                host_id: hostId,
                remote_path: remotePath,
                content_base64: content,
            }),
        });
        return handleResponse<FileTransferResponse>(response);
    },

    async download(
        hostId: number,
        remotePath: string
    ): Promise<FileDownloadResponse> {
        const response = await fetch(`${API}/download`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                host_id: hostId,
                remote_path: remotePath,
            }),
        });
        return handleResponse<FileDownloadResponse>(response);
    },

    async mkdir(
        hostId: number,
        remotePath: string
    ): Promise<FileTransferResponse> {
        const response = await fetch(`${API}/mkdir`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                host_id: hostId,
                remote_path: remotePath,
            }),
        });
        return handleResponse<FileTransferResponse>(response);
    },

    async remove(
        hostId: number,
        remotePath: string
    ): Promise<FileTransferResponse> {
        const response = await fetch(`${API}/delete`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                host_id: hostId,
                remote_path: remotePath,
            }),
        });
        return handleResponse<FileTransferResponse>(response);
    },

    async metrics(): Promise<SessionMetricsResponse> {
        const response = await fetch(`/api/v1/remote/metrics`);
        return handleResponse<SessionMetricsResponse>(response);
    },
};
