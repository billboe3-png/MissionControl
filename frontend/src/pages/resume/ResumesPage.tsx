import { useCallback, useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import { useToast } from "../../contexts/ToastContext";
import { resumesApi, Resume } from "../../services/resumes";

export default function ResumesPage() {
    const [items, setItems] = useState<Resume[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showModal, setShowModal] = useState(false);
    const [editing, setEditing] = useState<Resume | undefined>(undefined);
    const { showToast } = useToast();

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await resumesApi.list();
            setItems(data.items);
        } catch (e: any) {
            setError(e.message || "Failed to load resumes");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        load();
    }, [load]);

    const handleSave = () => {
        setShowModal(false);
        setEditing(undefined);
        load();
        showToast(editing ? "Resume updated" : "Resume created", "success");
    };

    const handleDelete = async (item: Resume) => {
        if (!window.confirm(`Delete resume "${item.title}"?`)) return;
        try {
            await resumesApi.remove(item.id);
            showToast("Resume deleted", "success");
            load();
        } catch (e: any) {
            showToast(e.message || "Delete failed", "error");
        }
    };

    const handleSetActive = async (item: Resume) => {
        try {
            await resumesApi.update(item.id, { available: true });
            showToast("Active resume updated", "success");
            load();
        } catch (e: any) {
            showToast(e.message || "Update failed", "error");
        }
    };

    return (
        <>
            <PageHeader
                title="Resume"
                subtitle="Saved work context to resume later"
                actions={
                    <button className="btn btn-primary" onClick={() => { setEditing(undefined); setShowModal(true); }}>
                        + New Resume
                    </button>
                }
            />

            {error && <div className="error-banner">{error}</div>}

            {loading ? (
                <div className="loading-bar" />
            ) : items.length === 0 ? (
                <div className="empty-state">
                    <h3>No Resumes</h3>
                    <p>Create a resume entry to save your current work context.</p>
                    <button className="btn btn-primary" onClick={() => { setEditing(undefined); setShowModal(true); }}>
                        + New Resume
                    </button>
                </div>
            ) : (
                <div className="table-container">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Title</th>
                                <th>Status</th>
                                <th>Updated</th>
                                <th style={{ textAlign: "right" }}>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {items.map((item) => (
                                <tr key={item.id}>
                                    <td>
                                        <strong>{item.title}</strong>
                                        {item.description && (
                                            <div style={{ fontSize: "0.85em", opacity: 0.6 }}>{item.description}</div>
                                        )}
                                    </td>
                                    <td>
                                        <span className={`status-badge ${item.available ? "status-ok" : "status-disabled"}`}>
                                            {item.available ? "Active" : "Inactive"}
                                        </span>
                                    </td>
                                    <td>{new Date(item.updated_at).toLocaleString()}</td>
                                    <td style={{ textAlign: "right" }}>
                                        {!item.available && (
                                            <button className="btn btn-sm" onClick={() => handleSetActive(item)}>
                                                Set Active
                                            </button>
                                        )}
                                        <button className="btn btn-sm" onClick={() => { setEditing(item); setShowModal(true); }}>
                                            Edit
                                        </button>
                                        <button className="btn btn-sm btn-danger" onClick={() => handleDelete(item)}>
                                            Delete
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {showModal && (
                <ResumeModal
                    resume={editing}
                    onSave={handleSave}
                    onCancel={() => { setShowModal(false); setEditing(undefined); }}
                />
            )}
        </>
    );
}

function ResumeModal({ resume, onSave, onCancel }: { resume?: Resume; onSave: () => void; onCancel: () => void }) {
    const [title, setTitle] = useState(resume?.title ?? "");
    const [description, setDescription] = useState(resume?.description ?? "");
    const [available, setAvailable] = useState(resume?.available ?? true);
    const [error, setError] = useState<string | null>(null);
    const [saving, setSaving] = useState(false);

    const handleSubmit = async () => {
        if (!title.trim()) {
            setError("Title is required");
            return;
        }
        setSaving(true);
        setError(null);
        try {
            if (resume) {
                await resumesApi.update(resume.id, { title: title.trim(), description: description || undefined, available });
            } else {
                await resumesApi.create({ title: title.trim(), description: description || undefined, available });
            }
            onSave();
        } catch (e: any) {
            setError(e.message || "Save failed");
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="modal-overlay" onClick={onCancel}>
            <div className="modal" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>{resume ? "Edit Resume" : "New Resume"}</h2>
                    <button className="modal-close" onClick={onCancel}>&times;</button>
                </div>
                <div className="modal-body">
                    {error && <div className="alert alert-error">{error}</div>}

                    <div className="form-group">
                        <label>Title *</label>
                        <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Current sprint context" />
                    </div>

                    <div className="form-group">
                        <label>Description</label>
                        <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={4} />
                    </div>

                    <div className="form-group">
                        <label>Active</label>
                        <select value={available ? "true" : "false"} onChange={(e) => setAvailable(e.target.value === "true")}>
                            <option value="true">Active</option>
                            <option value="false">Inactive</option>
                        </select>
                    </div>
                </div>
                <div className="modal-footer">
                    <button className="btn" onClick={onCancel} disabled={saving}>Cancel</button>
                    <button className="btn btn-primary" onClick={handleSubmit} disabled={saving}>
                        {saving ? "Saving..." : resume ? "Update" : "Create"}
                    </button>
                </div>
            </div>
        </div>
    );
}
