import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import PageHeader from "../../components/common/PageHeader";
import SearchInput from "../../components/common/SearchInput";
import DataTable, { Column } from "../../components/common/DataTable";
import EmptyState from "../../components/common/EmptyState";
import StatusBadge from "../../components/common/StatusBadge";
import { useToast } from "../../contexts/ToastContext";
import {
    automationApi,
    PlaybookData,
} from "../../services/automation";

export default function PlaybooksPage() {
    const [items, setItems] = useState<PlaybookData[]>([]);
    const [search, setSearch] = useState("");
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const { showToast } = useToast();
    const navigate = useNavigate();

    const loadData = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await automationApi.listPlaybooks(search || undefined);
            setItems(data.items);
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : "Failed to load playbooks");
        } finally {
            setLoading(false);
        }
    }, [search]);

    useEffect(() => {
        loadData();
    }, [loadData]);

    const handleDelete = async (id: number) => {
        if (!window.confirm("Delete this playbook?")) return;
        try {
            await automationApi.deletePlaybook(id);
            showToast("Playbook deleted", "success");
            loadData();
        } catch (e: unknown) {
            showToast(e instanceof Error ? e.message : "Delete failed", "error");
        }
    };

    const columns: Column<PlaybookData>[] = [
        { key: "name", header: "Name" },
        { key: "version", header: "Version", render: (r) => `v${r.version}` },
        { key: "category", header: "Category", render: (r) => r.category ?? "—" },
        {
            key: "enabled",
            header: "Status",
            render: (r) => (
                <StatusBadge
                    status={r.enabled ? "healthy" : "neutral"}
                    label={r.enabled ? "Active" : "Disabled"}
                />
            ),
        },
        {
            key: "requires_approval",
            header: "Approval",
            render: (r) => (
                <StatusBadge
                    status={r.requires_approval ? "warning" : "neutral"}
                    label={r.requires_approval ? "Required" : "None"}
                />
            ),
        },
        {
            key: "updated_at",
            header: "Updated",
            render: (r) => new Date(r.updated_at).toLocaleString(),
        },
    ];

    return (
        <>
            <PageHeader
                title="Playbooks"
                subtitle="Define and manage automation playbooks"
                actions={
                    <button
                        className="btn btn-primary"
                        onClick={() => navigate("/automation/playbooks/new")}
                    >
                        + New Playbook
                    </button>
                }
            />
            <SearchInput
                value={search}
                onChange={setSearch}
                placeholder="Search playbooks…"
            />
            {error && <div className="error-banner">{error}</div>}
            {loading ? (
                <div className="loading-bar" />
            ) : items.length === 0 ? (
                <EmptyState
                    icon="📋"
                    title="No playbooks"
                    description="Create your first playbook to automate operations."
                />
            ) : (
                <DataTable
                    columns={columns}
                    data={items}
                    onRowClick={(r) => navigate(`/automation/playbooks/${r.id}`)}
                    emptyMessage="No playbooks found"
                />
            )}
        </>
    );
}
