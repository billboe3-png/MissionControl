import { useState, useEffect } from "react";
import WidgetCard from "./WidgetCard";
import StatusBadge from "../common/StatusBadge";
import { apiClient } from "../../utils/apiClient";

interface SubsystemCheck {
    component: string;
    status: string;
    latency_ms: number;
    last_check: string;
    details?: string;
}

interface SubsystemsResponse {
    status: string;
    subsystems: Record<string, SubsystemCheck>;
}

const DISPLAY_NAMES: Record<string, string> = {
    postgres: "PostgreSQL",
    redis: "Redis",
    event_bus: "Event Bus",
    dashboard: "Dashboard Aggregator",
    scheduler: "Scheduler",
    automation: "Automation Engine",
    plugins: "Plugin Loader",
    heartbeat_service: "Heartbeat Service",
    agent_state_engine: "Fleet State Engine",
    ai: "AI Service",
};

export default function SystemWidget() {
    const [data, setData] = useState<SubsystemsResponse | null>(null);

    useEffect(() => {
        const load = () =>
            apiClient<SubsystemsResponse>("/api/v1/health/subsystems")
                .then(setData)
                .catch(() => {});
        load();
        const id = setInterval(load, 30000);
        return () => clearInterval(id);
    }, []);

    const subsystems = data?.subsystems ?? {};
    const entries = Object.entries(subsystems).filter(
        ([k]) => k !== "disk_space" && k !== "agents",
    );

    return (
        <WidgetCard title="System" icon="⚙️" to="/infrastructure/health">
            <div className="system-widget-list">
                {entries.length === 0 && (
                    <div className="empty-text">No subsystem data</div>
                )}
                {entries.map(([key, check]) => (
                    <div key={key} className="system-widget-row">
                        <span className="system-widget-name">
                            {DISPLAY_NAMES[key] ?? key}
                        </span>
                        <div className="system-widget-right">
                            <span className="system-widget-latency">
                                {check.latency_ms.toFixed(1)}ms
                            </span>
                            <StatusBadge
                                status={
                                    check.status === "ok"
                                        ? "healthy"
                                        : check.status === "warning"
                                          ? "warning"
                                          : "error"
                                }
                                label={check.status}
                            />
                        </div>
                    </div>
                ))}
            </div>
        </WidgetCard>
    );
}
