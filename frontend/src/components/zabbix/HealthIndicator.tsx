import StatusBadge from "../common/StatusBadge";

interface HealthIndicatorProps {
    status: string;
    label?: string;
}

export default function HealthIndicator({ status, label }: HealthIndicatorProps) {
    const statusType = status === "healthy" ? "healthy" : status === "degraded" ? "warning" : "error";
    return <StatusBadge status={statusType} label={label ?? status} />;
}
