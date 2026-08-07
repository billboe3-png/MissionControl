import { useCallback, useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import EmptyState from "../../components/common/EmptyState";
import StatusBadge from "../../components/common/StatusBadge";
import { useToast } from "../../contexts/ToastContext";
import { formatDateTime } from "../../utils/dateFormat";
import {
    automationApi,
    AuditTrailData,
} from "../../services/automation";

export default function AuditPage() {
    const [items, setItems] = useState<AuditTrailData[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [filterType, setFilterType] = useState("");
    const [filterAction, setFilterAction] = useState("");
    const { showToast } = useToast();

    const loadData = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await automationApi.listAuditTrail(
                filterType || undefined,
                filterAction || undefined,
            );
            setItems(data.items);
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : "Failed to load audit trail");
        } finally {
            setLoading(false);
        }
    }, [filterType, filterAction]);

    useEffect(() => {
        loadData();
    }, [loadData]);

    const actionColor = (action: string) => {
        if (["created", "started", "completed", "approved"].includes(action)) return "healthy";
        if (["failed", "rejected", "deleted"].includes(action)) return "error";
        if (["updated", "rollback", "dry_run"].includes(action)) return "warning";
        return "neutral";
    };

    return (
        <>
            <PageHeader
                title="Audit Trail"
                subtitle="Complete audit log of all automation actions"
            />
            <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem" }}>
                <select
                    className="form-select"
                    value={filterType}
                    onChange={(e) => setFilterType(e.target.value)}
                    style={{ padding: "0.5rem", background: "var(--surface)", color: "var(--text)", border: "1px solid var(--border)", borderRadius: "6px" }}
                >
                    <option value="">All Entity Types</option>
                    <option value="playbook">Playbook</option>
                    <option value="playbook_execution">Execution</option>
                    <option value="approval_request">Approval</option>
                </select>
                <select
                    className="form-select"
                    value={filterAction}
                    onChange={(e) => setFilterAction(e.target.value)}
                    style={{ padding: "0.5rem", background: "var(--surface)", color: "var(--text)", border: "1px solid var(--border)", borderRadius: "6px" }}
                >
                    <option value="">All Actions</option>
                    <option value="created">Created</option>
                    <option value="updated">Updated</option>
                    <option value="deleted">Deleted</option>
                    <option value="started">Started</option>
                    <option value="completed">Completed</option>
                    <option value="failed">Failed</option>
                    <option value="approved">Approved</option>
                    <option value="rejected">Rejected</option>
                    <option value="rollback">Rollback</option>
                    <option value="dry_run">Dry Run</option>
                </select>
            </div>
            {error && <div className="error-banner">{error}</div>}
            {loading ? (
                <div className="loading-bar" />
            ) : items.length === 0 ? (
                <EmptyState
                    icon="📋"
                    title="No audit entries"
                    description="Actions will be recorded here."
                />
            ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                    {items.map((item) => (
                        <div
                            key={item.id}
                            style={{
                                display: "flex",
                                justifyContent: "space-between",
                                alignItems: "center",
                                padding: "0.75rem 1rem",
                                background: "var(--surface)",
                                borderRadius: "8px",
                            }}
                        >
                            <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                                <StatusBadge
                                    status={actionColor(item.action)}
                                    label={item.action}
                                />
                                <div>
                                    <span style={{ fontWeight: 600 }}>{item.entity_type}</span>
                                    {item.entity_id && (
                                        <span className="text-muted"> #{item.entity_id}</span>
                                    )}
                                    {item.details && (
                                        <div className="text-muted" style={{ fontSize: "0.85rem" }}>
                                            {item.details}
                                        </div>
                                    )}
                                </div>
                            </div>
                            <div style={{ textAlign: "right" }}>
                                <div className="text-muted" style={{ fontSize: "0.85rem" }}>
                                    {item.actor ?? "System"}
                                </div>
                                <div className="text-muted" style={{ fontSize: "0.8rem" }}>
                                    {formatDateTime(item.timestamp)}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </>
    );
}
