import { useEffect, useState } from "react";
import { useVeeamServer } from "../../contexts/VeeamServerContext";
import { ServerSelector } from "../../components/veeam/ServerSelector";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import {
    veeamApi,
    VeeamRepository,
} from "../../services/veeam";

export default function VeeamRepositoriesPage() {
    const [repos, setRepos] = useState<VeeamRepository[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const { servers, selectedServerId } = useVeeamServer();

    useEffect(() => {
        // Servers fetched by VeeamServerProvider
    }, [selectedServerId]);

    useEffect(() => {
        if (loading) return;
        veeamApi.listRepositories(selectedServerId).then((r) => {
            setRepos(r);
        })
        .catch((e) => setError(e.message))
        .finally(() => setLoading(false));
    }, [selectedServerId, loading]);

    const selectedServerName = servers.length > 0 ? servers.find(s => s.id === selectedServerId)?.name : "Veeam Server";

    if (loading) return <div className="loading-bar" />;
    if (error) return <div className="error-banner">{error}</div>;

    return (
        <>
            <PageHeader
                title="Veeam Repositories"
                subtitle={`${selectedServerName ?? "Veeam Server"} v1.0`}
            />
            {error && <div className="error-banner">{error}</div>}
            {loading && <div className="loading-bar" />}
            {!error && !loading && (
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Type</th>
                            <th>Path</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {repos.map((repo) => {
                            return (
                                <tr key={repo.id}>
                                    <td>{repo.name}</td>
                                    <td>{repo.type}</td>
                                    <td>{repo.repository?.path ?? "-"}</td>
                                    <td>
                                        <StatusBadge
                                            status={repo.status === "Available" ? "healthy" : "warning"}
                                            label={repo.status ?? "Unknown"}
                                        />
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            )}
        {servers.length > 1 && <ServerSelector />}
        </>
    );
}
