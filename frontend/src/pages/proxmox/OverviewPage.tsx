import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import { proxmoxApi, ProxmoxSummary, ProxmoxHealth } from "../../services/proxmox";

export default function ProxmoxOverviewPage() {
    const [summary, setSummary] = useState<ProxmoxSummary | null>(null);
    const [health, setHealth] = useState<ProxmoxHealth | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        Promise.all([proxmoxApi.getSummary(), proxmoxApi.getHealth()])
            .then(([s, h]) => { setSummary(s); setHealth(h); })
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (loading) return <div className="loading-bar" />;
    if (error) return <div className="error-banner">{error}</div>;
    if (!summary) return null;

    const memPercent = summary.total_memory_gb > 0
        ? Math.round((summary.used_memory_gb / summary.total_memory_gb) * 100)
        : 0;

    const storPercent = summary.total_storage_gb > 0
        ? Math.round((summary.used_storage_gb / summary.total_storage_gb) * 100)
        : 0;

    return (
        <>
            <PageHeader title="Proxmox Overview" subtitle="Cluster infrastructure at a glance" />

            {!summary.connected && (
                <div className="error-banner">
                    Proxmox cluster not connected: {summary.error ?? "Unknown error"}
                </div>
            )}

            <div className="proxmox-overview-stats">
                <div className="proxmox-stat-card">
                    <span className="proxmox-stat-icon">🖥️</span>
                    <div className="proxmox-stat-info">
                        <span className="proxmox-stat-value">{summary.nodes_online}/{summary.nodes_total}</span>
                        <span className="proxmox-stat-label">Nodes Online</span>
                    </div>
                </div>
                <div className="proxmox-stat-card">
                    <span className="proxmox-stat-icon">💻</span>
                    <div className="proxmox-stat-info">
                        <span className="proxmox-stat-value">{summary.running}/{summary.total_vms}</span>
                        <span className="proxmox-stat-label">VMs Running</span>
                    </div>
                </div>
                <div className="proxmox-stat-card">
                    <span className="proxmox-stat-icon">📦</span>
                    <div className="proxmox-stat-info">
                        <span className="proxmox-stat-value">{summary.running_lxc}/{summary.total_lxc}</span>
                        <span className="proxmox-stat-label">LXCs Running</span>
                    </div>
                </div>
                <div className="proxmox-stat-card">
                    <span className="proxmox-stat-icon">💾</span>
                    <div className="proxmox-stat-info">
                        <span className="proxmox-stat-value">{summary.storage_count}</span>
                        <span className="proxmox-stat-label">Storage Pools</span>
                    </div>
                </div>
            </div>

            <div className="dashboard-row">
                <div className="dashboard-section">
                    <h3>Resources</h3>
                    <div className="proxmox-resource-bars">
                        <div className="proxmox-resource-item">
                            <span className="proxmox-resource-label">
                                CPU Cores: {summary.total_cpu}
                            </span>
                        </div>
                        <div className="proxmox-resource-item">
                            <span className="proxmox-resource-label">
                                Memory: {summary.used_memory_gb} / {summary.total_memory_gb} GB ({memPercent}%)
                            </span>
                            <div className="proxmox-progress-bar">
                                <div
                                    className={`proxmox-progress-fill ${memPercent > 85 ? "warning" : ""}`}
                                    style={{ width: `${memPercent}%` }}
                                />
                            </div>
                        </div>
                        <div className="proxmox-resource-item">
                            <span className="proxmox-resource-label">
                                Storage: {summary.used_storage_gb} / {summary.total_storage_gb} GB ({storPercent}%)
                            </span>
                            <div className="proxmox-progress-bar">
                                <div
                                    className={`proxmox-progress-fill ${storPercent > 85 ? "warning" : ""}`}
                                    style={{ width: `${storPercent}%` }}
                                />
                            </div>
                        </div>
                    </div>
                </div>

                <div className="dashboard-section">
                    <h3>Cluster Nodes</h3>
                    {health && health.nodes.length > 0 ? (
                        <div className="proxmox-node-list">
                            {health.nodes.map((node) => (
                                <div key={node.name} className="proxmox-node-item">
                                    <StatusBadge
                                        status={node.status === "online" ? "healthy" : "error"}
                                        label={node.name}
                                    />
                                    <span className="proxmox-node-meta">
                                        CPU {node.cpu_percent}% · RAM {node.memory_percent}% · VMs {node.vm_count}
                                    </span>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="settings-hint">No node data available.</p>
                    )}
                </div>
            </div>
        </>
    );
}
