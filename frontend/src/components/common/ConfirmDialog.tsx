interface ConfirmDialogProps {
    title: string;
    message: string;
    confirmLabel?: string;
    onConfirm: () => void;
    onCancel: () => void;
    loading?: boolean;
    danger?: boolean;
}

export default function ConfirmDialog({
    title,
    message,
    confirmLabel = "Confirm",
    onConfirm,
    onCancel,
    loading = false,
    danger = false,
}: ConfirmDialogProps) {
    return (
        <div className="modal-overlay" onClick={onCancel}>
            <div
                className="modal-content"
                onClick={(e) => e.stopPropagation()}
            >
                <h3 className="modal-title">{title}</h3>
                <p className="modal-message">{message}</p>
                <div className="modal-actions">
                    <button
                        className="btn btn-secondary"
                        onClick={onCancel}
                        disabled={loading}
                    >
                        Cancel
                    </button>
                    <button
                        className={danger ? "btn btn-danger" : "btn btn-primary"}
                        onClick={onConfirm}
                        disabled={loading}
                    >
                        {loading ? "Working..." : confirmLabel}
                    </button>
                </div>
            </div>
        </div>
    );
}
