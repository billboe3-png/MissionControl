import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import DataTable, { Column } from "../../components/common/DataTable";
import ProblemSeverityCard from "../../components/zabbix/ProblemSeverityCard";
import { zabbixApi, ZabbixProblem, ZabbixProblemsResponse } from "../../services/zabbix";

export default function ProblemsPage() {
    const [data, setData] = useState<ZabbixProblemsResponse | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        zabbixApi.getProblems()
            .then(setData)
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (error) return <div className="error-banner">{error}</div>;
    if (loading) return <div className="loading">Loading…</div>;

    const columns: Column<ZabbixProblem>[] = [
        { key: "name", header: "Problem" },
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
            key: "acknowledged",
            header: "Acknowledged",
            render: (row) => <StatusBadge status={row.acknowledged ? "healthy" : "warning"} label={row.acknowledged ? "Yes" : "No"} />,
        },
        { key: "timestamp", header: "Time" },
    ];

    return (
        <>
            <PageHeader title="Problems" subtitle={`Active problems (${data?.total_count ?? 0})`} />
            <div className="infra-overview-grid">
                {Object.entries(data?.severity_counts ?? {}).map(([sev, count]) => (
                    <ProblemSeverityCard key={sev} severity={sev} count={count} />
                ))}
            </div>
            <div className="identity-overview-section">
                <p><strong>Acknowledged:</strong> {data?.acknowledged_count ?? 0} | <strong>Unacknowledged:</strong> {data?.unacknowledged_count ?? 0}</p>
            </div>
            <DataTable columns={columns} data={data?.problems ?? []} emptyMessage="No active problems" />
        </>
    );
}
