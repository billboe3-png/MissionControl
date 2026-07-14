import StatusBadge from "../common/StatusBadge";

interface ZabbixSummaryCardProps {
    label: string;
    value: string | number;
    connected: boolean;
}

export default function ZabbixSummaryCard({ label, value, connected }: ZabbixSummaryCardProps) {
    return (
        <div className={`stat-card stat-card-${connected ? "green" : "red"}`}>
            <div className="stat-card-body">
                <span className="stat-card-value">{value}</span>
                <span className="stat-card-label">{label}</span>
            </div>
        </div>
    );
}
