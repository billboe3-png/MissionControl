import { Link } from "react-router-dom";

interface ZabbixSummaryCardProps {
    label: string;
    value: string | number;
    connected: boolean;
    to?: string;
}

export default function ZabbixSummaryCard({ label, value, connected, to }: ZabbixSummaryCardProps) {
    const card = (
        <div className={`stat-card ${to ? "stat-card-clickable" : ""} stat-card-${connected ? "green" : "red"}`}>
            <div className="stat-card-body">
                <span className="stat-card-value">{value}</span>
                <span className="stat-card-label">{label}</span>
            </div>
        </div>
    );

    return to ? <Link to={to} style={{ textDecoration: "none", color: "inherit" }}>{card}</Link> : card;
}
