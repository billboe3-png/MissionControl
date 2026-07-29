import { useEffect, useMemo, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import DataTable, { Column } from "../../components/common/DataTable";
import HostAvailabilityCard from "../../components/zabbix/HostAvailabilityCard";
import { zabbixApi, ZabbixHost, ZabbixHostsResponse } from "../../services/zabbix";

type StatusFilter = "all" | "enabled" | "disabled";

export default function HostsPage() {
    const [data, setData] = useState<ZabbixHostsResponse | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");

    useEffect(() => {
        zabbixApi.getHosts()
            .then(setData)
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    const filteredHosts = useMemo(() => {
        const hosts = data?.hosts ?? [];
        if (statusFilter === "all") return hosts;
        return hosts.filter((h) => h.status === statusFilter);
    }, [data, statusFilter]);

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
            render: (row) => (
                <StatusBadge
                    status={row.available === "available" ? "healthy" : row.available === "unavailable" ? "error" : "neutral"}
                    label={row.available}
                />
            ),
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
            <div className="fleet-toolbar">
                <select
                    className="form-input fleet-filter"
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
                >
                    <option value="all">All Status</option>
                    <option value="enabled">Enabled</option>
                    <option value="disabled">Disabled</option>
                </select>
                <span className="refresh-indicator">
                    {filteredHosts.length} of {data?.total_count ?? 0} shown
                </span>
            </div>
            <DataTable columns={columns} data={filteredHosts} emptyMessage="No hosts found" />
        </>
    );
}
