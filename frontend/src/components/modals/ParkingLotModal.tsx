import { useState } from "react";
import LoadingButton from "../common/LoadingButton";
import { parkingLotApi } from "../../services/parkingLot";
import { ParkingLotItem } from "../../types/dashboard";

interface ParkingLotModalProps {
    item?: ParkingLotItem;
    onSave: () => void;
    onCancel: () => void;
    onError: (message: string) => void;
}

export default function ParkingLotModal({
    item,
    onSave,
    onCancel,
    onError,
}: ParkingLotModalProps) {
    const [title, setTitle] = useState(item?.title ?? "");
    const [description, setDescription] = useState(
        item?.description ?? "",
    );
    const [priority, setPriority] = useState(item?.priority ?? "medium");
    const [status, setStatus] = useState(item?.status ?? "parked");
    const [owner, setOwner] = useState(item?.owner ?? "");
    const [category, setCategory] = useState(item?.category ?? "");
    const [labels, setLabels] = useState(item?.labels ?? "");
    const [targetSprint, setTargetSprint] = useState(
        item?.target_sprint ?? "",
    );
    const [loading, setLoading] = useState(false);

    const isEditing = item !== undefined;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            const payload = {
                title,
                description: description || undefined,
                priority,
                status,
                owner: owner || undefined,
                category: category || undefined,
                labels: labels || undefined,
                target_sprint: targetSprint || undefined,
            };

            if (isEditing) {
                await parkingLotApi.update(item.id, payload);
            } else {
                await parkingLotApi.create(payload);
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
                className="modal-content modal-content-wide"
                onClick={(e) => e.stopPropagation()}
            >
                <h3 className="modal-title">
                    {isEditing ? "Edit Item" : "New Item"}
                </h3>

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label htmlFor="pl-title">Title</label>
                        <input
                            id="pl-title"
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
                        <label htmlFor="pl-description">
                            Description
                        </label>
                        <textarea
                            id="pl-description"
                            className="form-input form-textarea"
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            rows={3}
                        />
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label htmlFor="pl-priority">
                                Priority
                            </label>
                            <select
                                id="pl-priority"
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
                            <label htmlFor="pl-status">Status</label>
                            <select
                                id="pl-status"
                                className="form-input"
                                value={status}
                                onChange={(e) => setStatus(e.target.value)}
                            >
                                <option value="parked">Parked</option>
                                <option value="in_progress">
                                    In Progress
                                </option>
                                <option value="done">Done</option>
                            </select>
                        </div>
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label htmlFor="pl-owner">Owner</label>
                            <input
                                id="pl-owner"
                                type="text"
                                className="form-input"
                                value={owner}
                                onChange={(e) => setOwner(e.target.value)}
                                maxLength={200}
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="pl-category">
                                Category
                            </label>
                            <input
                                id="pl-category"
                                type="text"
                                className="form-input"
                                value={category}
                                onChange={(e) => setCategory(e.target.value)}
                                maxLength={100}
                            />
                        </div>
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label htmlFor="pl-labels">Labels</label>
                            <input
                                id="pl-labels"
                                type="text"
                                className="form-input"
                                value={labels}
                                onChange={(e) => setLabels(e.target.value)}
                                placeholder="comma-separated"
                            />
                        </div>

                        <div className="form-group">
                            <label htmlFor="pl-sprint">
                                Target Sprint
                            </label>
                            <input
                                id="pl-sprint"
                                type="text"
                                className="form-input"
                                value={targetSprint}
                                onChange={(e) =>
                                    setTargetSprint(e.target.value)
                                }
                                maxLength={100}
                            />
                        </div>
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
