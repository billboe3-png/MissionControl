import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import DataTable, { Column } from "../../components/common/DataTable";
import { unifiPluginApi, UniFiClient } from "../../services/unifiPlugin";

function fmtBytes(n: number): string {
    if (!n) return "0 B";
    const units = ["B", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(n) / Math.log(1024));
    return `${(n / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
}

export default function UniFiClientsPage() {
    const [clients, setClients] = useState<UniFiClient[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        unifiPluginApi
            .listClients()
            .then(setClients)
            .catch((e: Error) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (error) return <div className="error-banner">{error}</div>;
    if (loading) return <div className="loading-bar" />;

    const columns: Column<UniFiClient>[] = [
        { key: "hostname", header: "Hostname" },
        { key: "ip_address", header: "IP Address" },
        { key: "mac_address", header: "MAC" },
        { key: "vlan", header: "VLAN" },
        {
            key: "is_wired",
            header: "Connection",
            render: (row) => (
                <StatusBadge
                    status={row.is_wired ? "info" : "neutral"}
                    label={row.is_wired ? "Wired" : "Wireless"}
                />
            ),
        },
        { key: "connected_ap_name", header: "AP" },
        { key: "connected_switch_name", header: "Switch" },
        { key: "is_guest", header: "Guest", render: (row) => (row.is_guest ? "Yes" : "No") },
        {
            key: "rx_bytes",
            header: "Downloaded",
            render: (row) => fmtBytes(row.rx_bytes),
        },
        {
            key: "tx_bytes",
            header: "Uploaded",
            render: (row) => fmtBytes(row.tx_bytes),
        },
    ];

    return (
        <>
            <PageHeader title="UniFi Clients" subtitle={`${clients.length} connected client(s)`} />
            <DataTable columns={columns} data={clients} emptyMessage="No UniFi clients found" />
        </>
    );
}
