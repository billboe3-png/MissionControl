import { useCallback, useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import EmptyState from "../../components/common/EmptyState";
import StatusBadge from "../../components/common/StatusBadge";
import {
    automationApi,
    PlaybookExecutionData,
    ExecutionLogData,
} from "../../services/automation";

const STATUS_OPTIONS = ["all", "running", "completed", "failed", "dry_run", "pending"] as const;

export default function ExecutionsPage() {
    const [items, setItems] = useState<PlaybookExecutionData[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [expanded, setExpanded] = useState<number | null>(null);
    const [statusFilter, setStatusFilter] = useState<string>("all");
    const [logs, setLogs] = useState<ExecutionLogData[]>([]);
    const [logsLoading, setLogsLoading] = useState(false);

    const loadData = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await automationApi.listExecutions(
                undefined,
                statusFilter === "all" ? undefined : statusFilter,
            );
            setItems(data.items);
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : "Failed to load executions");
        } finally {
            setLoading(false);
        }
    }, [statusFilter]);

    useEffect(() => {
        loadData();
    }, [loadData]);

    const loadLogs = useCallback(async (executionId: number) => {
        try {
            setLogsLoading(true);
            const data = await automationApi.listExecutionLogs(executionId);
            setLogs(data.items);
        } catch {
            setLogs([]);
        } finally {
            setLogsLoading(false);
        }
    }, []);

    useEffect(() => {
        if (expanded !== null) {
            loadLogs(expanded);
        } else {
            setLogs([]);
        }
    }, [expanded, loadLogs]);

    const renderProgressBar = (item: PlaybookExecutionData) => {
        const pct = item.steps_total > 0
            ? Math.round((item.steps_completed / item.steps_total) * 100)
            : 0;
        return (
            <div style={{ width: "120px", height: "6px", background: "var(--border)", borderRadius: "3px", overflow: "hidden" }}>
                <div
                    style={{
                        width: `${pct}%`,
                        height: "100%",
                        background: item.status === "failed" ? "var(--error)" : item.status === "completed" ? "var(--success)" : "var(--primary)",
                        borderRadius: "3px",
                        transition: "width 0.3s",
                    }}
                />
            </div>
        );
    };

    return (
        <>
            <PageHeader
                title="Execution History"
                subtitle="View all playbook executions"
                actions={
                    <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                        <select
                            className="form-input"
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                            style={{ width: "auto" }}
                        >
                            {STATUS_OPTIONS.map((s) => (
                                <option key={s} value={s}>{s === "all" ? "All Statuses" : s.charAt(0).toUpperCase() + s.slice(1)}</option>
                            ))}
                        </select>
                        <button className="btn btn-secondary btn-sm" onClick={loadData}>
                            Refresh
                        </button>
                    </div>
                }
            />
            {error && <div className="error-banner">{error}</div>}
            {loading ? (
                <div className="loading-bar" />
            ) : items.length === 0 ? (
                <EmptyState
                    icon="⚡"
                    title="No executions"
                    description="Execute a playbook to see results here."
                />
            ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                    {items.map((item) => (
                        <div
                            key={item.id}
                            className="card"
                            style={{ padding: "1rem", cursor: "pointer" }}
                            onClick={() => setExpanded(expanded === item.id ? null : item.id)}
                        >
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                                    <span style={{ fontWeight: 700, color: "var(--primary)", minWidth: "3rem" }}>
                                        #{item.id}
                                    </span>
                                    <StatusBadge
                                        status={
                                            item.status === "completed" ? "healthy" :
                                            item.status === "failed" ? "error" :
                                            item.status === "running" ? "warning" :
                                            item.status === "dry_run" ? "info" : "neutral"
                                        }
                                        label={item.status}
                                    />
                                    <span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                                        {item.mode}
                                    </span>
                                    {renderProgressBar(item)}
                                    <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                                        {item.steps_completed}/{item.steps_total}
                                    </span>
                                </div>
                                <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                                    <span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                                        {item.triggered_by ?? item.trigger_type}
                                    </span>
                                    <span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                                        {item.duration_ms != null ? `${item.duration_ms}ms` : "—"}
                                    </span>
                                    <span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                                        {new Date(item.created_at).toLocaleString()}
                                    </span>
                                </div>
                            </div>
                            {expanded === item.id && (
                                <div style={{ marginTop: "1rem", paddingTop: "1rem", borderTop: "1px solid var(--border)" }}>
                                    <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
                                        <StatusBadge status="info" label={`Steps: ${item.steps_completed}/${item.steps_total}`} />
                                        {item.steps_failed > 0 && <StatusBadge status="error" label={`Failed: ${item.steps_failed}`} />}
                                        {item.steps_skipped > 0 && <StatusBadge status="neutral" label={`Skipped: ${item.steps_skipped}`} />}
                                        {item.approval_required && <StatusBadge status="warning" label={`Approval: ${item.approval_status ?? "pending"}`} />}
                                        {item.rollback_status && <StatusBadge status="info" label={`Rollback: ${item.rollback_status}`} />}
                                    </div>
                                    {logsLoading ? (
                                        <div className="loading-bar" />
                                    ) : logs.length > 0 ? (
                                        <div style={{ marginBottom: "1rem" }}>
                                            <h4 style={{ marginBottom: "0.5rem" }}>Execution Logs</h4>
                                            <div style={{ display: "flex", flexDirection: "column", gap: "0.25rem", maxHeight: "300px", overflow: "auto" }}>
                                                {logs.map((log) => (
                                                    <div
                                                        key={log.id}
                                                        style={{
                                                            padding: "0.4rem 0.75rem",
                                                            background: log.level === "error" ? "#3b1515" : "var(--surface)",
                                                            borderRadius: "4px",
                                                            fontSize: "0.8rem",
                                                            fontFamily: "monospace",
                                                            color: log.level === "error" ? "#f5a5a5" : "var(--text)",
                                                        }}
                                                    >
                                                        <span style={{ color: "var(--text-muted)", marginRight: "0.5rem" }}>
                                                            [{log.level}]
                                                        </span>
                                                        {log.message}
                                                        {log.duration_ms != null && (
                                                            <span style={{ color: "var(--text-muted)", marginLeft: "0.5rem" }}>
                                                                ({log.duration_ms}ms)
                                                            </span>
                                                        )}
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    ) : null}
                                    {item.output && (
                                        <div style={{ marginBottom: "1rem" }}>
                                            <h4 style={{ marginBottom: "0.5rem" }}>Output</h4>
                                            <pre style={{ padding: "1rem", background: "var(--surface)", borderRadius: "6px", fontSize: "0.8rem", overflow: "auto", maxHeight: "300px" }}>
                                                {item.output}
                                            </pre>
                                        </div>
                                    )}
                                    {item.error && (
                                        <div style={{ marginBottom: "1rem" }}>
                                            <h4 style={{ marginBottom: "0.5rem" }}>Error</h4>
                                            <pre style={{ padding: "1rem", background: "#3b1515", borderRadius: "6px", fontSize: "0.8rem", color: "#f5a5a5", overflow: "auto", maxHeight: "300px" }}>
                                                {item.error}
                                            </pre>
                                        </div>
                                    )}
                                    {item.rollback_output && (
                                        <div>
                                            <h4 style={{ marginBottom: "0.5rem" }}>Rollback Output</h4>
                                            <pre style={{ padding: "1rem", background: "var(--surface)", borderRadius: "6px", fontSize: "0.8rem", overflow: "auto", maxHeight: "300px" }}>
                                                {item.rollback_output}
                                            </pre>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </>
    );
}
