import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import { veeamApi, VeeamManagedServer } from "../../services/veeam";

export default function VeeamServersPage() {
    const [servers, setServers] = useState<VeeamManagedServer[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        veeamApi
            .listServers()
            .then(setServers)
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    const uniqueServers = [...new Set(servers.map((s) => s.server_name).filter(Boolean))];
    const hasMultiServer = uniqueServers.length > 1;

    if (loading) return <div className="loading-bar" />;
    if (error) return <div className="error-banner">{error}</div>;

    return (
        <>
            <PageHeader title="Managed Servers" subtitle={`${servers.length} servers managed by ${hasMultiServer ? uniqueServers.length + " Veeam servers" : "Veeam"}`} />
            <table className="data-table">
                <thead>
                    <tr>
                        {hasMultiServer && <th>Veeam Server</th>}
                        <th>Name</th>
                        <th>Type</th>
                        <th>Description</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {servers.map((s) => (
                        <tr key={`${s.server_name ?? ""}-${s.id}`}>
                            {hasMultiServer && <td style={{ fontSize: "0.8rem", color: "#8b949e" }}>{s.server_name ?? ""}</td>}
                            <td>{s.name}</td>
                            <td>{s.type}</td>
                            <td>{typeof s.description === "string" ? s.description : "-"}</td>
                            <td>
                                <StatusBadge
                                    status={s.status === "Available" ? "healthy" : "warning"}
                                    label={s.status ?? "Unknown"}
                                />
                            </td>
                        </tr>
                    ))}
                    {servers.length === 0 && (
                        <tr><td colSpan={hasMultiServer ? 5 : 4} className="empty-state">No servers found</td></tr>
                    )}
                </tbody>
            </table>
        </>
    );
}
