import { useCallback, useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import DataTable, { Column } from "../../components/common/DataTable";
import EmptyState from "../../components/common/EmptyState";
import StatusBadge from "../../components/common/StatusBadge";
import CredentialModal from "../../components/modals/CredentialModal";
import { useToast } from "../../contexts/ToastContext";
import { credentialsApi, CredentialData, remoteApi } from "../../services/remote";

export default function CredentialsPage() {
    const { showToast } = useToast();
    const [credentials, setCredentials] = useState<CredentialData[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showModal, setShowModal] = useState(false);
    const [editingCredential, setEditingCredential] = useState<CredentialData | undefined>(undefined);
    const [testingId, setTestingId] = useState<number | null>(null);

    const loadCredentials = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await credentialsApi.list();
            setCredentials(data.items);
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : "Failed to load credentials");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadCredentials();
    }, [loadCredentials]);

    const handleDelete = async (cred: CredentialData) => {
        if (!confirm(`Delete credential "${cred.name}"?`)) return;
        try {
            await credentialsApi.remove(cred.id);
            showToast("Credential deleted");
            loadCredentials();
        } catch {
            showToast("Failed to delete credential", "error");
        }
    };

    const handleEdit = (cred: CredentialData) => {
        setEditingCredential(cred);
        setShowModal(true);
    };

    const handleCreate = () => {
        setEditingCredential(undefined);
        setShowModal(true);
    };

    const handleSave = () => {
        setShowModal(false);
        setEditingCredential(undefined);
        loadCredentials();
        showToast(editingCredential ? "Credential updated" : "Credential created");
    };

    const columns: Column<CredentialData>[] = [
        { key: "name", header: "Name" },
        { key: "username", header: "Username" },
        {
            key: "authentication_type",
            header: "Type",
            render: (row) => (
                <span className="tag">{row.authentication_type}</span>
            ),
        },
        {
            key: "description",
            header: "Description",
            render: (row) => row.description ?? "\u2014",
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
                title="Credentials"
                subtitle="Manage authentication profiles"
                actions={
                    <button className="btn btn-primary" onClick={handleCreate}>
                        + Add Credential
                    </button>
                }
            />
            {error && <div className="error-banner">{error}</div>}
            {loading ? (
                <div className="loading">Loading\u2026</div>
            ) : credentials.length === 0 ? (
                <EmptyState
                    icon="\uD83D\uDD11"
                    title="No credentials"
                    description="Add your first credential profile to get started."
                    action={
                        <button className="btn btn-primary" onClick={handleCreate}>
                            + Add Credential
                        </button>
                    }
                />
            ) : (
                <DataTable
                    columns={columns}
                    data={credentials}
                    onRowClick={(row) => handleEdit(row)}
                    emptyMessage="No credentials found"
                />
            )}
            {showModal && (
                <CredentialModal
                    credential={editingCredential}
                    onSave={handleSave}
                    onCancel={() => {
                        setShowModal(false);
                        setEditingCredential(undefined);
                    }}
                    onError={(msg) => showToast(msg, "error")}
                />
            )}
        </>
    );
}
