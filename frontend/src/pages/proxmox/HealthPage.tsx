import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import { proxmoxApi, ProxmoxHealth, ProxmoxHealthNode } from "../../services/proxmox";

function formatUptime(seconds: number): string {
    if (seconds === 0) return "—";
    const d = Math.floor(seconds / 86400);
    const h = Math.floor((seconds % 86400) / 3600);
    if (d > 0) return `${d}d ${h}h`;
    return `${h}h`;
}

function NodeCard({ node }: { node: ProxmoxHealthNode }) {
    return (
        <div className="proxmox-health-card">
            <div className="proxmox-health-header">
                <h3>{node.name}</h3>
                <StatusBadge
                    status={node.status === "healthy" ? "healthy" : "warning"}
                    label={node.status}
                />
            </div>
            <div className="proxmox-health-metrics">
                <div className="proxmox-health-metric">
                    <span className="proxmox-metric-label">CPU</span>
                    <div className="proxmox-progress-bar">
                        <div
                            className={`proxmox-progress-fill ${node.cpu_percent > 80 ? "warning" : ""}`}
                            style={{ width: `${node.cpu_percent}%` }}
                        />
                    </div>
                    <span className="proxmox-metric-value">
                        {node.cpu_percent}%
                    </span>
                </div>
                <div className="proxmox-health-metric">
                    <span className="proxmox-metric-label">Memory</span>
                    <div className="proxmox-progress-bar">
                        <div
                            className={`proxmox-progress-fill ${node.memory_percent > 80 ? "warning" : ""}`}
                            style={{ width: `${node.memory_percent}%` }}
                        />
                    </div>
                    <span className="proxmox-metric-value">
                        {node.memory_percent}%
                    </span>
                </div>
                <div className="proxmox-health-meta">
                    <span>VMs: {node.vm_count}</span>
                    <span>
                        Uptime: {formatUptime(node.uptime_seconds)}
                    </span>
                </div>
            </div>
        </div>
    );
}

export default function ProxmoxHealthPage() {
    const [health, setHealth] = useState<ProxmoxHealth | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        proxmoxApi.getHealth()
            .then(setHealth)
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (loading) return <div className="loading-bar" />;
    if (error) return <div className="error-banner">{error}</div>;
    if (!health) return null;

    return (
        <>
            <PageHeader
                title="Cluster Health"
                subtitle="Proxmox cluster node health status"
            />
            {health.cluster_summary && (
                <p className="settings-hint">{health.cluster_summary}</p>
            )}
            {health.nodes.length === 0 ? (
                <p className="settings-hint">
                    No node data available.
                </p>
            ) : (
                <div className="proxmox-health-grid">
                    {health.nodes.map((node) => (
                        <NodeCard key={node.name} node={node} />
                    ))}
                </div>
            )}
        </>
    );
}
