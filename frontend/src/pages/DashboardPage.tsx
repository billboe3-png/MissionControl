import { useEffect, useCallback, useState } from "react";
import PageHeader from "../components/common/PageHeader";
import StatusBadge from "../components/common/StatusBadge";
import WidgetCard from "../components/dashboard/WidgetCard";
import FleetWidget from "../components/dashboard/FleetWidget";
import InfraWidget from "../components/dashboard/InfraWidget";
import SystemWidget from "../components/dashboard/SystemWidget";
import ActivityWidget from "../components/dashboard/ActivityWidget";
import { api } from "../services/api";
import { DashboardResponse } from "../types/dashboard";

function formatTimestamp(d: Date | null) {
    if (!d) return "—";
    return d.toLocaleTimeString();
}

export default function DashboardPage() {
    const [data, setData] = useState<DashboardResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

    const load = useCallback(async () => {
        try {
            const result = await api.getDashboard();
            setData(result);
            setError(null);
            setLastRefresh(new Date());
        } catch (e) {
            setError(e instanceof Error ? e.message : "Failed to load");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        load();
        const id = setInterval(load, 15000);
        return () => clearInterval(id);
    }, [load]);

    const automation = data?.automation;
    const ai = data?.ai;

    return (
        <>
            <PageHeader
                title="Operations Workspace"
                subtitle="Single-pane-of-glass view of all infrastructure"
                actions={
                    <div className="page-header-actions">
                        <span className="refresh-indicator">
                            Last refresh: {formatTimestamp(lastRefresh)}
                        </span>
                        <button className="btn btn-sm btn-secondary" onClick={load}>
                            ↻ Refresh
                        </button>
                    </div>
                }
            />

            {error && (
                <div className="error-banner">
                    {error}
                    <button className="btn btn-link" onClick={() => setError(null)}>
                        Dismiss
                    </button>
                </div>
            )}

            {loading && !data && <div className="loading-bar" />}

            {data && (
                <div className="ops-dashboard-grid">
                    <FleetWidget stats={data.agents} />
                    <InfraWidget data={data} />
                    <SystemWidget />

                    <WidgetCard title="System Overview" icon="🖥️">
                        <div className="system-overview-grid">
                            <div className="system-overview-item">
                                <span className="sov-label">PostgreSQL</span>
                                <StatusBadge
                                    status={
                                        data.health.database.status === "healthy"
                                            ? "healthy"
                                            : "error"
                                    }
                                    label={data.health.database.status}
                                />
                            </div>
                            <div className="system-overview-item">
                                <span className="sov-label">Redis</span>
                                <StatusBadge
                                    status={
                                        data.health.redis.status === "healthy"
                                            ? "healthy"
                                            : data.health.redis.status === "unavailable"
                                              ? "neutral"
                                              : "error"
                                    }
                                    label={data.health.redis.status}
                                />
                            </div>
                            <div className="system-overview-item">
                                <span className="sov-label">Backend</span>
                                <StatusBadge
                                    status={
                                        data.health.backend.status === "healthy"
                                            ? "healthy"
                                            : "error"
                                    }
                                    label={data.health.backend.status}
                                />
                            </div>
                            <div className="system-overview-item">
                                <span className="sov-label">Docker</span>
                                <StatusBadge
                                    status={
                                        data.docker.running > 0
                                            ? "healthy"
                                            : "neutral"
                                    }
                                    label={`${data.docker.running} running`}
                                />
                            </div>
                            <div className="system-overview-item">
                                <span className="sov-label">Git</span>
                                <StatusBadge
                                    status={
                                        data.git?.available
                                            ? data.git?.working_tree_clean
                                                ? "healthy"
                                                : "warning"
                                            : "neutral"
                                    }
                                    label={
                                        data.git?.available
                                            ? data.git?.current_branch ?? "unknown"
                                            : "unavailable"
                                    }
                                />
                            </div>
                        </div>
                    </WidgetCard>

                    {automation && (
                        <WidgetCard title="Automation" icon="⚡" to="/automation">
                            <div className="automation-widget-grid">
                                <div className="auto-stat">
                                    <span className="auto-stat-value">{automation.total_playbooks}</span>
                                    <span className="auto-stat-label">Playbooks</span>
                                </div>
                                <div className="auto-stat">
                                    <span className="auto-stat-value">{automation.running}</span>
                                    <span className="auto-stat-label">Running</span>
                                </div>
                                <div className="auto-stat">
                                    <span className="auto-stat-value success">{automation.completed}</span>
                                    <span className="auto-stat-label">Completed</span>
                                </div>
                                <div className="auto-stat">
                                    <span className="auto-stat-value danger">{automation.failed}</span>
                                    <span className="auto-stat-label">Failed</span>
                                </div>
                                <div className="auto-stat">
                                    <span className="auto-stat-value warning">{automation.pending_approvals}</span>
                                    <span className="auto-stat-label">Pending Approvals</span>
                                </div>
                            </div>
                        </WidgetCard>
                    )}

                    {ai && (
                        <WidgetCard title="AI Engine" icon="🧠" to="/ai">
                            <div className="ai-widget-grid">
                                <div className="ai-stat">
                                    <span className="ai-stat-score">{ai.health_score.score}</span>
                                    <span className="ai-stat-grade">{ai.health_score.grade}</span>
                                    <span className="ai-stat-label">Health Score</span>
                                </div>
                                <div className="ai-stat">
                                    <span className="ai-stat-value">{ai.critical_incidents}</span>
                                    <span className="ai-stat-label">Critical Incidents</span>
                                </div>
                                <div className="ai-stat">
                                    <span className="ai-stat-value">{ai.recommendations}</span>
                                    <span className="ai-stat-label">Recommendations</span>
                                </div>
                                <div className="ai-stat">
                                    <span className="ai-stat-value">{ai.correlated_alerts}</span>
                                    <span className="ai-stat-label">Correlated Alerts</span>
                                </div>
                            </div>
                            {ai.top_risks.length > 0 && (
                                <div className="ai-risks">
                                    <span className="ai-risks-title">Top Risks</span>
                                    {ai.top_risks.slice(0, 3).map((risk, i) => (
                                        <div key={i} className="ai-risk-item">
                                            <StatusBadge
                                                status={
                                                    risk.severity === "critical"
                                                        ? "error"
                                                        : risk.severity === "high"
                                                          ? "warning"
                                                          : "info"
                                                }
                                                label={risk.severity}
                                            />
                                            <span className="ai-risk-title">{risk.title}</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </WidgetCard>
                    )}

                    <ActivityWidget />

                    <WidgetCard title="Companies & Sites" icon="🏢" to="/companies">
                        <div className="company-widget-info">
                            <div className="company-stat">
                                <span className="company-stat-value">
                                    {data.integrations?.profiles?.count ?? 0}
                                </span>
                                <span className="company-stat-label">Total Companies</span>
                            </div>
                            <div className="company-stat">
                                <span className="company-stat-value">
                                    {data.projects?.count ?? 0}
                                </span>
                                <span className="company-stat-label">Sites / Projects</span>
                            </div>
                        </div>
                    </WidgetCard>

                    <WidgetCard title="AI Insights" icon="💡">
                        <div className="ai-insights-list">
                            {data.agents && data.agents.total > 0 && (
                                <div className="ai-insight-item">
                                    <span className="ai-insight-icon">🤖</span>
                                    <span className="ai-insight-text">
                                        {data.agents.online} of {data.agents.total} agents online.
                                        Average CPU: {data.agents.avg_cpu.toFixed(1)}%.
                                        Average Memory: {data.agents.avg_memory.toFixed(1)}%.
                                    </span>
                                </div>
                            )}
                            {data.docker.running > 0 && (
                                <div className="ai-insight-item">
                                    <span className="ai-insight-icon">🐳</span>
                                    <span className="ai-insight-text">
                                        {data.docker.running} Docker containers running
                                        ({data.docker.stopped} stopped).
                                    </span>
                                </div>
                            )}
                            {data.tasks.statistics.blocked > 0 && (
                                <div className="ai-insight-item warning">
                                    <span className="ai-insight-icon">⚠️</span>
                                    <span className="ai-insight-text">
                                        {data.tasks.statistics.blocked} tasks are blocked.
                                    </span>
                                </div>
                            )}
                            {data.parking_lot.count > 0 && (
                                <div className="ai-insight-item">
                                    <span className="ai-insight-icon">📋</span>
                                    <span className="ai-insight-text">
                                        {data.parking_lot.count} items in parking lot.
                                    </span>
                                </div>
                            )}
                        </div>
                    </WidgetCard>
                </div>
            )}
        </>
    );
}
