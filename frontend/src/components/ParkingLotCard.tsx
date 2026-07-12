import { useState } from "react";
import { ParkingLotItem } from "../types/dashboard";
import { parkingLotApi } from "../services/parkingLot";
import Toolbar from "./common/Toolbar";
import ConfirmDialog from "./common/ConfirmDialog";
import ParkingLotModal from "./modals/ParkingLotModal";

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
        case "done":
            return "badge badge-success";
        case "in_progress":
            return "badge badge-warning";
        case "parked":
            return "badge badge-muted";
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

interface ParkingLotCardProps {
    count: number;
    items: ParkingLotItem[];
    onRefresh: () => void;
    showToast: (message: string, type?: "success" | "error") => void;
}

export default function ParkingLotCard({
    count,
    items,
    onRefresh,
    showToast,
}: ParkingLotCardProps) {
    const [modalOpen, setModalOpen] = useState(false);
    const [editing, setEditing] = useState<ParkingLotItem | undefined>(
        undefined,
    );
    const [confirmDelete, setConfirmDelete] = useState<
        ParkingLotItem | undefined
    >(undefined);
    const [confirmArchive, setConfirmArchive] = useState<
        ParkingLotItem | undefined
    >(undefined);
    const [deleting, setDeleting] = useState(false);
    const [archiving, setArchiving] = useState(false);

    const handleNew = () => {
        setEditing(undefined);
        setModalOpen(true);
    };

    const handleEdit = (item: ParkingLotItem) => {
        setEditing(item);
        setModalOpen(true);
    };

    const handleSave = () => {
        setModalOpen(false);
        setEditing(undefined);
        showToast("Item saved");
        onRefresh();
    };

    const handleDelete = async () => {
        if (!confirmDelete) return;
        setDeleting(true);
        try {
            await parkingLotApi.remove(confirmDelete.id);
            setConfirmDelete(undefined);
            showToast("Item deleted");
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

    const handleArchive = async () => {
        if (!confirmArchive) return;
        setArchiving(true);
        try {
            await parkingLotApi.update(confirmArchive.id, { archived: true });
            setConfirmArchive(undefined);
            showToast("Item archived");
            onRefresh();
        } catch (err) {
            showToast(
                err instanceof Error ? err.message : "Archive failed",
                "error",
            );
        } finally {
            setArchiving(false);
        }
    };

    return (
        <div className="card">
            <div className="card-header">
                <h2>Parking Lot</h2>
                <Toolbar onAdd={handleNew} addLabel="Add Item" />
            </div>

            {count === 0 ? (
                <p className="muted-text">No parked work items.</p>
            ) : (
                <ul className="parking-lot-list">
                    {items.map((item) => (
                        <li key={item.id} className="parking-lot-item">
                            <div className="parking-lot-header">
                                <strong>{item.title}</strong>
                                <span className="badge-group">
                                    <span
                                        className={priorityBadgeClass(
                                            item.priority,
                                        )}
                                    >
                                        {item.priority}
                                    </span>
                                    <span
                                        className={statusBadgeClass(
                                            item.status,
                                        )}
                                    >
                                        {item.status}
                                    </span>
                                </span>
                            </div>
                            {item.description && (
                                <p className="parking-lot-description">
                                    {item.description}
                                </p>
                            )}
                            <div className="item-meta">
                                {item.owner && (
                                    <span>Owner: {item.owner} </span>
                                )}
                                {item.category && (
                                    <span>Category: {item.category} </span>
                                )}
                                <span>
                                    Created {formatDate(item.created_at)}
                                </span>
                            </div>
                            <div className="item-actions">
                                <button
                                    className="btn-icon"
                                    title="Edit"
                                    onClick={() => handleEdit(item)}
                                >
                                    ✎
                                </button>
                                {!item.archived && (
                                    <button
                                        className="btn-icon"
                                        title="Archive"
                                        onClick={() =>
                                            setConfirmArchive(item)
                                        }
                                    >
                                        ↓
                                    </button>
                                )}
                                <button
                                    className="btn-icon btn-icon-danger"
                                    title="Delete"
                                    onClick={() => setConfirmDelete(item)}
                                >
                                    ✕
                                </button>
                            </div>
                        </li>
                    ))}
                </ul>
            )}

            {modalOpen && (
                <ParkingLotModal
                    item={editing}
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
                    title="Delete Item"
                    message={`Are you sure you want to delete "${confirmDelete.title}"? This action cannot be undone.`}
                    confirmLabel="Delete"
                    danger
                    loading={deleting}
                    onConfirm={handleDelete}
                    onCancel={() => setConfirmDelete(undefined)}
                />
            )}

            {confirmArchive && (
                <ConfirmDialog
                    title="Archive Item"
                    message={`Archive "${confirmArchive.title}"?`}
                    confirmLabel="Archive"
                    loading={archiving}
                    onConfirm={handleArchive}
                    onCancel={() => setConfirmArchive(undefined)}
                />
            )}
        </div>
    );
}
