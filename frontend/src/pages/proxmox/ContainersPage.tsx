import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import LoadingButton from "../../components/common/LoadingButton";
import StatusBadge from "../../components/common/StatusBadge";
import EmptyState from "../../components/common/EmptyState";
import { proxmoxApi, ProxmoxLxc } from "../../services/proxmox";

function formatUptime(seconds: number): string {
    if (seconds === 0) return "—";
    const d = Math.floor(seconds / 86400);
    const h = Math.floor((seconds % 86400) / 3600);
    if (d > 0) return `${d}d ${h}h`;
    return `${h}h`;
}

function formatBytes(mb: number): string {
    if (mb >= 1024) return `${(mb / 1024).toFixed(1)} GB`;
    return `${mb} MB`;
}

const stateColors: Record<string, "healthy" | "warning" | "error" | "neutral"> = {
    running: "healthy",
    stopped: "error",
    paused: "warning",
};

export default function ContainersPage() {
    const [containers, setContainers] = useState<ProxmoxLxc[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [actionId, setActionId] = useState<string | null>(null);

    const load = async () => {
        try { setContainers(await proxmoxApi.listLxc()); }
        catch (e) { setError(e instanceof Error ? e.message : "Failed to load"); }
        finally { setLoading(false); }
    };

    useEffect(() => { load(); }, []);

    const doAction = async (vmId: string, action: () => Promise<unknown>) => {
        setActionId(vmId);
        try { await action(); await load(); }
        catch (e) { setError(e instanceof Error ? e.message : "Action failed"); }
        finally { setActionId(null); }
    };

    if (loading) return <div className="loading">Loading…</div>;

    return (
        <>
            <PageHeader title="LXC Containers" subtitle="Manage Proxmox LXC containers" />
            {error && (
                <div className="error-banner">
                    {error}
                    <button className="btn btn-link" onClick={() => setError(null)}>Dismiss</button>
                </div>
            )}
            {containers.length === 0 ? (
                <EmptyState icon="📦" title="No containers" description="No LXC containers found in the cluster." />
            ) : (
                <div className="proxmox-lxc-grid">
                    {containers.map((lxc) => (
                        <div key={lxc.id} className={`proxmox-lxc-card state-${lxc.state}`}>
                            <div className="proxmox-lxc-header">
                                <h3>{lxc.name}</h3>
                                <StatusBadge status={stateColors[lxc.state] ?? "neutral"} label={lxc.state} />
                            </div>
                            <div className="proxmox-lxc-meta">
                                <span>Node: {lxc.host_server}</span>
                                {lxc.guest_os && <span>OS: {lxc.guest_os}</span>}
                                <span>CPU: {lxc.cpu_count} cores ({lxc.cpu_usage_percent}%)</span>
                                <span>RAM: {formatBytes(lxc.memory_assigned_mb)}</span>
                                <span>Uptime: {formatUptime(lxc.uptime_seconds)}</span>
                            </div>
                            <div className="proxmox-lxc-actions">
                                {lxc.state !== "running" && (
                                    <LoadingButton
                                        loading={actionId === lxc.id}
                                        className="btn btn-primary btn-sm"
                                        onClick={() => doAction(lxc.id, () => proxmoxApi.startLxc(lxc.id))}
                                    >
                                        Start
                                    </LoadingButton>
                                )}
                                {lxc.state === "running" && (
                                    <LoadingButton
                                        loading={actionId === lxc.id}
                                        className="btn btn-danger btn-sm"
                                        onClick={() => doAction(lxc.id, () => proxmoxApi.stopLxc(lxc.id))}
                                    >
                                        Stop
                                    </LoadingButton>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </>
    );
}
