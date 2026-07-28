import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import DataTable, { Column } from "../../components/common/DataTable";
import { unifiPluginApi, UniFiAlert } from "../../services/unifiPlugin";

function severityType(sev: string): "healthy" | "warning" | "error" | "info" | "neutral" {
    switch (sev.toLowerCase()) {
        case "critical":
        case "error":
            return "error";
        case "warning":
            return "warning";
        case "info":
            return "info";
        default:
            return "neutral";
    }
}

function fmtTs(ts: string | null): string {
    if (!ts) return "—";
    try {
        return new Date(ts).toLocaleString();
    } catch {
        return ts;
    }
}

export default function UniFiAlertsPage() {
    const [alerts, setAlerts] = useState<UniFiAlert[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        unifiPluginApi
            .listAlerts()
            .then(setAlerts)
            .catch((e: Error) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (error) return <div className="error-banner">{error}</div>;
    if (loading) return <div className="loading-bar" />;

    const columns: Column<UniFiAlert>[] = [
        {
            key: "severity",
            header: "Severity",
            render: (row) => (
                <StatusBadge status={severityType(row.severity)} label={row.severity} />
            ),
        },
        { key: "device_name", header: "Device" },
        { key: "message", header: "Message" },
        { key: "timestamp", header: "Time", render: (row) => fmtTs(row.timestamp) },
        {
            key: "is_acknowledged",
            header: "Ack",
            render: (row) => (row.is_acknowledged ? "Yes" : "No"),
        },
    ];

    return (
        <>
            <PageHeader title="UniFi Alerts" subtitle={`${alerts.length} alert(s)`} />
            <DataTable columns={columns} data={alerts} emptyMessage="No UniFi alerts found" />
        </>
    );
}
