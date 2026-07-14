import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import DataTable, { Column } from "../../components/common/DataTable";
import TriggerStatusCard from "../../components/zabbix/TriggerStatusCard";
import { zabbixApi, ZabbixTrigger, ZabbixTriggersResponse } from "../../services/zabbix";

export default function TriggersPage() {
    const [data, setData] = useState<ZabbixTriggersResponse | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        zabbixApi.getTriggers()
            .then(setData)
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (error) return <div className="error-banner">{error}</div>;
    if (loading) return <div className="loading">Loading…</div>;

    const columns: Column<ZabbixTrigger>[] = [
        { key: "description", header: "Description" },
        { key: "hosts", header: "Hosts", render: (row) => row.hosts.join(", ") },
        {
            key: "priority",
            header: "Priority",
            render: (row) => {
                const st = row.priority === "disaster" || row.priority === "high" ? "error" : row.priority === "warning" ? "warning" : "info";
                return <StatusBadge status={st} label={row.priority} />;
            },
        },
        {
            key: "value",
            header: "Status",
            render: (row) => <StatusBadge status={row.value === "PROBLEM" ? "error" : "healthy"} label={row.value} />,
        },
    ];

    return (
        <>
            <PageHeader title="Triggers" subtitle={`Trigger rules (${data?.total_count ?? 0})`} />
            <div className="identity-overview-section">
                <TriggerStatusCard problemCount={data?.problem_count ?? 0} okCount={data?.ok_count ?? 0} enabledCount={data?.enabled_count ?? 0} disabledCount={data?.disabled_count ?? 0} />
            </div>
            <DataTable columns={columns} data={data?.triggers ?? []} emptyMessage="No triggers found" />
        </>
    );
}
