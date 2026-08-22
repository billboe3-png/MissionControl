import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import { hypervApi, HyperVHealthHost } from "../../services/hyperv";

function formatUptime(seconds: number): string {
    if (seconds === 0) return "—";
    const d = Math.floor(seconds / 86400);
    const h = Math.floor((seconds % 86400) / 3600);
    if (d > 0) return `${d}d ${h}h`;
    return `${h}h`;
}

export default function HyperVHealthPage() {
    const [health, setHealth] = useState<HyperVHealthHost[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let cancelled = false;
        setLoading(true);
        setError(null);
        (async () => {
            try {
                const hostList = await hypervApi.listHosts();
                if (cancelled) return;
                const allHealth: HyperVHealthHost[] = [];
                for (const h of hostList) {
                    try {
                        const res = await hypervApi.getHealth(h.id);
                        if (cancelled) return;
                        if (res.hosts?.length) allHealth.push(...res.hosts);
                    } catch { /* skip failed host */ }
                }
                if (cancelled) return;
                setHealth(allHealth);
            } catch (e: unknown) {
                if (cancelled) return;
                setError(e instanceof Error ? e.message : "Failed to load health data");
            } finally {
                if (!cancelled) setLoading(false);
            }
        })();
        return () => { cancelled = true; };
    }, []);

    if (loading) return <div className="loading-bar" />;
    if (error) return <div className="error-banner">{error}</div>;

    return (
        <>
            <PageHeader title="Hyper-V Health" subtitle="Host cluster health status" />
            {health.length === 0 ? (
                <p className="settings-hint">No host data available.</p>
            ) : (
                <div className="hyperv-network-grid">
                    {health.map((host) => (
                        <div key={host.name} className="hyperv-network-card">
                            <div className="hyperv-network-header">
                                <h3>{host.name}</h3>
                                <StatusBadge
                                    status={host.status === "healthy" ? "healthy" : "warning"}
                                    label={host.status}
                                />
                            </div>
                            <div className="hyperv-network-meta">
                                <span>CPU: {host.cpu_percent}%</span>
                                <span>Memory: {host.memory_used_gb} / {host.memory_total_gb} GB</span>
                                <span>VMs: {host.vm_count}</span>
                                <span>Uptime: {formatUptime(host.uptime_seconds)}</span>
                                {host.version && <span>Version: {host.version}</span>}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </>
    );
}
