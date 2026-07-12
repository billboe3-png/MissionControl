import { useState } from "react";
import { Task, Project } from "../types/dashboard";
import { tasksApi } from "../services/tasks";
import Toolbar from "./common/Toolbar";
import ConfirmDialog from "./common/ConfirmDialog";
import TaskModal from "./modals/TaskModal";

function priorityBadgeClass(priority: string): string {
    switch (priority) {
        case "high":
            return "badge badge-danger";
        case "medium":
            return "badge badge-warning";
        case "low":
            return "badge badge-success";
        default:
            return "badge badge-muted";
    }
}

function statusBadgeClass(status: string): string {
    switch (status) {
        case "completed":
            return "badge badge-success";
        case "in_progress":
            return "badge badge-warning";
        case "pending":
            return "badge badge-muted";
        case "blocked":
            return "badge badge-danger";
        default:
            return "badge badge-muted";
    }
}

function formatDate(iso: string): string {
    const date = new Date(iso);
    return date.toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
    });
}

interface TasksCardProps {
    count: number;
    items: Task[];
    projects: Project[];
    onRefresh: () => void;
    showToast: (message: string, type?: "success" | "error") => void;
}

export default function TasksCard({
    count,
    items,
    projects,
    onRefresh,
    showToast,
}: TasksCardProps) {
    const [modalOpen, setModalOpen] = useState(false);
    const [editing, setEditing] = useState<Task | undefined>(undefined);
    const [confirmDelete, setConfirmDelete] = useState<Task | undefined>(
        undefined,
    );
    const [deleting, setDeleting] = useState(false);

    const handleNew = () => {
        setEditing(undefined);
        setModalOpen(true);
    };

    const handleEdit = (task: Task) => {
        setEditing(task);
        setModalOpen(true);
    };

    const handleSave = () => {
        setModalOpen(false);
        setEditing(undefined);
        showToast("Task saved");
        onRefresh();
    };

    const handleDelete = async () => {
        if (!confirmDelete) return;
        setDeleting(true);
        try {
            await tasksApi.remove(confirmDelete.id);
            setConfirmDelete(undefined);
            showToast("Task deleted");
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

    const handleComplete = async (task: Task) => {
        const newStatus =
            task.status === "completed" ? "pending" : "completed";
        try {
            await tasksApi.update(task.id, { status: newStatus });
            showToast(
                newStatus === "completed"
                    ? "Task completed"
                    : "Task reopened",
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
                <h2>Tasks</h2>
                <Toolbar onAdd={handleNew} addLabel="New Task" />
            </div>

            {count === 0 ? (
                <p className="muted-text">No tasks yet.</p>
            ) : (
                <ul className="status-list">
                    {items.map((task) => (
                        <li key={task.id}>
                            <span className="item-content">
                                <strong>{task.title}</strong>
                                <span className="item-meta">
                                    {task.project_name} &middot; Created{" "}
                                    {formatDate(task.created_at)}
                                </span>
                            </span>
                            <div className="item-actions-row">
                                <span className="badge-group">
                                    <span
                                        className={priorityBadgeClass(
                                            task.priority,
                                        )}
                                    >
                                        {task.priority}
                                    </span>
                                    <span
                                        className={statusBadgeClass(
                                            task.status,
                                        )}
                                    >
                                        {task.status}
                                    </span>
                                </span>
                                <div className="item-actions">
                                    <button
                                        className="btn-icon"
                                        title={
                                            task.status === "completed"
                                                ? "Reopen"
                                                : "Complete"
                                        }
                                        onClick={() => handleComplete(task)}
                                    >
                                        {task.status === "completed"
                                            ? "↺"
                                            : "✓"}
                                    </button>
                                    <button
                                        className="btn-icon"
                                        title="Edit"
                                        onClick={() => handleEdit(task)}
                                    >
                                        ✎
                                    </button>
                                    <button
                                        className="btn-icon btn-icon-danger"
                                        title="Delete"
                                        onClick={() =>
                                            setConfirmDelete(task)
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
                <TaskModal
                    task={editing}
                    projects={projects}
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
                    title="Delete Task"
                    message={`Are you sure you want to delete "${confirmDelete.title}"? This action cannot be undone.`}
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
