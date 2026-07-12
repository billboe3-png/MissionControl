interface LoadingButtonProps {
    loading: boolean;
    disabled?: boolean;
    onClick?: () => void;
    className?: string;
    type?: "button" | "submit";
    children: React.ReactNode;
}

export default function LoadingButton({
    loading,
    disabled = false,
    onClick,
    className = "btn btn-primary",
    type = "button",
    children,
}: LoadingButtonProps) {
    return (
        <button
            type={type}
            className={className}
            onClick={onClick}
            disabled={loading || disabled}
        >
            {loading && <span className="spinner" />}
            {children}
        </button>
    );
}
