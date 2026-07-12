import { useState, useEffect } from "react";
import { RemoteHost, CommandHistoryItem } from "../types/dashboard";
import { hostsApi, remoteApi } from "../services/remote";
import Toolbar from "./common/Toolbar";
import ConfirmDialog from "./common/ConfirmDialog";
import HostModal from "./modals/HostModal";
import ExecuteCommandModal from "./modals/ExecuteCommandModal";
import HistoryDialog from "./HistoryDialog";

function connectionBadge(type: string): string {
    return type === "ssh" ? "badge badge-info" : "badge badge-warning";
}

function statusBadge(enabled: boolean): string {
    return enabled ? "badge badge-success" : "badge badge-muted";
}

function formatDuration(ms: number | null): string {
    if (ms === null) return "—";
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
}

function formatDate(iso: string): string {
    const date = new Date(iso);
    return date.toLocaleString("en-US", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
}

interface RemoteOperationsCardProps {
    totalHosts: number;
    enabledHosts: number;
    recentCommands: { id: number; host_id: number; command: string; success: boolean; started_at: string | null }[];
    onRefresh: () => void;
    showToast: (message: string, type?: "success" | "error") => void;
}

export default function RemoteOperationsCard({
    totalHosts,
    enabledHosts,
    recentCommands,
    onRefresh,
    showToast,
}: RemoteOperationsCardProps) {
    const [hosts, setHosts] = useState<RemoteHost[]>([]);
    const [hostModalOpen, setHostModalOpen] = useState(false);
    const [editingHost, setEditingHost] = useState<RemoteHost | undefined>(undefined);
    const [confirmDelete, setConfirmDelete] = useState<RemoteHost | undefined>(undefined);
    const [deleting, setDeleting] = useState(false);
    const [executeModalOpen, setExecuteModalOpen] = useState(false);
    const [executeHost, setExecuteHost] = useState<RemoteHost | undefined>(undefined);
    const [historyOpen, setHistoryOpen] = useState(false);

    useEffect(() => {
        hostsApi.list().then((data) => setHosts(data.items)).catch(() => {});
    }, []);

    const handleNewHost = () => {
        setEditingHost(undefined);
        setHostModalOpen(true);
    };

    const handleEditHost = (host: RemoteHost) => {
        setEditingHost(host);
        setHostModalOpen(true);
    };

    const handleSaveHost = () => {
        setHostModalOpen(false);
        setEditingHost(undefined);
        showToast("Host saved");
        hostsApi.list().then((data) => setHosts(data.items)).catch(() => {});
        onRefresh();
    };

    const handleDeleteHost = async () => {
        if (!confirmDelete) return;
        setDeleting(true);
        try {
            await hostsApi.remove(confirmDelete.id);
            setConfirmDelete(undefined);
            showToast("Host deleted");
            hostsApi.list().then((data) => setHosts(data.items)).catch(() => {});
            onRefresh();
        } catch (err) {
            showToast(err instanceof Error ? err.message : "Delete failed", "error");
        } finally {
            setDeleting(false);
        }
    };

    const handleTestConnection = async (host: RemoteHost) => {
        try {
            const result = await remoteApi.testConnection({ host_id: host.id });
            showToast(result.message, result.success ? "success" : "error");
        } catch (err) {
            showToast(err instanceof Error ? err.message : "Test failed", "error");
        }
    };

    const handleExecute = (host: RemoteHost) => {
        setExecuteHost(host);
        setExecuteModalOpen(true);
    };

    return (
        <div className="dashboard-card">
            <div className="card-header">
                <h2 className="card-title">Remote Operations</h2>
                <div className="card-stats">
                    <span className="stat-value">{totalHosts}</span>
                    <span className="stat-label">hosts</span>
                </div>
            </div>

            <Toolbar onAdd={handleNewHost} addLabel="Add Host" />

            <div className="card-body">
                {hosts.length === 0 ? (
                    <p className="empty-state">
                        No remote hosts configured. Click "Add Host" to get started.
                    </p>
                ) : (
                    <div className="items-list">
                        {hosts.map((host) => (
                            <div key={host.id} className="item-row">
                                <div className="item-main">
                                    <div className="item-header">
                                        <span className="item-name">{host.name}</span>
                                        <span className={connectionBadge(host.connection_type)}>
                                            {host.connection_type.toUpperCase()}
                                        </span>
                                        <span className={statusBadge(host.enabled)}>
                                            {host.enabled ? "enabled" : "disabled"}
                                        </span>
                                    </div>
                                    <div className="item-detail">
                                        {host.hostname}:{host.port}
                                        {host.credential_profile_name && (
                                            <span className="credential-tag">
                                                {host.credential_profile_name}
                                            </span>
                                        )}
                                        {host.operating_system && (
                                            <span className="os-tag">{host.operating_system}</span>
                                        )}
                                    </div>
                                </div>
                                <div className="item-actions">
                                    <button
                                        className="btn btn-sm btn-ghost"
                                        onClick={() => handleTestConnection(host)}
                                        title="Test connection"
                                    >
                                        Test
                                    </button>
                                    <button
                                        className="btn btn-sm btn-ghost"
                                        onClick={() => handleExecute(host)}
                                        title="Execute command"
                                    >
                                        Execute
                                    </button>
                                    <button
                                        className="btn btn-sm btn-ghost"
                                        onClick={() => handleEditHost(host)}
                                        title="Edit host"
                                    >
                                        Edit
                                    </button>
                                    <button
                                        className="btn btn-sm btn-ghost btn-danger"
                                        onClick={() => setConfirmDelete(host)}
                                        title="Delete host"
                                    >
                                        Delete
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {recentCommands.length > 0 && (
                    <div className="recent-commands">
                        <h3 className="section-title">Recent Commands</h3>
                        <div className="items-list">
                            {recentCommands.map((cmd) => (
                                <div key={cmd.id} className="item-row item-row-compact">
                                    <span className={`status-dot ${cmd.success ? "status-ok" : "status-error"}`} />
                                    <span className="command-text">{cmd.command}</span>
                                    <span className="command-time">
                                        {cmd.started_at ? formatDate(cmd.started_at) : "—"}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                <button
                    className="btn btn-ghost btn-block"
                    onClick={() => setHistoryOpen(true)}
                >
                    View Full History
                </button>
            </div>

            {hostModalOpen && (
                <HostModal
                    host={editingHost}
                    onSave={handleSaveHost}
                    onCancel={() => { setHostModalOpen(false); setEditingHost(undefined); }}
                    onError={(msg) => showToast(msg, "error")}
                />
            )}

            {confirmDelete && (
                <ConfirmDialog
                    title="Delete Host"
                    message={`Are you sure you want to delete "${confirmDelete.name}"?`}
                    confirmLabel="Delete"
                    onConfirm={handleDeleteHost}
                    onCancel={() => setConfirmDelete(undefined)}
                    loading={deleting}
                    danger
                />
            )}

            {executeModalOpen && executeHost && (
                <ExecuteCommandModal
                    host={executeHost}
                    onExecute={async (result) => {
                        showToast(result.success ? "Command succeeded" : "Command failed", result.success ? "success" : "error");
                    }}
                    onCancel={() => { setExecuteModalOpen(false); setExecuteHost(undefined); }}
                    onError={(msg) => showToast(msg, "error")}
                />
            )}

            {historyOpen && (
                <HistoryDialog
                    hosts={hosts}
                    onClose={() => setHistoryOpen(false)}
                />
            )}
        </div>
    );
}
