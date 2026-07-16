import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import LoadingButton from "../../components/common/LoadingButton";
import EmptyState from "../../components/common/EmptyState";
import HyperVHostSelector, { useSelectedHost } from "../../components/hyperv/HyperVHostSelector";
import { hypervApi, HyperVCheckpoint, HyperVVm } from "../../services/hyperv";

function formatBytes(bytes: number): string {
    if (bytes >= 1073741824) return `${(bytes / 1073741824).toFixed(1)} GB`;
    if (bytes >= 1048576) return `${(bytes / 1048576).toFixed(0)} MB`;
    return `${bytes} B`;
}

export default function CheckpointsPage() {
    const { selectedHostId, hosts, loading: hostsLoading, setSelectedHostId } = useSelectedHost();
    const [checkpoints, setCheckpoints] = useState<HyperVCheckpoint[]>([]);
    const [vms, setVms] = useState<HyperVVm[]>([]);
    const [filterVm, setFilterVm] = useState<string>("");
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [creating, setCreating] = useState(false);

    const load = async () => {
        try {
            const [cps, vmList] = await Promise.all([
                hypervApi.listCheckpoints(filterVm || undefined, selectedHostId),
                hypervApi.listVms(selectedHostId),
            ]);
            setCheckpoints(cps);
            setVms(vmList);
        } catch (e) {
            setError(e instanceof Error ? e.message : "Failed to load");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (hostsLoading) return;
        setLoading(true);
        load();
    }, [filterVm, selectedHostId, hostsLoading]);

    const handleDelete = async (cp: HyperVCheckpoint) => {
        if (!window.confirm(`Delete checkpoint "${cp.name}"?`)) return;
        try {
            await hypervApi.deleteCheckpoint(cp.vm_id ?? "", cp.id, selectedHostId);
            await load();
        } catch (e) {
            setError(e instanceof Error ? e.message : "Delete failed");
        }
    };

    if (hostsLoading) return <div className="loading-bar" />;

    return (
        <>
            <PageHeader
                title="Checkpoints"
                subtitle="Hyper-V VM snapshots"
                actions={
                    <div className="hyperv-checkpoint-actions">
                        <HyperVHostSelector hosts={hosts} selectedHostId={selectedHostId} onChange={setSelectedHostId} />
                        <select
                            className="form-input"
                            value={filterVm}
                            onChange={(e) => { setFilterVm(e.target.value); setLoading(true); }}
                        >
                            <option value="">All VMs</option>
                            {vms.map((vm) => (
                                <option key={vm.id} value={vm.id}>{vm.name}</option>
                            ))}
                        </select>
                    </div>
                }
            />
            {error && <div className="error-banner">{error}</div>}
            {loading ? (
                <div className="loading-bar" />
            ) : checkpoints.length === 0 ? (
                <EmptyState icon="📸" title="No checkpoints" description="No checkpoints found for the selected VM." />
            ) : (
                <div className="hyperv-checkpoint-table">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>VM</th>
                                <th>Type</th>
                                <th>Size</th>
                                <th>Created</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {checkpoints.map((cp) => (
                                <tr key={cp.id}>
                                    <td>{cp.name}</td>
                                    <td>{cp.vm_name}</td>
                                    <td>{cp.checkpoint_type}</td>
                                    <td>{formatBytes(cp.size_bytes)}</td>
                                    <td>{cp.creation_time ? new Date(cp.creation_time).toLocaleString() : "—"}</td>
                                    <td>
                                        <button
                                            className="btn btn-danger btn-sm"
                                            onClick={() => handleDelete(cp)}
                                        >
                                            Delete
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </>
    );
}
