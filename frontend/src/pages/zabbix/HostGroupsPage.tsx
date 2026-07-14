import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import HostGroupTable from "../../components/zabbix/HostGroupTable";
import { zabbixApi, ZabbixHostGroupsResponse } from "../../services/zabbix";

export default function HostGroupsPage() {
    const [data, setData] = useState<ZabbixHostGroupsResponse | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        zabbixApi.getGroups()
            .then(setData)
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (error) return <div className="error-banner">{error}</div>;
    if (loading) return <div className="loading">Loading…</div>;

    return (
        <>
            <PageHeader title="Host Groups" subtitle={`Host groups (${data?.total_count ?? 0})`} />
            <HostGroupTable groups={data?.groups ?? []} />
        </>
    );
}
