import { Link } from "react-router-dom";

interface ProblemSeverityCardProps {
    severity: string;
    count: number;
    to?: string;
}

const severityMap: Record<string, "error" | "warning" | "info" | "healthy"> = {
    disaster: "error",
    high: "error",
    average: "warning",
    warning: "warning",
    information: "info",
    not_classified: "info",
};

export default function ProblemSeverityCard({ severity, count, to }: ProblemSeverityCardProps) {
    const card = (
        <div className={`stat-card ${to ? "stat-card-clickable" : ""} stat-card-gray`}>
            <div className="stat-card-body">
                <span className="stat-card-value">{count}</span>
                <span className="stat-card-label">{severity}</span>
            </div>
        </div>
    );

    return to ? <Link to={to} style={{ textDecoration: "none", color: "inherit" }}>{card}</Link> : card;
}
