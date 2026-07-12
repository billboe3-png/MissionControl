import { useState } from "react";
import LoadingButton from "../common/LoadingButton";
import { notesApi } from "../../services/notes";
import { Note, Project } from "../../types/dashboard";

interface NoteModalProps {
    note?: Note;
    projects: Project[];
    onSave: () => void;
    onCancel: () => void;
    onError: (message: string) => void;
}

export default function NoteModal({
    note,
    projects,
    onSave,
    onCancel,
    onError,
}: NoteModalProps) {
    const [title, setTitle] = useState(note?.title ?? "");
    const [content, setContent] = useState(note?.content ?? "");
    const [projectId, setProjectId] = useState<number | null>(
        note?.project_id ? Number(note.project_id) : null,
    );
    const [loading, setLoading] = useState(false);

    const isEditing = note !== undefined;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            if (isEditing) {
                await notesApi.update(note.id, {
                    title,
                    content,
                    project_id: projectId ?? undefined,
                });
            } else {
                await notesApi.create({
                    title,
                    content,
                    project_id: projectId ?? 0,
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
                    {isEditing ? "Edit Note" : "New Note"}
                </h3>

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label htmlFor="note-title">Title</label>
                        <input
                            id="note-title"
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
                        <label htmlFor="note-content">Content</label>
                        <textarea
                            id="note-content"
                            className="form-input form-textarea"
                            value={content}
                            onChange={(e) => setContent(e.target.value)}
                            required
                            rows={6}
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="note-project">Project</label>
                        <select
                            id="note-project"
                            className="form-input"
                            value={projectId ?? ""}
                            onChange={(e) =>
                                setProjectId(
                                    e.target.value
                                        ? Number(e.target.value)
                                        : null,
                                )
                            }
                        >
                            <option value="">No project</option>
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
