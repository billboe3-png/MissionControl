import { useCallback, useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import {
    automationApi,
    AutomationSummaryData,
    PlaybookData,
    PlaybookExecutionData,
} from "../../services/automation";

export default function AutomationOverviewPage() {
    const [summary, setSummary] = useState<AutomationSummaryData | null>(null);
    const [playbooks, setPlaybooks] = useState<PlaybookData[]>([]);
    const [recentExecutions, setRecentExecutions] = useState<PlaybookExecutionData[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const loadData = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const [s, p, e] = await Promise.all([
                automationApi.getSummary(),
                automationApi.listPlaybooks(),
                automationApi.listExecutions(),
            ]);
            setSummary(s);
            setPlaybooks(p.items);
            setRecentExecutions(e.items.slice(0, 5));
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : "Failed to load automation data");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadData();
    }, [loadData]);

    if (loading) return <div className="loading-bar" />;
    if (error) return <div className="error-banner">{error}</div>;

    return (
        <>
            <PageHeader
                title="Automation"
                subtitle="Playbooks, executions, and workflow orchestration"
            />
            {summary && (
                <div className="stats-grid">
                    <div className="stat-card">
                        <div className="stat-value">{summary.total_playbooks}</div>
                        <div className="stat-label">Playbooks</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value">{summary.total_executions}</div>
                        <div className="stat-label">Total Executions</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value">{summary.running}</div>
                        <div className="stat-label">Running</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value">{summary.completed}</div>
                        <div className="stat-label">Completed</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value">{summary.failed}</div>
                        <div className="stat-label">Failed</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value">{summary.pending_approvals}</div>
                        <div className="stat-label">Pending Approvals</div>
                    </div>
                </div>
            )}

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem", marginTop: "1.5rem" }}>
                <div className="card">
                    <h3 className="card-title">Recent Playbooks</h3>
                    {playbooks.length === 0 ? (
                        <p className="text-muted">No playbooks created yet.</p>
                    ) : (
                        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                            {playbooks.slice(0, 5).map((p) => (
                                <div key={p.id} className="data-table-row" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0.75rem", background: "var(--surface)", borderRadius: "8px" }}>
                                    <div>
                                        <div style={{ fontWeight: 600 }}>{p.name}</div>
                                        <div className="text-muted" style={{ fontSize: "0.8rem" }}>
                                            v{p.version} · {p.category ?? "General"}
                                        </div>
                                    </div>
                                    <StatusBadge
                                        status={p.enabled ? "healthy" : "neutral"}
                                        label={p.enabled ? "Active" : "Disabled"}
                                    />
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                <div className="card">
                    <h3 className="card-title">Recent Executions</h3>
                    {recentExecutions.length === 0 ? (
                        <p className="text-muted">No executions yet.</p>
                    ) : (
                        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                            {recentExecutions.map((e) => (
                                <div key={e.id} className="data-table-row" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0.75rem", background: "var(--surface)", borderRadius: "8px" }}>
                                    <div>
                                        <div style={{ fontWeight: 600 }}>Execution #{e.id}</div>
                                        <div className="text-muted" style={{ fontSize: "0.8rem" }}>
                                            {e.steps_completed}/{e.steps_total} steps · {e.mode}
                                        </div>
                                    </div>
                                    <StatusBadge
                                        status={
                                            e.status === "completed" ? "healthy" :
                                            e.status === "failed" ? "error" :
                                            e.status === "running" ? "warning" : "neutral"
                                        }
                                        label={e.status}
                                    />
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </>
    );
}
