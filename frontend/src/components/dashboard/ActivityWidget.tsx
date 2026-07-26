import { useState, useEffect } from "react";
import WidgetCard from "./WidgetCard";
import StatusBadge from "../common/StatusBadge";
import { apiClient } from "../../utils/apiClient";

interface ActivityItem {
    id: string;
    type: string;
    message: string;
    timestamp: string;
    status: string;
    agent?: string;
}

export default function ActivityWidget() {
    const [items, setItems] = useState<ActivityItem[]>([]);

    useEffect(() => {
        const load = async () => {
            try {
                const cmds = await apiClient<{ items: Array<{ id: number; command: string; status: string; created_at: string | null; agent_id: number }> }>("/api/v1/agents/commands/all?limit=10");
                const mapped: ActivityItem[] = (cmds.items ?? []).map((c) => ({
                    id: `cmd-${c.id}`,
                    type: "command",
                    message: c.command.length > 80 ? c.command.slice(0, 80) + "..." : c.command,
                    timestamp: c.created_at ?? "",
                    status: c.status,
                    agent: `Agent ${c.agent_id}`,
                }));
                setItems(mapped);
            } catch {
                setItems([]);
            }
        };
        load();
        const id = setInterval(load, 20000);
        return () => clearInterval(id);
    }, []);

    return (
        <WidgetCard title="Activity" icon="📋" to="/remote/history">
            <div className="activity-widget-list">
                {items.length === 0 && (
                    <div className="empty-text">No recent activity</div>
                )}
                {items.map((item) => (
                    <div key={item.id} className="activity-widget-row">
                        <div className="activity-widget-dot">
                            <StatusBadge
                                status={
                                    item.status === "completed"
                                        ? "healthy"
                                        : item.status === "failed"
                                          ? "error"
                                          : item.status === "running"
                                            ? "info"
                                            : "warning"
                                }
                                label=""
                            />
                        </div>
                        <div className="activity-widget-content">
                            <span className="activity-widget-message">{item.message}</span>
                            <span className="activity-widget-meta">
                                {item.agent && <span>{item.agent}</span>}
                                {item.timestamp && (
                                    <span>
                                        {new Date(item.timestamp).toLocaleTimeString()}
                                    </span>
                                )}
                            </span>
                        </div>
                        <span className="activity-widget-status">{item.status}</span>
                    </div>
                ))}
            </div>
        </WidgetCard>
    );
}
