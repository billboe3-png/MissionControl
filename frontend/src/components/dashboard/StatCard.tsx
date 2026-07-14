import { Link } from "react-router-dom";

interface StatCardProps {
    label: string;
    value: string | number;
    icon: string;
    to?: string;
    status?: "green" | "amber" | "red" | "gray";
}

export default function StatCard({
    label,
    value,
    icon,
    to,
    status = "gray",
}: StatCardProps) {
    const content = (
        <div className={`stat-card stat-card-${status}`}>
            <span className="stat-card-icon">{icon}</span>
            <div className="stat-card-body">
                <span className="stat-card-value">{value}</span>
                <span className="stat-card-label">{label}</span>
            </div>
        </div>
    );

    return to ? <Link to={to} className="stat-card-link">{content}</Link> : content;
}
