import { Link } from "react-router-dom";
import StatusBadge from "../common/StatusBadge";
import WidgetCard from "./WidgetCard";
import { AgentStats } from "../../types/dashboard";

interface FleetWidgetProps {
    stats: AgentStats | undefined;
}

function statusVariant(online: number, total: number) {
    if (total === 0) return "neutral" as const;
    if (online === total) return "healthy" as const;
    if (online > total * 0.5) return "warning" as const;
    return "error" as const;
}

export default function FleetWidget({ stats }: FleetWidgetProps) {
    const total = stats?.total ?? 0;
    const online = stats?.online ?? 0;
    const offline = stats?.offline ?? 0;

    return (
        <WidgetCard title="Fleet" icon="🤖" to="/agents">
            <div className="fleet-widget-grid">
                <div className="fleet-stat">
                    <span className="fleet-stat-value">{total}</span>
                    <span className="fleet-stat-label">Total Agents</span>
                </div>
                <div className="fleet-stat">
                    <span className="fleet-stat-value success">{online}</span>
                    <span className="fleet-stat-label">Online</span>
                </div>
                <div className="fleet-stat">
                    <span className="fleet-stat-value danger">{offline}</span>
                    <span className="fleet-stat-label">Offline</span>
                </div>
            </div>
            <div className="fleet-widget-bar">
                <div className="fleet-bar-track">
                    <div
                        className="fleet-bar-fill"
                        style={{
                            width: total > 0 ? `${(online / total) * 100}%` : "0%",
                        }}
                    />
                </div>
                <span className="fleet-bar-text">
                    {total > 0 ? `${Math.round((online / total) * 100)}%` : "—"} online
                </span>
            </div>
            <StatusBadge
                status={statusVariant(online, total)}
                label={total > 0 ? `${online}/${total} online` : "No agents"}
            />
            <div className="fleet-widget-footer">
                <Link to="/agents" className="widget-link">
                    Manage fleet
                </Link>
            </div>
        </WidgetCard>
    );
}
