import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import { veeamApi, VeeamRepository, formatBytes } from "../../services/veeam";

export default function VeeamRepositoriesPage() {
    const [repos, setRepos] = useState<VeeamRepository[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        veeamApi
            .listRepositories()
            .then(setRepos)
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (loading) return <div className="loading-bar" />;
    if (error) return <div className="error-banner">{error}</div>;

    return (
        <>
            <PageHeader title="Backup Repositories" subtitle="Veeam backup storage locations" />
            <table className="data-table">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Type</th>
                        <th>Path</th>
                        <th>Status</th>
                        <th>Description</th>
                    </tr>
                </thead>
                <tbody>
                    {repos.map((repo) => (
                        <tr key={repo.id}>
                            <td>{repo.name}</td>
                            <td>{repo.type}</td>
                            <td className="monospace">{repo.repository?.path ?? "-"}</td>
                            <td>
                                <StatusBadge
                                    status="healthy"
                                    label="Available"
                                />
                            </td>
                            <td>{repo.description ?? "-"}</td>
                        </tr>
                    ))}
                    {repos.length === 0 && (
                        <tr><td colSpan={5} className="empty-state">No repositories found</td></tr>
                    )}
                </tbody>
            </table>
        </>
    );
}
