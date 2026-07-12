import { useState, useEffect } from "react";
import { CommandHistoryItem, RemoteHost } from "../types/dashboard";
import { remoteApi } from "../services/remote";

function formatDate(iso: string): string {
    const date = new Date(iso);
    return date.toLocaleString("en-US", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
}

function formatDuration(ms: number | null): string {
    if (ms === null) return "—";
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
}

interface HistoryDialogProps {
    hosts: RemoteHost[];
    onClose: () => void;
}

export default function HistoryDialog({ hosts, onClose }: HistoryDialogProps) {
    const [items, setItems] = useState<CommandHistoryItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState("");
    const [hostFilter, setHostFilter] = useState<string>("");
    const [successFilter, setSuccessFilter] = useState<string>("");
    const [expandedId, setExpandedId] = useState<number | null>(null);

    const fetchHistory = async () => {
        setLoading(true);
        try {
            const hostId = hostFilter ? parseInt(hostFilter, 10) : undefined;
            const success = successFilter === "" ? undefined : successFilter === "true";
            const data = await remoteApi.getHistory(
                search || undefined,
                hostId,
                success,
                50,
            );
            setItems(data.items);
        } catch {
            // silently fail
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchHistory();
    }, [search, hostFilter, successFilter]);

    const toggleExpand = (id: number) => {
        setExpandedId(expandedId === id ? null : id);
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div
                className="modal-content modal-content-wide"
                onClick={(e) => e.stopPropagation()}
            >
                <h3 className="modal-title">Command History</h3>

                <div className="history-filters">
                    <input
                        type="text"
                        className="form-input"
                        placeholder="Search commands..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                    <select
                        className="form-input"
                        value={hostFilter}
                        onChange={(e) => setHostFilter(e.target.value)}
                    >
                        <option value="">All Hosts</option>
                        {hosts.map((h) => (
                            <option key={h.id} value={h.id}>
                                {h.name}
                            </option>
                        ))}
                    </select>
                    <select
                        className="form-input"
                        value={successFilter}
                        onChange={(e) => setSuccessFilter(e.target.value)}
                    >
                        <option value="">All Results</option>
                        <option value="true">Success</option>
                        <option value="false">Failed</option>
                    </select>
                </div>

                <div className="history-list">
                    {loading ? (
                        <p className="empty-state">Loading...</p>
                    ) : items.length === 0 ? (
                        <p className="empty-state">No history records found.</p>
                    ) : (
                        items.map((item) => (
                            <div
                                key={item.id}
                                className="history-row"
                                onClick={() => toggleExpand(item.id)}
                            >
                                <div className="history-row-summary">
                                    <span
                                        className={`status-dot ${item.success ? "status-ok" : "status-error"}`}
                                    />
                                    <span className="history-host">
                                        {item.host_name ?? `Host #${item.host_id}`}
                                    </span>
                                    <span className="history-command">
                                        {item.command}
                                    </span>
                                    <span className="history-meta">
                                        {item.shell} | {formatDuration(item.duration_ms)}
                                    </span>
                                    <span className="history-time">
                                        {formatDate(item.started_at)}
                                    </span>
                                </div>

                                {expandedId === item.id && (
                                    <div className="history-detail">
                                        <div className="history-detail-row">
                                            <strong>Exit code:</strong>{" "}
                                            <span className={item.success ? "text-success" : "text-error"}>
                                                {item.exit_code}
                                            </span>
                                            {item.executed_by && (
                                                <>
                                                    {" | "}
                                                    <strong>User:</strong> {item.executed_by}
                                                </>
                                            )}
                                        </div>
                                        {item.stdout && (
                                            <pre className="command-output-pre">
                                                {item.stdout}
                                            </pre>
                                        )}
                                        {item.stderr && (
                                            <pre className="command-output-pre command-output-stderr">
                                                {item.stderr}
                                            </pre>
                                        )}
                                    </div>
                                )}
                            </div>
                        ))
                    )}
                </div>

                <div className="modal-actions">
                    <button className="btn btn-secondary" onClick={onClose}>
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
}
