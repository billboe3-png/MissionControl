import { useCallback, useEffect, useState } from "react";
import { useVeeamServer } from "../../contexts/VeeamServerContext";
import VeeamPageShell from "../../components/veeam/VeeamPageShell";
import StatusBadge from "../../components/common/StatusBadge";
import { veeamApi, VeeamManagedServer } from "../../services/veeam";

export default function VeeamServersPage() {
    const [servers, setServers] = useState<VeeamManagedServer[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const { selectedServerId } = useVeeamServer();

    const load = useCallback(() => {
        setLoading(true);
        setError(null);
        veeamApi
            .listServers(selectedServerId)
            .then(setServers)
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, [selectedServerId]);

    useEffect(() => {
        load();
    }, [load]);

    const uniqueServers = [...new Set(servers.map((s) => s.server_name).filter(Boolean))];
    const hasMultiServer = uniqueServers.length > 1;

    return (
        <VeeamPageShell title="Managed Servers" onRefresh={load} refreshing={loading}>
            {error && <div className="error-banner">{error}</div>}
            {loading && <div className="loading-bar" />}
            {!error && servers.length === 0 && !loading && (
                <div className="data-table-empty">No servers found.</div>
            )}
            {!error && servers.length > 0 && (
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
                                {hasMultiServer && (
                                    <td style={{ fontSize: "0.8rem", color: "#8b949e" }}>{s.server_name ?? ""}</td>
                                )}
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
                    </tbody>
                </table>
            )}
        </VeeamPageShell>
    );
}
