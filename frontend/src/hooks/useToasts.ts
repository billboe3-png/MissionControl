import { useState } from "react";
import { Toast } from "../components/Toast";

let toastId = 0;

export function useToasts(): {
    toasts: Toast[];
    showToast: (message: string, type?: "success" | "error") => void;
    dismissToast: (id: number) => void;
} {
    const [toasts, setToasts] = useState<Toast[]>([]);

    const dismissToast = (id: number) => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
    };

    const showToast = (
        message: string,
        type: "success" | "error" = "success",
    ) => {
        const id = ++toastId;
        setToasts((prev) => [...prev, { id, message, type }]);
    };

    return { toasts, showToast, dismissToast };
}
