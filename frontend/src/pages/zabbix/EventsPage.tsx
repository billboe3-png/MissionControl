import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import DataTable, { Column } from "../../components/common/DataTable";
import { zabbixApi, ZabbixEvent, ZabbixEventsResponse } from "../../services/zabbix";

const SEVERITIES = [
    { key: "not_classified", label: "Not classified", color: "#6c757d" },
    { key: "information", label: "Information", color: "#0dcaf0" },
    { key: "warning", label: "Warning", color: "#ffc107" },
    { key: "average", label: "Average", color: "#fd7e14" },
    { key: "high", label: "High", color: "#dc3545" },
    { key: "disaster", label: "Disaster", color: "#842029" },
];

const SEVERITY_STATUS: Record<string, "error" | "warning" | "info"> = {
    not_classified: "info",
    information: "info",
    warning: "warning",
    average: "warning",
    high: "error",
    disaster: "error",
};

export default function EventsPage() {
    const [searchParams] = useSearchParams();
    const [data, setData] = useState<ZabbixEventsResponse | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    const urlSeverities = searchParams.getAll("severity");
    const [activeSeverities, setActiveSeverities] = useState<Set<string>>(
        () => new Set(urlSeverities.length > 0 ? urlSeverities : SEVERITIES.map((s) => s.key))
    );

    useEffect(() => {
        const sevs = searchParams.getAll("severity");
        if (sevs.length > 0) {
            setActiveSeverities(new Set(sevs));
        }
    }, [searchParams]);

    useEffect(() => {
        zabbixApi.getEvents()
            .then(setData)
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    const toggleSeverity = (key: string) => {
        setActiveSeverities((prev) => {
            const next = new Set(prev);
            if (next.has(key)) {
                next.delete(key);
            } else {
                next.add(key);
            }
            return next;
        });
    };

    if (error) return <div className="error-banner">{error}</div>;
    if (loading) return <div className="loading-bar" />;

    const filtered = (data?.events ?? []).filter((e) =>
        activeSeverities.has(e.severity)
    );

    const columns: Column<ZabbixEvent>[] = [
        { key: "name", header: "Event" },
        { key: "host", header: "Host" },
        {
            key: "severity",
            header: "Severity",
            render: (row) => (
                <StatusBadge
                    status={SEVERITY_STATUS[row.severity] ?? "info"}
                    label={row.severity}
                />
            ),
        },
        {
            key: "status",
            header: "Status",
            render: (row) => <StatusBadge status={row.status === "PROBLEM" ? "error" : "healthy"} label={row.status} />,
        },
        {
            key: "timestamp",
            header: "Time",
            render: (row) => {
                const ts = typeof row.timestamp === "number" ? row.timestamp : Number(row.timestamp);
                if (!ts || isNaN(ts)) return row.timestamp ?? "—";
                const d = new Date(ts * 1000);
                return d.toLocaleString();
            },
        },
    ];

    return (
        <>
            <PageHeader title="Events" subtitle={`Recent events (${filtered.length})`} />
            <div className="identity-overview-section">
                <h3>Severity Filter</h3>
                <div className="severity-filters">
                    {SEVERITIES.map((s) => {
                        const count = (data?.events ?? []).filter((e) => e.severity === s.key).length;
                        return (
                            <label key={s.key} className="severity-filter-item">
                                <input
                                    type="checkbox"
                                    checked={activeSeverities.has(s.key)}
                                    onChange={() => toggleSeverity(s.key)}
                                />
                                <span
                                    className="severity-dot"
                                    style={{ backgroundColor: s.color }}
                                />
                                <span>{s.label}</span>
                                <span className="severity-count">({count})</span>
                            </label>
                        );
                    })}
                </div>
            </div>
            <DataTable columns={columns} data={filtered} emptyMessage="No events match filter" />
        </>
    );
}
