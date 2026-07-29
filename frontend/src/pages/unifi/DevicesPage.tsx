import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import DataTable, { Column } from "../../components/common/DataTable";
import { unifiPluginApi, UniFiDevice } from "../../services/unifiPlugin";
import { fmtUptime } from "./DashboardPage";

const deviceTypeOptions = [
    { value: "", label: "All Types" },
    { value: "access_point", label: "Access Points" },
    { value: "switch", label: "Switches" },
    { value: "gateway", label: "Gateways" },
    { value: "unknown", label: "Other" },
];

function statusType(status: string): "healthy" | "warning" | "error" | "neutral" {
    if (status === "online") return "healthy";
    if (status === "offline") return "error";
    if (status === "pending" || status === "connected") return "warning";
    return "neutral";
}

export default function UniFiDevicesPage() {
    const [devices, setDevices] = useState<UniFiDevice[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [typeFilter, setTypeFilter] = useState<string>("");

    useEffect(() => {
        setLoading(true);
        unifiPluginApi
            .listDevices(undefined, undefined, typeFilter || undefined)
            .then(setDevices)
            .catch((e: Error) => setError(e.message))
            .finally(() => setLoading(false));
    }, [typeFilter]);

    if (error) return <div className="error-banner">{error}</div>;
    if (loading) return <div className="loading-bar" />;

    const columns: Column<UniFiDevice>[] = [
        { key: "name", header: "Name" },
        { key: "model", header: "Model" },
        { key: "device_type", header: "Type" },
        { key: "ip_address", header: "IP Address" },
        {
            key: "status",
            header: "Status",
            render: (row) => (
                <StatusBadge status={statusType(row.status)} label={row.status} />
            ),
        },
        { key: "firmware_version", header: "Firmware" },
        {
            key: "cpu_utilization",
            header: "CPU",
            render: (row) => `${row.cpu_utilization.toFixed(0)}%`,
        },
        {
            key: "memory_utilization",
            header: "Memory",
            render: (row) => `${row.memory_utilization.toFixed(0)}%`,
        },
        {
            key: "uptime_seconds",
            header: "Uptime",
            render: (row) => fmtUptime(row.uptime_seconds),
        },
    ];

    return (
        <>
            <PageHeader
                title="UniFi Devices"
                subtitle={`${devices.length} device(s)`}
            />
            <div className="fleet-toolbar">
                <select
                    className="form-input fleet-filter"
                    value={typeFilter}
                    onChange={(e) => setTypeFilter(e.target.value)}
                >
                    {deviceTypeOptions.map((o) => (
                        <option key={o.value} value={o.value}>
                            {o.label}
                        </option>
                    ))}
                </select>
            </div>
            <DataTable columns={columns} data={devices} emptyMessage="No UniFi devices found" />
        </>
    );
}
