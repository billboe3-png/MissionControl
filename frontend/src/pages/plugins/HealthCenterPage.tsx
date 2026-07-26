import { useState, useEffect } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
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
    component: string;
    last_check: string;
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
    disk_space: "Disk Space",
    agents: "Agent State Engine",
};

const DISPLAY_ICONS: Record<string, string> = {
    postgres: "🐘",
    redis: "⚡",
    event_bus: "📨",
    dashboard: "📊",
    scheduler: "⏰",
    automation: "🤖",
    plugins: "🧩",
    heartbeat_service: "💓",
    agent_state_engine: "🌐",
    ai: "🧠",
    disk_space: "💾",
    agents: "🤖",
};

export default function HealthCenterPage() {
    const [data, setData] = useState<SubsystemsResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const load = async () => {
            try {
                const result = await apiClient<SubsystemsResponse>("/api/v1/health/subsystems");
                setData(result);
                setError(null);
            } catch (e) {
                setError(e instanceof Error ? e.message : "Failed to load");
            } finally {
                setLoading(false);
            }
        };
        load();
        const id = setInterval(load, 15000);
        return () => clearInterval(id);
    }, []);

    const subsystems = data?.subsystems ?? {};
    const entries = Object.entries(subsystems);
    const healthyCount = entries.filter(([, c]) => c.status === "ok").length;
    const warningCount = entries.filter(([, c]) => c.status === "warning").length;
    const errorCount = entries.filter(([, c]) => c.status === "error").length;

    return (
        <>
            <PageHeader
                title="Health Center"
                subtitle="Subsystem health status with latency metrics"
            />

            {error && <div className="error-banner">{error}</div>}

            {data && (
                <div className="fleet-stats-bar">
                    <div className="fleet-stat-chip">
                        <span className="fleet-stat-chip-value">{entries.length}</span>
                        <span className="fleet-stat-chip-label">Total</span>
                    </div>
                    <div className="fleet-stat-chip success">
                        <span className="fleet-stat-chip-value">{healthyCount}</span>
                        <span className="fleet-stat-chip-label">Healthy</span>
                    </div>
                    {warningCount > 0 && (
                        <div className="fleet-stat-chip" style={{ borderLeftColor: "var(--warning)" }}>
                            <span className="fleet-stat-chip-value">{warningCount}</span>
                            <span className="fleet-stat-chip-label">Warning</span>
                        </div>
                    )}
                    {errorCount > 0 && (
                        <div className="fleet-stat-chip danger">
                            <span className="fleet-stat-chip-value">{errorCount}</span>
                            <span className="fleet-stat-chip-label">Error</span>
                        </div>
                    )}
                    <div className="fleet-stat-chip">
                        <StatusBadge
                            status={
                                data.status === "healthy"
                                    ? "healthy"
                                    : data.status === "degraded"
                                      ? "warning"
                                      : "error"
                            }
                            label={data.status}
                        />
                    </div>
                </div>
            )}

            {loading && !data ? (
                <div className="loading-bar" />
            ) : (
                <div className="health-center-grid">
                    {entries.map(([key, check]) => (
                        <div key={key} className="health-center-card">
                            <div className="health-center-header">
                                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                    <span>{DISPLAY_ICONS[key] ?? "⚙️"}</span>
                                    <span className="health-center-name">
                                        {DISPLAY_NAMES[key] ?? key}
                                    </span>
                                </div>
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
                            <div className="health-center-metrics">
                                <div className="health-center-metric">
                                    <span className="health-center-metric-label">Latency</span>
                                    <span className="health-center-metric-value">
                                        {check.latency_ms.toFixed(2)}ms
                                    </span>
                                </div>
                                <div className="health-center-metric">
                                    <span className="health-center-metric-label">Last Check</span>
                                    <span className="health-center-metric-value">
                                        {check.last_check
                                            ? new Date(check.last_check).toLocaleTimeString()
                                            : "—"}
                                    </span>
                                </div>
                            </div>
                            {check.details && (
                                <div style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                                    {check.details}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </>
    );
}
