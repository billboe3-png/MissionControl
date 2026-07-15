import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import EmptyState from "../../components/common/EmptyState";
import HyperVHostSelector, { useSelectedHost } from "../../components/hyperv/HyperVHostSelector";
import { hypervApi, HyperVStorage } from "../../services/hyperv";

function formatBytes(bytes: number): string {
    if (bytes >= 1099511627776) return `${(bytes / 1099511627776).toFixed(1)} TB`;
    if (bytes >= 1073741824) return `${(bytes / 1073741824).toFixed(1)} GB`;
    if (bytes >= 1048576) return `${(bytes / 1048576).toFixed(0)} MB`;
    return `${bytes} B`;
}

export default function StoragePage() {
    const { selectedHostId, hosts, loading: hostsLoading } = useSelectedHost();
    const [storage, setStorage] = useState<HyperVStorage[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (hostsLoading) return;
        setLoading(true);
        hypervApi.listStorage(selectedHostId)
            .then(setStorage)
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, [selectedHostId, hostsLoading]);

    if (hostsLoading) return <div className="loading">Loading…</div>;

    return (
        <>
            <PageHeader
                title="Virtual Storage"
                subtitle="Hyper-V virtual hard disks"
                actions={<HyperVHostSelector hosts={hosts} selectedHostId={selectedHostId} onChange={() => {}} />}
            />
            {loading ? (
                <div className="loading">Loading…</div>
            ) : (
                <>
                    {error && <div className="error-banner">{error}</div>}
                    {storage.length === 0 ? (
                        <EmptyState icon="💾" title="No storage" description="No virtual hard disks found." />
                    ) : (
                        <div className="hyperv-storage-table">
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>Name</th>
                                        <th>VM</th>
                                        <th>Type</th>
                                        <th>Format</th>
                                        <th>Size</th>
                                        <th>Used</th>
                                        <th>Usage</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {storage.map((disk) => {
                                        const usagePercent = disk.size_bytes > 0
                                            ? Math.round((disk.used_bytes / disk.size_bytes) * 100)
                                            : 0;
                                        return (
                                            <tr key={disk.id}>
                                                <td>{disk.name}</td>
                                                <td>{disk.vm_name ?? "—"}</td>
                                                <td>{disk.type.toUpperCase()}</td>
                                                <td>{disk.format ?? "—"}</td>
                                                <td>{formatBytes(disk.size_bytes)}</td>
                                                <td>{formatBytes(disk.used_bytes)}</td>
                                                <td>
                                                    <div className="hyperv-storage-usage">
                                                        <div className="hyperv-progress-bar">
                                                            <div
                                                                className={`hyperv-progress-fill ${usagePercent > 85 ? "warning" : ""}`}
                                                                style={{ width: `${usagePercent}%` }}
                                                            />
                                                        </div>
                                                        <span>{usagePercent}%</span>
                                                    </div>
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    )}
                </>
            )}
        </>
    );
}
