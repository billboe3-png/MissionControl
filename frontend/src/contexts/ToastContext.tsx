import { createContext, useCallback, useContext, useState } from "react";
import ToastContainer, { Toast } from "../components/Toast";

let toastId = 0;

interface ToastContextValue {
    showToast: (message: string, type?: "success" | "error") => void;
}

const ToastContext = createContext<ToastContextValue>({
    showToast: () => {},
});

export function ToastProvider({ children }: { children: React.ReactNode }) {
    const [toasts, setToasts] = useState<Toast[]>([]);

    const dismissToast = useCallback((id: number) => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
    }, []);

    const showToast = useCallback(
        (message: string, type: "success" | "error" = "success") => {
            const id = ++toastId;
            setToasts((prev) => [...prev, { id, message, type }]);
        },
        [],
    );

    return (
        <ToastContext.Provider value={{ showToast }}>
            {children}
            <ToastContainer toasts={toasts} onDismiss={dismissToast} />
        </ToastContext.Provider>
    );
}

export function useToast() {
    return useContext(ToastContext);
}
