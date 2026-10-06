import { useCallback, useEffect, useState } from "react";
import { useVeeamServer } from "../../contexts/VeeamServerContext";
import VeeamPageShell from "../../components/veeam/VeeamPageShell";
import StatusBadge from "../../components/common/StatusBadge";
import {
    veeamApi,
    VeeamRepository,
} from "../../services/veeam";

export default function VeeamRepositoriesPage() {
    const [repos, setRepos] = useState<VeeamRepository[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const { selectedServerId } = useVeeamServer();

    const load = useCallback(() => {
        setLoading(true);
        setError(null);
        veeamApi
            .listRepositories(selectedServerId)
            .then(setRepos)
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, [selectedServerId]);

    useEffect(() => {
        load();
    }, [load]);

    return (
        <VeeamPageShell title="Veeam Repositories" onRefresh={load} refreshing={loading}>
            {error && <div className="error-banner">{error}</div>}
            {loading && <div className="loading-bar" />}
            {!error && repos.length === 0 && !loading && (
                <div className="data-table-empty">No repositories found.</div>
            )}
            {!error && repos.length > 0 && (
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
        </VeeamPageShell>
    );
}
