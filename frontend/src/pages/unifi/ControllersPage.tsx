import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import DataTable, { Column } from "../../components/common/DataTable";
import { unifiPluginApi, UniFiController } from "../../services/unifiPlugin";

function fmtTs(ts: string | null): string {
    if (!ts) return "Never";
    try {
        return new Date(ts).toLocaleString();
    } catch {
        return ts;
    }
}

function statusType(status: string): "healthy" | "warning" | "error" | "neutral" {
    if (status === "healthy") return "healthy";
    if (status === "error") return "error";
    return "neutral";
}

export default function UniFiControllersPage() {
    const [controllers, setControllers] = useState<UniFiController[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        unifiPluginApi
            .listControllers()
            .then(setControllers)
            .catch((e: Error) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (error) return <div className="error-banner">{error}</div>;
    if (loading) return <div className="loading-bar" />;

    const columns: Column<UniFiController>[] = [
        { key: "name", header: "Name" },
        { key: "url", header: "URL" },
        {
            key: "controller_type",
            header: "Type",
            render: (row) => (
                <StatusBadge
                    status="neutral"
                    label={row.controller_type}
                />
            ),
        },
        {
            key: "status",
            header: "Status",
            render: (row) => (
                <StatusBadge status={statusType(row.status)} label={row.status} />
            ),
        },
        { key: "organization_name", header: "Organization" },
        { key: "version", header: "Version" },
        { key: "last_sync_at", header: "Last Sync", render: (row) => fmtTs(row.last_sync_at) },
        {
            key: "last_error",
            header: "Error",
            render: (row) =>
                row.last_error ? (
                    <span className="text-danger" title={row.last_error}>
                        {row.last_error.slice(0, 60)}
                        {row.last_error.length > 60 ? "…" : ""}
                    </span>
                ) : (
                    "—"
                ),
        },
    ];

    return (
        <>
            <PageHeader
                title="UniFi Controllers"
                subtitle={`${controllers.length} controller(s)`}
            />
            {controllers.length === 0 ? (
                <div className="identity-overview-section">
                    <p>No UniFi controllers configured.</p>
                    <p className="page-subtitle">
                        Controllers are registered via the Integrations settings page
                        (UniFi Site Manager API key) or the plugin config file.
                    </p>
                </div>
            ) : (
                <DataTable
                    columns={columns}
                    data={controllers}
                    emptyMessage="No UniFi controllers found"
                />
            )}
        </>
    );
}
