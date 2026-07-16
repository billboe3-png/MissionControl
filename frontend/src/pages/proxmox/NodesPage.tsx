import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import EmptyState from "../../components/common/EmptyState";
import { proxmoxApi, ProxmoxNode } from "../../services/proxmox";

function formatUptime(seconds: number): string {
    if (seconds === 0) return "—";
    const d = Math.floor(seconds / 86400);
    const h = Math.floor((seconds % 86400) / 3600);
    if (d > 0) return `${d}d ${h}h`;
    return `${h}h`;
}

const statusColors: Record<string, "healthy" | "error"> = {
    online: "healthy",
    offline: "error",
};

export default function NodesPage() {
    const [nodes, setNodes] = useState<ProxmoxNode[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        proxmoxApi.listNodes()
            .then(setNodes)
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (loading) return <div className="loading-bar" />;

    return (
        <>
            <PageHeader title="Cluster Nodes" subtitle="Proxmox node status and resource usage" />
            {error && <div className="error-banner">{error}</div>}
            {nodes.length === 0 ? (
                <EmptyState icon="🖥️" title="No nodes" description="No cluster nodes found." />
            ) : (
                <div className="proxmox-nodes-table">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Status</th>
                                <th>CPU</th>
                                <th>Memory</th>
                                <th>Disk</th>
                                <th>Uptime</th>
                                <th>Version</th>
                            </tr>
                        </thead>
                        <tbody>
                            {nodes.map((node) => {
                                const memPercent = node.memory_total_mb > 0
                                    ? Math.round((node.memory_used_mb / node.memory_total_mb) * 100)
                                    : 0;
                                const diskPercent = node.disk_total_gb > 0
                                    ? Math.round((node.disk_used_gb / node.disk_total_gb) * 100)
                                    : 0;
                                return (
                                    <tr key={node.name}>
                                        <td>{node.name}</td>
                                        <td>
                                            <StatusBadge
                                                status={statusColors[node.status] ?? "neutral"}
                                                label={node.status}
                                            />
                                        </td>
                                        <td>{node.cpu_percent}%</td>
                                        <td>{node.memory_used_mb} / {node.memory_total_mb} MB ({memPercent}%)</td>
                                        <td>{node.disk_used_gb} / {node.disk_total_gb} GB ({diskPercent}%)</td>
                                        <td>{formatUptime(node.uptime_seconds)}</td>
                                        <td>{node.version}</td>
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
