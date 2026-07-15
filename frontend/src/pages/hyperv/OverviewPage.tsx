import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import HyperVHostSelector, { useSelectedHost } from "../../components/hyperv/HyperVHostSelector";
import { hypervApi, HyperVSummary, HyperVHealth } from "../../services/hyperv";

export default function HyperVOverviewPage() {
    const { selectedHostId, hosts, loading: hostsLoading } = useSelectedHost();
    const [summary, setSummary] = useState<HyperVSummary | null>(null);
    const [health, setHealth] = useState<HyperVHealth | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (hostsLoading || selectedHostId === null && hosts.length > 0) return;
        setLoading(true);
        setError(null);
        Promise.all([hypervApi.getSummary(selectedHostId), hypervApi.getHealth(selectedHostId)])
            .then(([s, h]) => { setSummary(s); setHealth(h); })
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, [selectedHostId, hostsLoading]);

    if (hostsLoading) return <div className="loading">Loading…</div>;

    const memPercent = summary && summary.total_memory_gb > 0
        ? Math.round((summary.used_memory_gb / summary.total_memory_gb) * 100)
        : 0;

    return (
        <>
            <PageHeader
                title="Hyper-V Overview"
                subtitle="Virtualization infrastructure at a glance"
                actions={<HyperVHostSelector hosts={hosts} selectedHostId={selectedHostId} onChange={() => {}} />}
            />
            {loading ? (
                <div className="loading">Loading…</div>
            ) : error ? (
                <div className="error-banner">{error}</div>
            ) : summary ? (
                <>
                    {!summary.connected && (
                        <div className="error-banner">
                            Hyper-V host not connected: {summary.error ?? "Unknown error"}
                        </div>
                    )}

                    <div className="hyperv-overview-stats">
                        <div className="hyperv-stat-card">
                            <span className="hyperv-stat-icon">🖥️</span>
                            <div className="hyperv-stat-info">
                                <span className="hyperv-stat-value">{summary.total_vms}</span>
                                <span className="hyperv-stat-label">Total VMs</span>
                            </div>
                        </div>
                        <div className="hyperv-stat-card">
                            <span className="hyperv-stat-icon">▶️</span>
                            <div className="hyperv-stat-info">
                                <span className="hyperv-stat-value">{summary.running}</span>
                                <span className="hyperv-stat-label">Running</span>
                            </div>
                        </div>
                        <div className="hyperv-stat-card">
                            <span className="hyperv-stat-icon">⏹️</span>
                            <div className="hyperv-stat-info">
                                <span className="hyperv-stat-value">{summary.stopped}</span>
                                <span className="hyperv-stat-label">Stopped</span>
                            </div>
                        </div>
                        <div className="hyperv-stat-card">
                            <span className="hyperv-stat-icon">⏸️</span>
                            <div className="hyperv-stat-info">
                                <span className="hyperv-stat-value">{summary.paused}</span>
                                <span className="hyperv-stat-label">Paused</span>
                            </div>
                        </div>
                    </div>

                    <div className="dashboard-row">
                        <div className="dashboard-section">
                            <h3>Resources</h3>
                            <div className="hyperv-resource-bars">
                                <div className="hyperv-resource-item">
                                    <span className="hyperv-resource-label">
                                        CPU Cores: {summary.total_cpu}
                                    </span>
                                </div>
                                <div className="hyperv-resource-item">
                                    <span className="hyperv-resource-label">
                                        Memory: {summary.used_memory_gb} / {summary.total_memory_gb} GB ({memPercent}%)
                                    </span>
                                    <div className="hyperv-progress-bar">
                                        <div
                                            className="hyperv-progress-fill"
                                            style={{ width: `${memPercent}%` }}
                                        />
                                    </div>
                                </div>
                                <div className="hyperv-resource-item">
                                    <span className="hyperv-resource-label">
                                        Storage: {summary.used_storage_gb} / {summary.total_storage_gb} GB
                                    </span>
                                </div>
                            </div>
                        </div>

                        <div className="dashboard-section">
                            <h3>Host Cluster</h3>
                            {summary.host_servers.length > 0 ? (
                                <div className="hyperv-host-list">
                                    {summary.host_servers.map((host) => {
                                        const hostHealth = health?.hosts.find((h) => h.name === host);
                                        return (
                                            <div key={host} className="hyperv-host-item">
                                                <StatusBadge
                                                    status={hostHealth?.status === "healthy" ? "healthy" : "warning"}
                                                    label={host}
                                                />
                                                {hostHealth && (
                                                    <span className="hyperv-host-meta">
                                                        CPU {hostHealth.cpu_percent}% · RAM {hostHealth.memory_percent}%
                                                    </span>
                                                )}
                                            </div>
                                        );
                                    })}
                                </div>
                            ) : (
                                <p className="settings-hint">No host servers detected.</p>
                            )}
                        </div>
                    </div>
                </>
            ) : null}
        </>
    );
}
