import { useCallback, useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import EmptyState from "../../components/common/EmptyState";
import StatusBadge from "../../components/common/StatusBadge";
import { useToast } from "../../contexts/ToastContext";
import { formatDateTime } from "../../utils/dateFormat";
import {
    automationApi,
    ApprovalRequestData,
} from "../../services/automation";

export default function ApprovalsPage() {
    const [items, setItems] = useState<ApprovalRequestData[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const { showToast } = useToast();

    const loadData = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await automationApi.listPendingApprovals();
            setItems(data.items);
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : "Failed to load approvals");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadData();
    }, [loadData]);

    const handleApprove = async (id: number) => {
        if (!window.confirm("Approve this request?")) return;
        try {
            await automationApi.approveRequest(id, {
                approved_by: "ui_user",
                comments: "Approved from UI",
            });
            showToast("Request approved", "success");
            loadData();
        } catch (e: unknown) {
            showToast(e instanceof Error ? e.message : "Approval failed", "error");
        }
    };

    const handleReject = async (id: number) => {
        if (!window.confirm("Reject this request?")) return;
        try {
            await automationApi.rejectRequest(id, {
                approved_by: "ui_user",
                comments: "Rejected from UI",
            });
            showToast("Request rejected", "success");
            loadData();
        } catch (e: unknown) {
            showToast(e instanceof Error ? e.message : "Rejection failed", "error");
        }
    };

    return (
        <>
            <PageHeader
                title="Approvals"
                subtitle="Pending approval requests for playbook executions"
            />
            {error && <div className="error-banner">{error}</div>}
            {loading ? (
                <div className="loading-bar" />
            ) : items.length === 0 ? (
                <EmptyState
                    icon="✅"
                    title="No pending approvals"
                    description="All approval requests have been processed."
                />
            ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                    {items.map((item) => (
                        <div
                            key={item.id}
                            className="card"
                            style={{ padding: "1.25rem" }}
                        >
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                <div>
                                    <div style={{ fontWeight: 600 }}>
                                        Approval Request #{item.id}
                                    </div>
                                    <div className="text-muted" style={{ fontSize: "0.85rem" }}>
                                        Execution #{item.execution_id} · Workflow #{item.workflow_id}
                                    </div>
                                    <div className="text-muted" style={{ fontSize: "0.85rem" }}>
                                        Requested by: {item.requested_by ?? "Unknown"} · {formatDateTime(item.requested_at)}
                                    </div>
                                </div>
                                <div style={{ display: "flex", gap: "0.5rem" }}>
                                    <StatusBadge
                                        status={item.status === "pending" ? "warning" : item.status === "approved" ? "healthy" : "error"}
                                        label={item.status}
                                    />
                                    {item.status === "pending" && (
                                        <>
                                            <button
                                                className="btn btn-primary btn-sm"
                                                onClick={() => handleApprove(item.id)}
                                            >
                                                Approve
                                            </button>
                                            <button
                                                className="btn btn-danger btn-sm"
                                                onClick={() => handleReject(item.id)}
                                            >
                                                Reject
                                            </button>
                                        </>
                                    )}
                                </div>
                            </div>
                            {item.comments && (
                                <div style={{ marginTop: "0.75rem", padding: "0.5rem", background: "var(--surface)", borderRadius: "6px" }}>
                                    <span className="text-muted">Comment: </span>{item.comments}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </>
    );
}
