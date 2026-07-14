import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import HealthIndicator from "../../components/zabbix/HealthIndicator";
import { zabbixApi, ZabbixHealthResponse } from "../../services/zabbix";

export default function HealthPage() {
    const [data, setData] = useState<ZabbixHealthResponse | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        zabbixApi.getHealth()
            .then(setData)
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (error) return <div className="error-banner">{error}</div>;
    if (loading) return <div className="loading">Loading…</div>;

    return (
        <>
            <PageHeader title="Zabbix Health" subtitle="Server and component health" />
            <div className="ad-info-grid">
                <div className="ad-info-card">
                    <h4>Server</h4>
                    <p><strong>Status:</strong> <HealthIndicator status={data?.status ?? "unknown"} /></p>
                    <p><strong>Version:</strong> {data?.version ?? "unknown"}</p>
                    <p><strong>Server:</strong> {data?.server ?? "N/A"}</p>
                    <p><strong>Uptime:</strong> {data?.uptime_hours ?? 0}h</p>
                    <p><strong>API Latency:</strong> {data?.api_latency_ms ?? 0}ms</p>
                </div>
                <div className="ad-info-card">
                    <h4>Database</h4>
                    <p><strong>Status:</strong> <HealthIndicator status={data?.database?.status ?? "unknown"} /></p>
                    <p><strong>Type:</strong> {data?.database?.type ?? "unknown"}</p>
                    <p><strong>Size:</strong> {data?.database?.size_mb ?? 0} MB</p>
                </div>
                <div className="ad-info-card">
                    <h4>Performance</h4>
                    <p><strong>Proxies:</strong> {data?.proxy_count ?? 0}</p>
                    <p><strong>Poller Items/sec:</strong> {data?.poller_items_per_sec ?? 0}</p>
                    <p><strong>Trigger Functions/sec:</strong> {data?.trigger_functions_per_sec ?? 0}</p>
                </div>
            </div>
        </>
    );
}
