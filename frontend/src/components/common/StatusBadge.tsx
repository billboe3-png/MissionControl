export type StatusType = "healthy" | "warning" | "error" | "info" | "neutral";

const statusColors: Record<StatusType, string> = {
    healthy: "green",
    warning: "amber",
    error: "red",
    info: "blue",
    neutral: "gray",
};

interface StatusBadgeProps {
    status: StatusType;
    label: string;
}

export default function StatusBadge({ status, label }: StatusBadgeProps) {
    return (
        <span className={`status-badge ${statusColors[status]}`}>
            <span className="status-badge-dot" />
            {label}
        </span>
    );
}
