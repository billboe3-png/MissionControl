import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { hypervApi, HyperVHealthHost } from "../../services/hyperv";
import StatusBadge from "../common/StatusBadge";

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

function formatUptime(seconds: number): string {
    if (seconds === 0) return "\u2014";
    const d = Math.floor(seconds / 86400);
    const h = Math.floor((seconds % 86400) / 3600);
    if (d > 0) return `${d}d ${h}h`;
    return `${h}h`;
}

export default function HyperVCard() {
    const navigate = useNavigate();
    const [hosts, setHosts] = useState<{ id: number; name: string }[]>([]);
    const [hostsHealth, setHostsHealth] = useState<HyperVHealthHost[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let cancelled = false;
        const load = async () => {
            try {
                const allHosts = await hypervApi.listHosts();
                if (cancelled) return;
                setHosts(allHosts);

                const healthResults: HyperVHealthHost[] = [];
                for (const h of allHosts) {
                    try {
                        const health = await hypervApi.getHealth(h.id);
                        if (health.hosts?.length) healthResults.push(...health.hosts);
                    } catch { /* skip failed host */ }
                }
                if (cancelled) return;
                setHostsHealth(healthResults);
            } catch (e) {
                if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load");
            } finally {
                if (!cancelled) setLoading(false);
            }
        };
        load();
        return () => { cancelled = true; };
    }, []);

    const handleHostClick = (hostId: number) => {
        localStorage.setItem("hyperv_selected_host_id", String(hostId));
        navigate("/hyperv/vms");
    };

    return (
        <div className="dashboard-section hyperv-card">
            <div className="hyperv-card-header">
                <h3>Hyper-V</h3>
                <button
                    className="btn btn-link btn-sm"
                    onClick={() => navigate("/hyperv")}
                >
                    Manage
                </button>
            </div>
            {loading ? (
                <div className="loading-bar" />
            ) : error ? (
                <p className="settings-hint">{error}</p>
            ) : hosts.length === 0 ? (
                <p className="settings-hint">No Hyper-V hosts configured.</p>
            ) : (
                <div className="hyperv-host-cards">
                    {hostsHealth.map((host) => (
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
                            </div>
                            <div className="hyperv-host-card-body">
                                <UsageBar percent={host.cpu_percent} label="CPU" />
                                <UsageBar percent={host.memory_percent} label={`Memory: ${host.memory_used_gb}/${host.memory_total_gb} GB`} />
                            </div>
                            <div className="hyperv-host-card-footer">
                                <span>VMs: {host.vm_count}</span>
                                <span>Uptime: {formatUptime(host.uptime_seconds)}</span>
                                <span className="hyperv-host-card-action">View →</span>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
