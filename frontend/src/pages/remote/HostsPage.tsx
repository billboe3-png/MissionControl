import { useCallback, useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import SearchInput from "../../components/common/SearchInput";
import DataTable, { Column } from "../../components/common/DataTable";
import EmptyState from "../../components/common/EmptyState";
import StatusBadge from "../../components/common/StatusBadge";
import HostModal from "../../components/modals/HostModal";
import { useToast } from "../../contexts/ToastContext";
import { hostsApi, HostData } from "../../services/remote";

export default function HostsPage() {
    const { showToast } = useToast();
    const [hosts, setHosts] = useState<HostData[]>([]);
    const [search, setSearch] = useState("");
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showHostModal, setShowHostModal] = useState(false);
    const [editingHost, setEditingHost] = useState<HostData | undefined>(undefined);

    const loadHosts = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await hostsApi.list(search || undefined);
            setHosts(data.items);
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : "Failed to load hosts");
        } finally {
            setLoading(false);
        }
    }, [search]);

    useEffect(() => {
        loadHosts();
    }, [loadHosts]);

    const handleDelete = async (host: HostData) => {
        if (!confirm(`Delete host "${host.name}"?`)) return;
        try {
            await hostsApi.remove(host.id);
            showToast("Host deleted");
            loadHosts();
        } catch {
            showToast("Failed to delete host", "error");
        }
    };

    const handleEdit = (host: HostData) => {
        setEditingHost(host);
        setShowHostModal(true);
    };

    const handleCreate = () => {
        setEditingHost(undefined);
        setShowHostModal(true);
    };

    const handleSave = () => {
        setShowHostModal(false);
        setEditingHost(undefined);
        loadHosts();
        showToast(editingHost ? "Host updated" : "Host added");
    };

    const columns: Column<HostData>[] = [
        { key: "name", header: "Name" },
        { key: "hostname", header: "Hostname" },
        {
            key: "connection_type",
            header: "Type",
            render: (row) => (
                <span className="tag">{row.connection_type.toUpperCase()}</span>
            ),
        },
        {
            key: "enabled",
            header: "Status",
            render: (row) => (
                <StatusBadge
                    status={row.enabled ? "healthy" : "error"}
                    label={row.enabled ? "Enabled" : "Disabled"}
                />
            ),
        },
        {
            key: "credential_profile_name",
            header: "Credential",
            render: (row) => row.credential_profile_name ?? "\u2014",
        },
        {
            key: "actions",
            header: "",
            render: (row) => (
                <div className="item-actions-row">
                    <button
                        className="btn btn-sm btn-secondary"
                        onClick={(e) => {
                            e.stopPropagation();
                            handleEdit(row);
                        }}
                    >
                        Edit
                    </button>
                    <button
                        className="btn btn-sm btn-danger"
                        onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(row);
                        }}
                    >
                        Delete
                    </button>
                </div>
            ),
        },
    ];

    return (
        <>
            <PageHeader
                title="Hosts"
                subtitle="Manage remote hosts"
                actions={
                    <button className="btn btn-primary" onClick={handleCreate}>
                        + Add Host
                    </button>
                }
            />
            <SearchInput
                value={search}
                onChange={setSearch}
                placeholder="Search hosts\u2026"
            />
            {error && <div className="error-banner">{error}</div>}
            {loading ? (
                <div className="loading-bar" />
            ) : hosts.length === 0 ? (
                <EmptyState
                    icon="\uD83D\uDDA5\uFE0F"
                    title="No hosts"
                    description="Add your first remote host to get started."
                    action={
                        <button className="btn btn-primary" onClick={handleCreate}>
                            + Add Host
                        </button>
                    }
                />
            ) : (
                <DataTable
                    columns={columns}
                    data={hosts}
                    onRowClick={(row) => handleEdit(row)}
                    emptyMessage="No hosts found"
                />
            )}
            {showHostModal && (
                <HostModal
                    host={editingHost}
                    onSave={handleSave}
                    onCancel={() => {
                        setShowHostModal(false);
                        setEditingHost(undefined);
                    }}
                    onError={(msg) => showToast(msg, "error")}
                />
            )}
        </>
    );
}
