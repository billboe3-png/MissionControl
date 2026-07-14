import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import TemplateTable from "../../components/zabbix/TemplateTable";
import { zabbixApi, ZabbixTemplatesResponse } from "../../services/zabbix";

export default function TemplatesPage() {
    const [data, setData] = useState<ZabbixTemplatesResponse | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        zabbixApi.getTemplates()
            .then(setData)
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (error) return <div className="error-banner">{error}</div>;
    if (loading) return <div className="loading">Loading…</div>;

    return (
        <>
            <PageHeader title="Templates" subtitle={`Monitoring templates (${data?.total_count ?? 0})`} />
            <TemplateTable templates={data?.templates ?? []} />
        </>
    );
}
