import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import LoadingButton from "../../components/common/LoadingButton";
import EmptyState from "../../components/common/EmptyState";
import { proxmoxApi, ProxmoxSnapshot } from "../../services/proxmox";

function formatBytes(bytes: number): string {
    if (bytes >= 1073741824) return `${(bytes / 1073741824).toFixed(1)} GB`;
    if (bytes >= 1048576) return `${(bytes / 1048576).toFixed(0)} MB`;
    return `${bytes} B`;
}

function formatDate(iso: string | null): string {
    if (!iso) return "—";
    return new Date(iso).toLocaleString();
}

export default function SnapshotsPage() {
    const [snapshots, setSnapshots] = useState<ProxmoxSnapshot[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [creating, setCreating] = useState(false);
    const [deleteId, setDeleteId] = useState<string | null>(null);

    const load = async () => {
        try { setSnapshots(await proxmoxApi.listSnapshots()); }
        catch (e) { setError(e instanceof Error ? e.message : "Failed to load"); }
        finally { setLoading(false); }
    };

    useEffect(() => { load(); }, []);

    const handleCreate = async (vmId: string) => {
        setCreating(true);
        try {
            const result = await proxmoxApi.createSnapshot(vmId);
            if (!result.success) setError(result.error ?? "Create failed");
            await load();
        } catch (e) { setError(e instanceof Error ? e.message : "Create failed"); }
        finally { setCreating(false); }
    };

    const handleDelete = async (vmId: string, snapshotId: string) => {
        setDeleteId(snapshotId);
        try {
            const result = await proxmoxApi.deleteSnapshot(vmId, snapshotId);
            if (!result.success) setError(result.error ?? "Delete failed");
            await load();
        } catch (e) { setError(e instanceof Error ? e.message : "Delete failed"); }
        finally { setDeleteId(null); }
    };

    if (loading) return <div className="loading-bar" />;

    return (
        <>
            <PageHeader
                title="Snapshots"
                subtitle="Manage Proxmox VM snapshots"
            />
            {error && (
                <div className="error-banner">
                    {error}
                    <button
                        className="btn btn-link"
                        onClick={() => setError(null)}
                    >
                        Dismiss
                    </button>
                </div>
            )}
            {snapshots.length === 0 ? (
                <EmptyState
                    icon="📸"
                    title="No snapshots"
                    description="No snapshots found in the cluster."
                />
            ) : (
                <div className="proxmox-snapshots-table">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>VM</th>
                                <th>Type</th>
                                <th>Size</th>
                                <th>Parent</th>
                                <th>Created</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {snapshots.map((snap) => (
                                <tr key={`${snap.vm_id}-${snap.id}`}>
                                    <td>{snap.name}</td>
                                    <td>{snap.vm_name}</td>
                                    <td>{snap.checkpoint_type}</td>
                                    <td>{formatBytes(snap.size_bytes)}</td>
                                    <td>{snap.parent_checkpoint_id ?? "—"}</td>
                                    <td>{formatDate(snap.creation_time)}</td>
                                    <td>
                                        <LoadingButton
                                            loading={deleteId === snap.id}
                                            className="btn btn-danger btn-sm"
                                            onClick={() =>
                                                snap.vm_id &&
                                                handleDelete(
                                                    snap.vm_id,
                                                    snap.id
                                                )
                                            }
                                        >
                                            Delete
                                        </LoadingButton>
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
