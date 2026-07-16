import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import MapCard from "../../components/zabbix/MapCard";
import { zabbixApi, ZabbixMapsResponse } from "../../services/zabbix";

export default function MapsPage() {
    const [data, setData] = useState<ZabbixMapsResponse | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        zabbixApi.getMaps()
            .then(setData)
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (error) return <div className="error-banner">{error}</div>;
    if (loading) return <div className="loading-bar" />;

    return (
        <>
            <PageHeader title="Maps" subtitle={`Network maps (${data?.total_count ?? 0})`} />
            <div className="ad-info-grid">
                {(data?.maps ?? []).map((m) => (
                    <MapCard key={m.sysmapid} map={m} />
                ))}
                {(!data || data.total_count === 0) && <p>No maps found</p>}
            </div>
        </>
    );
}
