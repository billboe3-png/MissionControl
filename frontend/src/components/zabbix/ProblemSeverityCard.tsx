import StatusBadge from "../common/StatusBadge";

interface ProblemSeverityCardProps {
    severity: string;
    count: number;
}

const severityMap: Record<string, "error" | "warning" | "info" | "healthy"> = {
    disaster: "error",
    high: "error",
    warning: "warning",
    info: "info",
};

export default function ProblemSeverityCard({ severity, count }: ProblemSeverityCardProps) {
    return (
        <div className="stat-card stat-card-gray">
            <div className="stat-card-body">
                <span className="stat-card-value">{count}</span>
                <span className="stat-card-label">{severity}</span>
            </div>
        </div>
    );
}
