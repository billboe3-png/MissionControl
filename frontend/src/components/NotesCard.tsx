import { useState } from "react";
import { Note, Project } from "../types/dashboard";
import { notesApi } from "../services/notes";
import Toolbar from "./common/Toolbar";
import ConfirmDialog from "./common/ConfirmDialog";
import NoteModal from "./modals/NoteModal";

function formatDate(iso: string): string {
    const date = new Date(iso);
    return date.toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
    });
}

function truncate(content: string, max: number): string {
    if (content.length <= max) return content;
    return content.slice(0, max).trimEnd() + "...";
}

interface NotesCardProps {
    count: number;
    items: Note[];
    projects: Project[];
    onRefresh: () => void;
    showToast: (message: string, type?: "success" | "error") => void;
}

export default function NotesCard({
    count,
    items,
    projects,
    onRefresh,
    showToast,
}: NotesCardProps) {
    const [modalOpen, setModalOpen] = useState(false);
    const [editing, setEditing] = useState<Note | undefined>(undefined);
    const [confirmDelete, setConfirmDelete] = useState<Note | undefined>(
        undefined,
    );
    const [deleting, setDeleting] = useState(false);

    const handleNew = () => {
        setEditing(undefined);
        setModalOpen(true);
    };

    const handleEdit = (note: Note) => {
        setEditing(note);
        setModalOpen(true);
    };

    const handleSave = () => {
        setModalOpen(false);
        setEditing(undefined);
        showToast("Note saved");
        onRefresh();
    };

    const handleDelete = async () => {
        if (!confirmDelete) return;
        setDeleting(true);
        try {
            await notesApi.remove(confirmDelete.id);
            setConfirmDelete(undefined);
            showToast("Note deleted");
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

    return (
        <div className="card">
            <div className="card-header">
                <h2>Notes</h2>
                <Toolbar onAdd={handleNew} addLabel="New Note" />
            </div>

            {count === 0 ? (
                <p className="muted-text">No notes yet.</p>
            ) : (
                <ul className="status-list">
                    {items.map((note) => (
                        <li key={note.id}>
                            <span className="item-content">
                                <strong>{note.title}</strong>
                                {note.project_name && (
                                    <span className="item-meta">
                                        {note.project_name} &middot; Created{" "}
                                        {formatDate(note.created_at)}
                                    </span>
                                )}
                                {!note.project_name && (
                                    <span className="item-meta">
                                        Created {formatDate(note.created_at)}
                                    </span>
                                )}
                                <span className="item-description">
                                    {truncate(note.content, 120)}
                                </span>
                            </span>
                            <div className="item-actions">
                                <button
                                    className="btn-icon"
                                    title="Edit"
                                    onClick={() => handleEdit(note)}
                                >
                                    ✎
                                </button>
                                <button
                                    className="btn-icon btn-icon-danger"
                                    title="Delete"
                                    onClick={() => setConfirmDelete(note)}
                                >
                                    ✕
                                </button>
                            </div>
                        </li>
                    ))}
                </ul>
            )}

            {modalOpen && (
                <NoteModal
                    note={editing}
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
                    title="Delete Note"
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
