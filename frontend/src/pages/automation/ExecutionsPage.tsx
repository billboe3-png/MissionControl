import { useCallback, useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import SearchInput from "../../components/common/SearchInput";
import DataTable, { Column } from "../../components/common/DataTable";
import EmptyState from "../../components/common/EmptyState";
import StatusBadge from "../../components/common/StatusBadge";
import {
    automationApi,
    PlaybookExecutionData,
} from "../../services/automation";

export default function ExecutionsPage() {
    const [items, setItems] = useState<PlaybookExecutionData[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [expanded, setExpanded] = useState<number | null>(null);

    const loadData = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await automationApi.listExecutions();
            setItems(data.items);
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : "Failed to load executions");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadData();
    }, [loadData]);

    const columns: Column<PlaybookExecutionData>[] = [
        {
            key: "id",
            header: "ID",
            render: (r) => `#${r.id}`,
        },
        {
            key: "status",
            header: "Status",
            render: (r) => (
                <StatusBadge
                    status={
                        r.status === "completed" ? "healthy" :
                        r.status === "failed" ? "error" :
                        r.status === "running" ? "warning" :
                        r.status === "dry_run" ? "info" : "neutral"
                    }
                    label={r.status}
                />
            ),
        },
        { key: "mode", header: "Mode" },
        {
            key: "steps_completed",
            header: "Progress",
            render: (r) => `${r.steps_completed}/${r.steps_total}`,
        },
        {
            key: "trigger_type",
            header: "Trigger",
            render: (r) => r.triggered_by ?? r.trigger_type,
        },
        {
            key: "duration_ms",
            header: "Duration",
            render: (r) => r.duration_ms != null ? `${r.duration_ms}ms` : "—",
        },
        {
            key: "created_at",
            header: "Started",
            render: (r) => new Date(r.created_at).toLocaleString(),
        },
    ];

    return (
        <>
            <PageHeader
                title="Execution History"
                subtitle="View all playbook executions"
            />
            {error && <div className="error-banner">{error}</div>}
            {loading ? (
                <div className="loading">Loading…</div>
            ) : items.length === 0 ? (
                <EmptyState
                    icon="⚡"
                    title="No executions"
                    description="Execute a playbook to see results here."
                />
            ) : (
                <DataTable
                    columns={columns}
                    data={items}
                    onRowClick={(r) => setExpanded(expanded === r.id ? null : r.id)}
                    emptyMessage="No executions found"
                />
            )}
            {expanded !== null && (() => {
                const item = items.find((i) => i.id === expanded);
                if (!item) return null;
                return (
                    <div className="history-detail" style={{ marginTop: "1rem" }}>
                        <h3>Execution #{item.id} Output</h3>
                        {item.output && (
                            <pre className="execute-stdout">{item.output}</pre>
                        )}
                        {item.error && (
                            <pre className="execute-stderr">{item.error}</pre>
                        )}
                        {item.rollback_output && (
                            <>
                                <h4>Rollback Output</h4>
                                <pre className="execute-stdout">{item.rollback_output}</pre>
                            </>
                        )}
                    </div>
                );
            })()}
        </>
    );
}
