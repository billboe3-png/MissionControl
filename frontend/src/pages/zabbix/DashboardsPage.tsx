import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import DashboardCard from "../../components/zabbix/DashboardCard";
import { zabbixApi, ZabbixDashboardsResponse } from "../../services/zabbix";

export default function DashboardsPage() {
    const [data, setData] = useState<ZabbixDashboardsResponse | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        zabbixApi.getDashboards()
            .then(setData)
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (error) return <div className="error-banner">{error}</div>;
    if (loading) return <div className="loading">Loading…</div>;

    return (
        <>
            <PageHeader title="Dashboards" subtitle={`Zabbix dashboards (${data?.total_count ?? 0})`} />
            <div className="ad-info-grid">
                {(data?.dashboards ?? []).map((d) => (
                    <DashboardCard key={d.dashboardid} dashboard={d} />
                ))}
                {(!data || data.total_count === 0) && <p>No dashboards found</p>}
            </div>
        </>
    );
}
