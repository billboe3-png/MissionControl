import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import LoadingButton from "../../components/common/LoadingButton";
import StatusBadge from "../../components/common/StatusBadge";
import EmptyState from "../../components/common/EmptyState";
import { hypervApi, HyperVVm } from "../../services/hyperv";

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
    saved: "neutral",
};

export default function VirtualMachinesPage() {
    const [vms, setVms] = useState<HyperVVm[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [actionId, setActionId] = useState<string | null>(null);

    const load = async () => {
        try { setVms(await hypervApi.listVms()); }
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
            <PageHeader title="Virtual Machines" subtitle="Manage Hyper-V virtual machines" />
            {error && (
                <div className="error-banner">
                    {error}
                    <button className="btn btn-link" onClick={() => setError(null)}>Dismiss</button>
                </div>
            )}
            {vms.length === 0 ? (
                <EmptyState icon="🖥️" title="No virtual machines" description="No VMs found on the connected Hyper-V host." />
            ) : (
                <div className="hyperv-vm-grid">
                    {vms.map((vm) => (
                        <div key={vm.id} className={`hyperv-vm-card state-${vm.state}`}>
                            <div className="hyperv-vm-header">
                                <h3>{vm.name}</h3>
                                <StatusBadge status={stateColors[vm.state] ?? "neutral"} label={vm.state} />
                            </div>
                            <div className="hyperv-vm-meta">
                                <span>Host: {vm.host_server}</span>
                                {vm.guest_os && <span>OS: {vm.guest_os}</span>}
                                <span>CPU: {vm.cpu_count} cores</span>
                                <span>RAM: {formatBytes(vm.memory_assigned_mb)} / {formatBytes(vm.memory_startup_mb)}</span>
                                <span>Uptime: {formatUptime(vm.uptime_seconds)}</span>
                                {vm.last_checkpoint && (
                                    <span>Last checkpoint: {new Date(vm.last_checkpoint).toLocaleDateString()}</span>
                                )}
                            </div>
                            <div className="hyperv-vm-actions">
                                {vm.state !== "running" && (
                                    <LoadingButton
                                        loading={actionId === vm.id}
                                        className="btn btn-primary btn-sm"
                                        onClick={() => doAction(vm.id, () => hypervApi.startVm(vm.id))}
                                    >
                                        Start
                                    </LoadingButton>
                                )}
                                {vm.state === "running" && (
                                    <>
                                        <LoadingButton
                                            loading={actionId === vm.id}
                                            className="btn btn-danger btn-sm"
                                            onClick={() => doAction(vm.id, () => hypervApi.stopVm(vm.id))}
                                        >
                                            Stop
                                        </LoadingButton>
                                        <LoadingButton
                                            loading={actionId === vm.id}
                                            className="btn btn-secondary btn-sm"
                                            onClick={() => doAction(vm.id, () => hypervApi.restartVm(vm.id))}
                                        >
                                            Restart
                                        </LoadingButton>
                                        <LoadingButton
                                            loading={actionId === vm.id}
                                            className="btn btn-secondary btn-sm"
                                            onClick={() => doAction(vm.id, () => hypervApi.pauseVm(vm.id))}
                                        >
                                            Pause
                                        </LoadingButton>
                                    </>
                                )}
                                {vm.state === "paused" && (
                                    <LoadingButton
                                        loading={actionId === vm.id}
                                        className="btn btn-primary btn-sm"
                                        onClick={() => doAction(vm.id, () => hypervApi.resumeVm(vm.id))}
                                    >
                                        Resume
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
