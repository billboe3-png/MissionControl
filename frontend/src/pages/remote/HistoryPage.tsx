import { useCallback, useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import SearchInput from "../../components/common/SearchInput";
import DataTable, { Column } from "../../components/common/DataTable";
import EmptyState from "../../components/common/EmptyState";
import StatusBadge from "../../components/common/StatusBadge";
import { remoteApi, CommandHistoryData } from "../../services/remote";

export default function HistoryPage() {
    const [items, setItems] = useState<CommandHistoryData[]>([]);
    const [search, setSearch] = useState("");
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [expanded, setExpanded] = useState<number | null>(null);

    const loadHistory = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await remoteApi.getHistory(search || undefined);
            setItems(data.items);
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : "Failed to load history");
        } finally {
            setLoading(false);
        }
    }, [search]);

    useEffect(() => {
        loadHistory();
    }, [loadHistory]);

    const columns: Column<CommandHistoryData>[] = [
        {
            key: "host_name",
            header: "Host",
            render: (row) => row.host_name ?? `#${row.host_id}`,
        },
        {
            key: "command",
            header: "Command",
            render: (row) => (
                <code className="history-command">{row.command}</code>
            ),
        },
        {
            key: "success",
            header: "Status",
            render: (row) => (
                <StatusBadge
                    status={row.success ? "healthy" : "error"}
                    label={row.success ? "OK" : `Exit ${row.exit_code}`}
                />
            ),
        },
        {
            key: "duration_ms",
            header: "Duration",
            render: (row) =>
                row.duration_ms != null ? `${row.duration_ms}ms` : "—",
        },
        {
            key: "started_at",
            header: "Time",
            render: (row) => new Date(row.started_at).toLocaleString(),
        },
    ];

    return (
        <>
            <PageHeader
                title="Command History"
                subtitle="Past remote command executions"
            />
            <SearchInput
                value={search}
                onChange={setSearch}
                placeholder="Search commands…"
            />
            {error && <div className="error-banner">{error}</div>}
            {loading ? (
                <div className="loading">Loading…</div>
            ) : items.length === 0 ? (
                <EmptyState
                    icon="📜"
                    title="No command history"
                    description="Commands you execute will appear here."
                />
            ) : (
                <DataTable
                    columns={columns}
                    data={items}
                    onRowClick={(row) => {
                        setExpanded(expanded === row.id ? null : row.id);
                    }}
                    emptyMessage="No history found"
                />
            )}
            {expanded !== null && (() => {
                const item = items.find((i) => i.id === expanded);
                if (!item) return null;
                return (
                    <div className="history-detail">
                        <h3>Output — {item.command}</h3>
                        {item.stdout && (
                            <pre className="execute-stdout">{item.stdout}</pre>
                        )}
                        {item.stderr && (
                            <pre className="execute-stderr">{item.stderr}</pre>
                        )}
                    </div>
                );
            })()}
        </>
    );
}
