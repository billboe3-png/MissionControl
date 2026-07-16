import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import DataTable, { Column } from "../../components/common/DataTable";
import HostAvailabilityCard from "../../components/zabbix/HostAvailabilityCard";
import { zabbixApi, ZabbixHost, ZabbixHostsResponse } from "../../services/zabbix";

export default function HostsPage() {
    const [data, setData] = useState<ZabbixHostsResponse | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        zabbixApi.getHosts()
            .then(setData)
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (error) return <div className="error-banner">{error}</div>;
    if (loading) return <div className="loading-bar" />;

    const columns: Column<ZabbixHost>[] = [
        { key: "name", header: "Name" },
        { key: "host", header: "Hostname" },
        { key: "interface", header: "IP" },
        {
            key: "status",
            header: "Status",
            render: (row) => <StatusBadge status={row.status === "enabled" ? "healthy" : "error"} label={row.status} />,
        },
        {
            key: "available",
            header: "Availability",
            render: (row) => <StatusBadge status={row.available === "available" ? "healthy" : "error"} label={row.available} />,
        },
    ];

    return (
        <>
            <PageHeader title="Hosts" subtitle={`Monitored hosts (${data?.total_count ?? 0})`} />
            <div className="identity-overview-section">
                <div className="ad-info-grid">
                    <HostAvailabilityCard available={data?.available_count ?? 0} unavailable={data?.unavailable_count ?? 0} total={data?.total_count ?? 0} />
                    <div className="ad-info-card">
                        <h4>Host Status</h4>
                        <p><strong>Enabled:</strong> {data?.enabled_count ?? 0}</p>
                        <p><strong>Disabled:</strong> {data?.disabled_count ?? 0}</p>
                    </div>
                </div>
            </div>
            <DataTable columns={columns} data={data?.hosts ?? []} emptyMessage="No hosts found" />
        </>
    );
}
