import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import LoadingButton from "../../components/common/LoadingButton";
import StatusBadge from "../../components/common/StatusBadge";
import EmptyState from "../../components/common/EmptyState";
import HyperVHostSelector, { useSelectedHost } from "../../components/hyperv/HyperVHostSelector";
import { hypervApi, HyperVVm } from "../../services/hyperv";
import { formatDateTime } from "../../utils/dateFormat";

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
    const { selectedHostId, hosts, loading: hostsLoading, setSelectedHostId } = useSelectedHost();
    const [vms, setVms] = useState<HyperVVm[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [actionId, setActionId] = useState<string | null>(null);
    const [pendingLabel, setPendingLabel] = useState<string | null>(null);
    const [hostFilter, setHostFilter] = useState<string>("all");

    const load = async () => {
        try { setVms(await hypervApi.listVms(selectedHostId)); }
        catch (e) { setError(e instanceof Error ? e.message : "Failed to load"); }
        finally { setLoading(false); }
    };

    useEffect(() => {
        if (hostsLoading) return;
        setLoading(true);
        setHostFilter("all");
        load();
        const id = setInterval(load, 20000);
        return () => clearInterval(id);
    }, [selectedHostId, hostsLoading]);

    const hostServers = Array.from(new Set(vms.map((vm) => vm.host_server).filter(Boolean)));

    const visibleVms = hostFilter === "all" ? vms : vms.filter((vm) => vm.host_server === hostFilter);

    const doAction = async (vmId: string, action: () => Promise<unknown>, label: string) => {
        setActionId(vmId);
        setPendingLabel(label);
        try { await action(); await load(); }
        catch (e) { setError(e instanceof Error ? e.message : "Action failed"); }
        finally { setActionId(null); setPendingLabel(null); }
    };

    if (hostsLoading) return <div className="loading-bar" />;

    return (
        <>
            <PageHeader
                title="Virtual Machines"
                subtitle="Manage Hyper-V virtual machines"
                actions={<HyperVHostSelector hosts={hosts} selectedHostId={selectedHostId} onChange={setSelectedHostId} />}
            />
            {hostServers.length > 1 && (
                <div className="hyperv-host-selector" style={{ marginBottom: 16 }}>
                    <label className="hyperv-host-selector-label">Host:</label>
                    <select
                        className="hyperv-host-selector-select"
                        value={hostFilter}
                        onChange={(e) => setHostFilter(e.target.value)}
                    >
                        <option value="all">All hosts</option>
                        {hostServers.map((host) => (
                            <option key={host} value={host}>{host}</option>
                        ))}
                    </select>
                </div>
            )}
            {error && (
                <div className="error-banner">
                    {error}
                    <button className="btn btn-link" onClick={() => setError(null)}>Dismiss</button>
                </div>
            )}
            {loading ? (
                <div className="loading-bar" />
            ) : visibleVms.length === 0 ? (
                <EmptyState icon="🖥️" title="No virtual machines" description="No VMs found on the connected Hyper-V host." />
            ) : (
                <div className="hyperv-vm-grid">
                    {visibleVms.map((vm) => (
                        <div key={vm.id} className={`hyperv-vm-card state-${vm.state}`}>
                            <div className="hyperv-vm-header">
                                <h3>{vm.name}</h3>
                                <StatusBadge status={stateColors[vm.state] ?? "neutral"} label={vm.state} />
                            </div>
                            <div className="hyperv-vm-meta">
                                <span>Host: {vm.host_server}</span>
                                {vm.guest_os && <span>OS: {vm.guest_os}</span>}
                                <span>CPU: {vm.cpu_count ? `${vm.cpu_count} cores` : `—`}</span>
                                {vm.cpu_usage_percent ? <span>CPU usage: {vm.cpu_usage_percent}%</span> : null}
                                <span>RAM: {formatBytes(vm.memory_assigned_mb)} / {formatBytes(vm.memory_startup_mb)}</span>
                                <span>Uptime: {formatUptime(vm.uptime_seconds)}</span>
                                {vm.last_checkpoint && (
                                    <span>Last checkpoint: {formatDateTime(vm.last_checkpoint)}</span>
                                )}
                            </div>
                            <div className="hyperv-vm-actions">
                                {vm.state !== "running" && (
                                    <LoadingButton
                                        loading={actionId === vm.id}
                                        className="btn btn-primary btn-sm"
                                        onClick={() => doAction(vm.id, () => hypervApi.startVm(vm.id, selectedHostId), "Starting…")}
                                    >
                                        {actionId === vm.id && pendingLabel ? pendingLabel : "Start"}
                                    </LoadingButton>
                                )}
                                {vm.state === "running" && (
                                    <>
                                        <LoadingButton
                                            loading={actionId === vm.id}
                                            className="btn btn-danger btn-sm"
                                            onClick={() => doAction(vm.id, () => hypervApi.stopVm(vm.id, false, selectedHostId), "Stopping…")}
                                        >
                                            {actionId === vm.id && pendingLabel ? pendingLabel : "Stop"}
                                        </LoadingButton>
                                        <LoadingButton
                                            loading={actionId === vm.id}
                                            className="btn btn-secondary btn-sm"
                                            onClick={() => doAction(vm.id, () => hypervApi.restartVm(vm.id, selectedHostId), "Restarting…")}
                                        >
                                            {actionId === vm.id && pendingLabel ? pendingLabel : "Restart"}
                                        </LoadingButton>
                                        <LoadingButton
                                            loading={actionId === vm.id}
                                            className="btn btn-secondary btn-sm"
                                            onClick={() => doAction(vm.id, () => hypervApi.pauseVm(vm.id, selectedHostId), "Pausing…")}
                                        >
                                            {actionId === vm.id && pendingLabel ? pendingLabel : "Pause"}
                                        </LoadingButton>
                                    </>
                                )}
                                {vm.state === "paused" && (
                                    <LoadingButton
                                        loading={actionId === vm.id}
                                        className="btn btn-primary btn-sm"
                                        onClick={() => doAction(vm.id, () => hypervApi.resumeVm(vm.id, selectedHostId), "Resuming…")}
                                    >
                                        {actionId === vm.id && pendingLabel ? pendingLabel : "Resume"}
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
