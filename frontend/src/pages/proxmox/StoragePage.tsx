import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import EmptyState from "../../components/common/EmptyState";
import { proxmoxApi, ProxmoxStorage } from "../../services/proxmox";

function formatBytes(bytes: number): string {
    if (bytes >= 1099511627776) return `${(bytes / 1099511627776).toFixed(1)} TB`;
    if (bytes >= 1073741824) return `${(bytes / 1073741824).toFixed(1)} GB`;
    if (bytes >= 1048576) return `${(bytes / 1048576).toFixed(0)} MB`;
    return `${bytes} B`;
}

export default function StoragePage() {
    const [storage, setStorage] = useState<ProxmoxStorage[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        proxmoxApi.listStorage()
            .then(setStorage)
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (loading) return <div className="loading-bar" />;

    return (
        <>
            <PageHeader title="Storage" subtitle="Proxmox storage pools" />
            {error && <div className="error-banner">{error}</div>}
            {storage.length === 0 ? (
                <EmptyState icon="💾" title="No storage" description="No storage pools found." />
            ) : (
                <div className="proxmox-storage-table">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Type</th>
                                <th>Node</th>
                                <th>Size</th>
                                <th>Used</th>
                                <th>Usage</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {storage.map((pool) => {
                                const usagePercent = pool.size_bytes > 0
                                    ? Math.round((pool.used_bytes / pool.size_bytes) * 100)
                                    : 0;
                                return (
                                    <tr key={pool.id}>
                                        <td>{pool.name}</td>
                                        <td>{pool.type.toUpperCase()}</td>
                                        <td>{pool.node}</td>
                                        <td>{formatBytes(pool.size_bytes)}</td>
                                        <td>{formatBytes(pool.used_bytes)}</td>
                                        <td>
                                            <div className="proxmox-storage-usage">
                                                <div className="proxmox-progress-bar">
                                                    <div
                                                        className={`proxmox-progress-fill ${usagePercent > 85 ? "warning" : ""}`}
                                                        style={{ width: `${usagePercent}%` }}
                                                    />
                                                </div>
                                                <span>{usagePercent}%</span>
                                            </div>
                                        </td>
                                        <td>{pool.status}</td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            )}
        </>
    );
}
