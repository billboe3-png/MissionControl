import { useState } from "react";
import { Project } from "../types/dashboard";
import { projectsApi } from "../services/projects";
import Toolbar from "./common/Toolbar";
import ConfirmDialog from "./common/ConfirmDialog";
import ProjectModal from "./modals/ProjectModal";

function statusBadgeClass(active: boolean): string {
    return active ? "badge badge-success" : "badge badge-muted";
}

function formatDate(iso: string): string {
    const date = new Date(iso);
    return date.toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
    });
}

interface ProjectsCardProps {
    count: number;
    items: Project[];
    onRefresh: () => void;
    showToast: (message: string, type?: "success" | "error") => void;
}

export default function ProjectsCard({
    count,
    items,
    onRefresh,
    showToast,
}: ProjectsCardProps) {
    const [modalOpen, setModalOpen] = useState(false);
    const [editing, setEditing] = useState<Project | undefined>(undefined);
    const [confirmDelete, setConfirmDelete] = useState<Project | undefined>(
        undefined,
    );
    const [deleting, setDeleting] = useState(false);

    const handleNew = () => {
        setEditing(undefined);
        setModalOpen(true);
    };

    const handleEdit = (project: Project) => {
        setEditing(project);
        setModalOpen(true);
    };

    const handleSave = () => {
        setModalOpen(false);
        setEditing(undefined);
        showToast("Project saved");
        onRefresh();
    };

    const handleDelete = async () => {
        if (!confirmDelete) return;
        setDeleting(true);
        try {
            await projectsApi.remove(confirmDelete.id);
            setConfirmDelete(undefined);
            showToast("Project deleted");
            onRefresh();
        } catch (err) {
            showToast(
                err instanceof Error ? err.message : "Delete failed",
                "error",
            );
        } finally {
            setDeleting(false);
        }
    };

    const handleToggleActive = async (project: Project) => {
        try {
            await projectsApi.update(project.id, { active: !project.active });
            showToast(
                project.active ? "Project deactivated" : "Project activated",
            );
            onRefresh();
        } catch (err) {
            showToast(
                err instanceof Error ? err.message : "Update failed",
                "error",
            );
        }
    };

    return (
        <div className="card">
            <div className="card-header">
                <h2>Projects</h2>
                <Toolbar onAdd={handleNew} addLabel="New Project" />
            </div>

            {count === 0 ? (
                <p className="muted-text">No projects yet.</p>
            ) : (
                <ul className="status-list">
                    {items.map((project) => (
                        <li key={project.id}>
                            <span className="item-content">
                                <strong>{project.name}</strong>
                                {project.description && (
                                    <span className="item-description">
                                        {project.description}
                                    </span>
                                )}
                                <span className="item-meta">
                                    Created {formatDate(project.created_at)}
                                </span>
                            </span>
                            <div className="item-actions-row">
                                <span
                                    className={statusBadgeClass(project.active)}
                                >
                                    {project.active ? "Active" : "Inactive"}
                                </span>
                                <div className="item-actions">
                                    <button
                                        className="btn-icon"
                                        title="Toggle active"
                                        onClick={() =>
                                            handleToggleActive(project)
                                        }
                                    >
                                        {project.active ? "⏸" : "▶"}
                                    </button>
                                    <button
                                        className="btn-icon"
                                        title="Edit"
                                        onClick={() => handleEdit(project)}
                                    >
                                        ✎
                                    </button>
                                    <button
                                        className="btn-icon btn-icon-danger"
                                        title="Delete"
                                        onClick={() =>
                                            setConfirmDelete(project)
                                        }
                                    >
                                        ✕
                                    </button>
                                </div>
                            </div>
                        </li>
                    ))}
                </ul>
            )}

            {modalOpen && (
                <ProjectModal
                    project={editing}
                    onSave={handleSave}
                    onCancel={() => {
                        setModalOpen(false);
                        setEditing(undefined);
                    }}
                    onError={(msg) => showToast(msg, "error")}
                />
            )}

            {confirmDelete && (
                <ConfirmDialog
                    title="Delete Project"
                    message={`Are you sure you want to delete "${confirmDelete.name}"? This action cannot be undone.`}
                    confirmLabel="Delete"
                    danger
                    loading={deleting}
                    onConfirm={handleDelete}
                    onCancel={() => setConfirmDelete(undefined)}
                />
            )}
        </div>
    );
}
