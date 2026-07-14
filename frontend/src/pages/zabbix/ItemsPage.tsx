import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import ItemTable from "../../components/zabbix/ItemTable";
import StatusBadge from "../../components/common/StatusBadge";
import { zabbixApi, ZabbixItemsResponse } from "../../services/zabbix";

export default function ItemsPage() {
    const [data, setData] = useState<ZabbixItemsResponse | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        zabbixApi.getItems()
            .then(setData)
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (error) return <div className="error-banner">{error}</div>;
    if (loading) return <div className="loading">Loading…</div>;

    return (
        <>
            <PageHeader title="Items" subtitle={`Collected items (${data?.total_count ?? 0})`} />
            <div className="identity-overview-section">
                <p><strong>Supported:</strong> <StatusBadge status="healthy" label={String(data?.supported_count ?? 0)} /> | <strong>Unsupported:</strong> <StatusBadge status="warning" label={String(data?.unsupported_count ?? 0)} /></p>
            </div>
            <ItemTable items={data?.items ?? []} />
        </>
    );
}
