import { useState } from "react";
import LoadingButton from "../common/LoadingButton";
import { tasksApi } from "../../services/tasks";
import { Task, Project } from "../../types/dashboard";

interface TaskModalProps {
    task?: Task;
    projects: Project[];
    onSave: () => void;
    onCancel: () => void;
    onError: (message: string) => void;
}

export default function TaskModal({
    task,
    projects,
    onSave,
    onCancel,
    onError,
}: TaskModalProps) {
    const [title, setTitle] = useState(task?.title ?? "");
    const [description, setDescription] = useState(
        task?.description ?? "",
    );
    const [priority, setPriority] = useState(task?.priority ?? "medium");
    const [status, setStatus] = useState(task?.status ?? "pending");
    const [projectId, setProjectId] = useState<number>(
        task?.project_id ?? (projects.length > 0 ? projects[0].id : 0),
    );
    const [loading, setLoading] = useState(false);

    const isEditing = task !== undefined;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            if (isEditing) {
                await tasksApi.update(task.id, {
                    title,
                    description: description || undefined,
                    priority,
                    status,
                    project_id: projectId,
                });
            } else {
                await tasksApi.create({
                    title,
                    description: description || undefined,
                    priority,
                    status,
                    project_id: projectId,
                });
            }
            onSave();
        } catch (err) {
            onError(
                err instanceof Error ? err.message : "Operation failed",
            );
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="modal-overlay" onClick={onCancel}>
            <div
                className="modal-content"
                onClick={(e) => e.stopPropagation()}
            >
                <h3 className="modal-title">
                    {isEditing ? "Edit Task" : "New Task"}
                </h3>

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label htmlFor="task-title">Title</label>
                        <input
                            id="task-title"
                            type="text"
                            className="form-input"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            required
                            maxLength={200}
                            autoFocus
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="task-description">
                            Description
                        </label>
                        <textarea
                            id="task-description"
                            className="form-input form-textarea"
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            maxLength={1000}
                            rows={3}
                        />
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label htmlFor="task-priority">
                                Priority
                            </label>
                            <select
                                id="task-priority"
                                className="form-input"
                                value={priority}
                                onChange={(e) => setPriority(e.target.value)}
                            >
                                <option value="low">Low</option>
                                <option value="medium">Medium</option>
                                <option value="high">High</option>
                            </select>
                        </div>

                        <div className="form-group">
                            <label htmlFor="task-status">Status</label>
                            <select
                                id="task-status"
                                className="form-input"
                                value={status}
                                onChange={(e) => setStatus(e.target.value)}
                            >
                                <option value="pending">Pending</option>
                                <option value="in_progress">
                                    In Progress
                                </option>
                                <option value="completed">Completed</option>
                                <option value="blocked">Blocked</option>
                            </select>
                        </div>
                    </div>

                    <div className="form-group">
                        <label htmlFor="task-project">Project</label>
                        <select
                            id="task-project"
                            className="form-input"
                            value={projectId}
                            onChange={(e) =>
                                setProjectId(Number(e.target.value))
                            }
                        >
                            {projects.map((p) => (
                                <option key={p.id} value={p.id}>
                                    {p.name}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="modal-actions">
                        <button
                            type="button"
                            className="btn btn-secondary"
                            onClick={onCancel}
                            disabled={loading}
                        >
                            Cancel
                        </button>
                        <LoadingButton type="submit" loading={loading}>
                            Save
                        </LoadingButton>
                    </div>
                </form>
            </div>
        </div>
    );
}
