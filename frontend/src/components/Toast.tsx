import { useEffect } from "react";

export interface Toast {
    id: number;
    message: string;
    type: "success" | "error";
}

interface ToastItemProps {
    toast: Toast;
    onDismiss: (id: number) => void;
}

function ToastItem({ toast, onDismiss }: ToastItemProps) {
    useEffect(() => {
        const timer = setTimeout(() => onDismiss(toast.id), 3000);
        return () => clearTimeout(timer);
    }, [toast.id, onDismiss]);

    return (
        <div className={`toast toast-${toast.type}`}>
            <span>{toast.message}</span>
            <button
                className="toast-dismiss"
                onClick={() => onDismiss(toast.id)}
            >
                &times;
            </button>
        </div>
    );
}

interface ToastContainerProps {
    toasts: Toast[];
    onDismiss: (id: number) => void;
}

export default function ToastContainer({
    toasts,
    onDismiss,
}: ToastContainerProps) {
    if (toasts.length === 0) return null;

    return (
        <div className="toast-container">
            {toasts.map((toast) => (
                <ToastItem key={toast.id} toast={toast} onDismiss={onDismiss} />
            ))}
        </div>
    );
}
