import { useState } from "react";
import LoadingButton from "../common/LoadingButton";
import { projectsApi } from "../../services/projects";
import { Project } from "../../types/dashboard";

interface ProjectModalProps {
    project?: Project;
    onSave: () => void;
    onCancel: () => void;
    onError: (message: string) => void;
}

export default function ProjectModal({
    project,
    onSave,
    onCancel,
    onError,
}: ProjectModalProps) {
    const [name, setName] = useState(project?.name ?? "");
    const [description, setDescription] = useState(
        project?.description ?? "",
    );
    const [active, setActive] = useState(project?.active ?? true);
    const [loading, setLoading] = useState(false);

    const isEditing = project !== undefined;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            if (isEditing) {
                await projectsApi.update(project.id, {
                    name,
                    description: description || undefined,
                    active,
                });
            } else {
                await projectsApi.create({
                    name,
                    description: description || undefined,
                    active,
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
                    {isEditing ? "Edit Project" : "New Project"}
                </h3>

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label htmlFor="project-name">Name</label>
                        <input
                            id="project-name"
                            type="text"
                            className="form-input"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            required
                            maxLength={200}
                            autoFocus
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="project-description">
                            Description
                        </label>
                        <textarea
                            id="project-description"
                            className="form-input form-textarea"
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            maxLength={1000}
                            rows={3}
                        />
                    </div>

                    <div className="form-group form-group-inline">
                        <label htmlFor="project-active">Active</label>
                        <input
                            id="project-active"
                            type="checkbox"
                            checked={active}
                            onChange={(e) => setActive(e.target.checked)}
                        />
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
                        <LoadingButton
                            type="submit"
                            loading={loading}
                        >
                            Save
                        </LoadingButton>
                    </div>
                </form>
            </div>
        </div>
    );
}
