import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import PageHeader from "../../components/common/PageHeader";
import { useToast } from "../../contexts/ToastContext";
import { projectsApi, Project } from "../../services/projects";
import { formatDateTime } from "../../utils/dateFormat";

type Status = "all" | "active" | "inactive";

export default function ProjectsPage() {
    const [projects, setProjects] = useState<Project[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showModal, setShowModal] = useState(false);
    const [editingProject, setEditingProject] = useState<Project | undefined>(undefined);
    const [statusFilter, setStatusFilter] = useState<Status>("all");
    const { showToast } = useToast();
    const navigate = useNavigate();

    const loadData = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await projectsApi.list();
            let items = data.items;
            if (statusFilter === "active") {
                items = items.filter((p) => p.active);
            } else if (statusFilter === "inactive") {
                items = items.filter((p) => !p.active);
            }
            setProjects(items);
        } catch (e: any) {
            setError(e.message || "Failed to load projects");
        } finally {
            setLoading(false);
        }
    }, [statusFilter]);

    useEffect(() => {
        loadData();
    }, [loadData]);

    const handleSave = () => {
        setShowModal(false);
        setEditingProject(undefined);
        loadData();
        showToast(editingProject ? "Project updated" : "Project created", "success");
    };

    const handleClose = async (project: Project) => {
        if (!window.confirm(`Close project "${project.name}"? It will be marked inactive.`)) return;
        try {
            await projectsApi.close(project.id);
            showToast("Project closed", "success");
            loadData();
        } catch (e: any) {
            showToast(e.message || "Close failed", "error");
        }
    };

    const handleDelete = async (project: Project) => {
        if (!window.confirm(`Delete project "${project.name}"? This cannot be undone.`)) return;
        try {
            await projectsApi.remove(project.id);
            showToast("Project deleted", "success");
            loadData();
        } catch (e: any) {
            showToast(e.message || "Delete failed", "error");
        }
    };

    const goToProject = (project: Project) => {
        navigate(`/companies?project=${project.id}`);
    };

    return (
        <>
            <PageHeader
                title="Projects"
                subtitle="Manage projects and track progress"
                actions={
                    <button
                        className="btn btn-primary"
                        onClick={() => {
                            setEditingProject(undefined);
                            setShowModal(true);
                        }}
                    >
                        + New Project
                    </button>
                }
            />

            {error && <div className="error-banner">{error}</div>}

            <div className="toolbar">
                <div className="filters">
                    <label>Status:</label>
                    <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value as Status)}>
                        <option value="all">All</option>
                        <option value="active">Active</option>
                        <option value="inactive">Inactive</option>
                    </select>
                </div>
            </div>

            {loading ? (
                <div className="loading-bar" />
            ) : projects.length === 0 ? (
                <div className="empty-state">
                    <h3>No Projects</h3>
                    <p>Create your first project to start organizing work.</p>
                    <button className="btn btn-primary" onClick={() => { setEditingProject(undefined); setShowModal(true); }}>
                        + New Project
                    </button>
                </div>
            ) : (
                <div className="table-container">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Status</th>
                                <th>Updated</th>
                                <th style={{ textAlign: "right" }}>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {projects.map((p) => (
                                <tr key={p.id} style={{ cursor: "pointer" }} onClick={() => goToProject(p)}>
                                    <td>
                                        <strong>{p.name}</strong>
                                        {p.description && (
                                            <div style={{ fontSize: "0.85em", opacity: 0.6 }}>{p.description}</div>
                                        )}
                                    </td>
                                    <td>
                                        <span className={`status-badge ${p.active ? "status-ok" : "status-disabled"}`}>
                                            {p.active ? "Active" : "Inactive"}
                                        </span>
                                    </td>
                                    <td>{formatDateTime(p.updated_at)}</td>
                                    <td onClick={(e) => e.stopPropagation()}>
                                        <button
                                            className="btn btn-sm"
                                            onClick={() => {
                                                setEditingProject(p);
                                                setShowModal(true);
                                            }}
                                        >
                                            Edit
                                        </button>
                                        {p.active && (
                                            <button
                                                className="btn btn-sm"
                                                onClick={() => handleClose(p)}
                                            >
                                                Close
                                            </button>
                                        )}
                                        <button
                                            className="btn btn-sm btn-danger"
                                            onClick={() => handleDelete(p)}
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

            {showModal && (
                <ProjectModal
                    project={editingProject}
                    onSave={handleSave}
                    onCancel={() => {
                        setShowModal(false);
                        setEditingProject(undefined);
                    }}
                />
            )}
        </>
    );
}

function ProjectModal({ project, onSave, onCancel }: { project?: Project; onSave: () => void; onCancel: () => void }) {
    const [name, setName] = useState(project?.name ?? "");
    const [description, setDescription] = useState(project?.description ?? "");
    const [active, setActive] = useState(project?.active ?? true);
    const [error, setError] = useState<string | null>(null);
    const [saving, setSaving] = useState(false);

    const handleSubmit = async () => {
        if (!name.trim()) {
            setError("Name is required");
            return;
        }

        setSaving(true);
        setError(null);
        try {
            if (project) {
                await projectsApi.update(project.id, {
                    name: name.trim(),
                    description: description || undefined,
                    active,
                });
            } else {
                await projectsApi.create({
                    name: name.trim(),
                    description: description || undefined,
                    active,
                });
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
                    <h2>{project ? "Edit Project" : "New Project"}</h2>
                    <button className="modal-close" onClick={onCancel}>&times;</button>
                </div>
                <div className="modal-body">
                    {error && <div className="alert alert-error">{error}</div>}

                    <div className="form-group">
                        <label>Name *</label>
                        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Mission Control" />
                    </div>

                    <div className="form-group">
                        <label>Description</label>
                        <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} />
                    </div>

                    <div className="form-group">
                        <label>Active</label>
                        <select value={active ? "true" : "false"} onChange={(e) => setActive(e.target.value === "true")}>
                            <option value="true">Active</option>
                            <option value="false">Inactive</option>
                        </select>
                    </div>
                </div>
                <div className="modal-footer">
                    <button className="btn" onClick={onCancel} disabled={saving}>Cancel</button>
                    <button className="btn btn-primary" onClick={handleSubmit} disabled={saving}>
                        {saving ? "Saving..." : project ? "Update" : "Create"}
                    </button>
                </div>
            </div>
        </div>
    );
}
