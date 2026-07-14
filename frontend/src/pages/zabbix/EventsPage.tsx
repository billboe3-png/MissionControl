import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import DataTable, { Column } from "../../components/common/DataTable";
import { zabbixApi, ZabbixEvent, ZabbixEventsResponse } from "../../services/zabbix";

export default function EventsPage() {
    const [data, setData] = useState<ZabbixEventsResponse | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        zabbixApi.getEvents()
            .then(setData)
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (error) return <div className="error-banner">{error}</div>;
    if (loading) return <div className="loading">Loading…</div>;

    const columns: Column<ZabbixEvent>[] = [
        { key: "name", header: "Event" },
        { key: "host", header: "Host" },
        {
            key: "severity",
            header: "Severity",
            render: (row) => {
                const st = row.severity === "disaster" || row.severity === "high" ? "error" : row.severity === "warning" ? "warning" : "info";
                return <StatusBadge status={st} label={row.severity} />;
            },
        },
        {
            key: "status",
            header: "Status",
            render: (row) => <StatusBadge status={row.status === "PROBLEM" ? "error" : "healthy"} label={row.status} />,
        },
        { key: "timestamp", header: "Time" },
    ];

    return (
        <>
            <PageHeader title="Events" subtitle={`Recent events (${data?.total_count ?? 0})`} />
            <DataTable columns={columns} data={data?.events ?? []} emptyMessage="No events found" />
        </>
    );
}
