import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import DataTable, { Column } from "../../components/common/DataTable";
import { unifiPluginApi, UniFiWirelessNetwork } from "../../services/unifiPlugin";

export default function UniFiWirelessPage() {
    const [networks, setNetworks] = useState<UniFiWirelessNetwork[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        unifiPluginApi
            .listWireless()
            .then(setNetworks)
            .catch((e: Error) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (error) return <div className="error-banner">{error}</div>;
    if (loading) return <div className="loading-bar" />;

    const columns: Column<UniFiWirelessNetwork>[] = [
        { key: "ssid", header: "SSID" },
        { key: "security", header: "Security" },
        { key: "vlan", header: "VLAN" },
        {
            key: "is_guest",
            header: "Guest",
            render: (row) => (row.is_guest ? "Yes" : "No"),
        },
        {
            key: "is_hidden",
            header: "Hidden",
            render: (row) => (row.is_hidden ? "Yes" : "No"),
        },
        {
            key: "has_alerts",
            header: "Alerts",
            render: (row) => (
                <StatusBadge
                    status={row.has_alerts ? "warning" : "healthy"}
                    label={row.has_alerts ? "Has Alerts" : "OK"}
                />
            ),
        },
    ];

    return (
        <>
            <PageHeader
                title="UniFi Wireless Networks"
                subtitle={`${networks.length} SSID(s)`}
            />
            <DataTable
                columns={columns}
                data={networks}
                emptyMessage="No UniFi wireless networks found"
            />
        </>
    );
}
