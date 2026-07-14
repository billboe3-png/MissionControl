import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import { hypervApi, HyperVHealth } from "../../services/hyperv";

function formatUptime(seconds: number): string {
    if (seconds === 0) return "—";
    const d = Math.floor(seconds / 86400);
    const h = Math.floor((seconds % 86400) / 3600);
    if (d > 0) return `${d}d ${h}h`;
    return `${h}h`;
}

export default function HyperVHealthPage() {
    const [health, setHealth] = useState<HyperVHealth | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        hypervApi.getHealth()
            .then(setHealth)
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (loading) return <div className="loading">Loading…</div>;
    if (error) return <div className="error-banner">{error}</div>;
    if (!health) return null;

    return (
        <>
            <PageHeader title="Hyper-V Health" subtitle="Host cluster health status" />
            {health.cluster_summary && (
                <p className="settings-hint">{health.cluster_summary}</p>
            )}
            {health.hosts.length === 0 ? (
                <p className="settings-hint">No host data available.</p>
            ) : (
                <div className="hyperv-health-grid">
                    {health.hosts.map((host) => (
                        <div key={host.name} className="hyperv-health-card">
                            <div className="hyperv-health-header">
                                <h3>{host.name}</h3>
                                <StatusBadge
                                    status={host.status === "healthy" ? "healthy" : "warning"}
                                    label={host.status}
                                />
                            </div>
                            <div className="hyperv-health-metrics">
                                <div className="hyperv-health-metric">
                                    <span className="hyperv-metric-label">CPU</span>
                                    <div className="hyperv-progress-bar">
                                        <div
                                            className={`hyperv-progress-fill ${host.cpu_percent > 80 ? "warning" : ""}`}
                                            style={{ width: `${host.cpu_percent}%` }}
                                        />
                                    </div>
                                    <span className="hyperv-metric-value">{host.cpu_percent}%</span>
                                </div>
                                <div className="hyperv-health-metric">
                                    <span className="hyperv-metric-label">Memory</span>
                                    <div className="hyperv-progress-bar">
                                        <div
                                            className={`hyperv-progress-fill ${host.memory_percent > 80 ? "warning" : ""}`}
                                            style={{ width: `${host.memory_percent}%` }}
                                        />
                                    </div>
                                    <span className="hyperv-metric-value">{host.memory_percent}%</span>
                                </div>
                                <div className="hyperv-health-meta">
                                    <span>VMs: {host.vm_count}</span>
                                    <span>Uptime: {formatUptime(host.uptime_seconds)}</span>
                                    {host.version && <span>Version: {host.version}</span>}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </>
    );
}
