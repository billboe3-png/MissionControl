import StatusBadge from "../common/StatusBadge";
import { ZabbixEvent } from "../../services/zabbix";

interface LatestEventsCardProps {
    events: ZabbixEvent[];
    max?: number;
}

const severityStatus: Record<string, "error" | "warning" | "info" | "healthy"> = {
    disaster: "error",
    high: "error",
    warning: "warning",
    info: "info",
};

export default function LatestEventsCard({ events, max = 5 }: LatestEventsCardProps) {
    const displayed = events.slice(0, max);

    return (
        <div className="ad-info-card">
            <h4>Latest Events</h4>
            {displayed.length === 0 && <p>No recent events</p>}
            {displayed.map((e) => (
                <div key={e.eventid} style={{ marginBottom: "4px" }}>
                    <StatusBadge
                        status={severityStatus[e.severity] ?? "info"}
                        label={e.status}
                    />
                    <span> {e.name} ({e.host})</span>
                </div>
            ))}
        </div>
    );
}
