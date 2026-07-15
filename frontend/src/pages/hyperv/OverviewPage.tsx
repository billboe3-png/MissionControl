import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import HyperVHostSelector, { useSelectedHost } from "../../components/hyperv/HyperVHostSelector";
import { hypervApi, HyperVSummary, HyperVHealthHost } from "../../services/hyperv";

function formatUptime(seconds: number): string {
    if (seconds === 0) return "\u2014";
    const d = Math.floor(seconds / 86400);
    const h = Math.floor((seconds % 86400) / 3600);
    if (d > 0) return `${d}d ${h}h`;
    return `${h}h`;
}

function UsageBar({ percent, label }: { percent: number; label: string }) {
    const cls = percent >= 90 ? "danger" : percent >= 70 ? "warning" : "";
    return (
        <div className="hyperv-resource-item">
            <span className="hyperv-resource-label">{label}: {percent}%</span>
            <div className="hyperv-progress-bar">
                <div className={`hyperv-progress-fill ${cls}`} style={{ width: `${percent}%` }} />
            </div>
        </div>
    );
}

export default function HyperVOverviewPage() {
    const { selectedHostId, hosts, loading: hostsLoading, setSelectedHostId } = useSelectedHost();
    const [summary, setSummary] = useState<HyperVSummary | null>(null);
    const [allHostsHealth, setAllHostsHealth] = useState<HyperVHealthHost[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        if (hostsLoading) return;
        setLoading(true);
        setError(null);

        const loadAll = async () => {
            const s = await hypervApi.getSummary(selectedHostId);
            setSummary(s);

            const hostsHealth: HyperVHealthHost[] = [];
            for (const h of hosts) {
                try {
                    const health = await hypervApi.getHealth(h.id);
                    if (health.hosts?.length) hostsHealth.push(...health.hosts);
                } catch { /* skip failed host */ }
            }
            setAllHostsHealth(hostsHealth);
        };

        loadAll()
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, [selectedHostId, hostsLoading, hosts]);

    const handleHostClick = (hostId: number) => {
        setSelectedHostId(hostId);
        navigate("/hyperv/vms");
    };

    if (hostsLoading) return <div className="loading">Loading\u2026</div>;

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
                <div className="loading">Loading\u2026</div>
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

                    {allHostsHealth.length > 0 && (
                        <div className="dashboard-section">
                            <h3>Cluster Hosts</h3>
                            <div className="hyperv-host-cards">
                                {allHostsHealth.map((host) => (
                                    <div
                                        key={host.name}
                                        className={`hyperv-host-card ${host.status === "healthy" ? "healthy" : "warning"}`}
                                        onClick={() => {
                                            const match = hosts.find((h) => h.name === host.name);
                                            if (match) handleHostClick(match.id);
                                        }}
                                        role="button"
                                        tabIndex={0}
                                        onKeyDown={(e) => {
                                            if (e.key === "Enter") {
                                                const match = hosts.find((h) => h.name === host.name);
                                                if (match) handleHostClick(match.id);
                                            }
                                        }}
                                    >
                                        <div className="hyperv-host-card-header">
                                            <StatusBadge
                                                status={host.status === "healthy" ? "healthy" : "warning"}
                                                label={host.name}
                                            />
                                            {host.version && (
                                                <span className="hyperv-host-version">v{host.version}</span>
                                            )}
                                        </div>
                                        <div className="hyperv-host-card-body">
                                            <UsageBar percent={host.cpu_percent} label="CPU" />
                                            <UsageBar percent={host.memory_percent} label="Memory" />
                                        </div>
                                        <div className="hyperv-host-card-footer">
                                            <span>VMs: {host.vm_count}</span>
                                            <span>Uptime: {formatUptime(host.uptime_seconds)}</span>
                                            <span className="hyperv-host-card-action">View VMs →</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    <div className="dashboard-row">
                        <div className="dashboard-section">
                            <h3>Resources</h3>
                            <div className="hyperv-resource-bars">
                                <div className="hyperv-resource-item">
                                    <span className="hyperv-resource-label">
                                        CPU Cores: {summary.total_cpu}
                                    </span>
                                </div>
                                <UsageBar percent={memPercent} label={`Memory: ${summary.used_memory_gb} / ${summary.total_memory_gb} GB`} />
                                <div className="hyperv-resource-item">
                                    <span className="hyperv-resource-label">
                                        Storage: {summary.used_storage_gb} / {summary.total_storage_gb} GB
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                </>
            ) : null}
        </>
    );
}
