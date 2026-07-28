import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import DataTable, { Column } from "../../components/common/DataTable";
import { unifiPluginApi, UniFiSite } from "../../services/unifiPlugin";

function wanType(status: string): "healthy" | "warning" | "error" | "neutral" {
    if (status === "online" || status === "up") return "healthy";
    if (status === "down" || status === "offline") return "error";
    return "neutral";
}

export default function UniFiSitesPage() {
    const [sites, setSites] = useState<UniFiSite[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        unifiPluginApi
            .listSites()
            .then(setSites)
            .catch((e: Error) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (error) return <div className="error-banner">{error}</div>;
    if (loading) return <div className="loading-bar" />;

    const columns: Column<UniFiSite>[] = [
        { key: "name", header: "Name" },
        { key: "description", header: "Description" },
        { key: "isp_name", header: "ISP" },
        {
            key: "wan_status",
            header: "WAN",
            render: (row) => (
                <StatusBadge status={wanType(row.wan_status)} label={row.wan_status} />
            ),
        },
        { key: "num_devices", header: "Devices" },
        { key: "num_clients", header: "Clients" },
        { key: "timezone", header: "Timezone" },
    ];

    return (
        <>
            <PageHeader title="UniFi Sites" subtitle={`${sites.length} site(s)`} />
            <DataTable columns={columns} data={sites} emptyMessage="No UniFi sites found" />
        </>
    );
}
