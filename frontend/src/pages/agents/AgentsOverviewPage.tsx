import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import EmptyState from "../../components/common/EmptyState";
import { agentsApi, Agent } from "../../services/agents";

function formatUptime(dateStr: string | null): string {
    if (!dateStr) return "Never";
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "Just now";
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
}

function HealthBar({
    label,
    value,
}: {
    label: string;
    value: number | null;
}) {
    const pct = value ?? 0;
    const color =
        pct > 90 ? "#ef4444" : pct > 70 ? "#f59e0b" : "#22c55e";
    return (
        <div className="agent-health-bar">
            <span className="agent-health-label">{label}</span>
            <div className="agent-health-track">
                <div
                    className="agent-health-fill"
                    style={{ width: `${pct}%`, backgroundColor: color }}
                />
            </div>
            <span className="agent-health-value">{pct.toFixed(1)}%</span>
        </div>
    );
}

export default function AgentsOverviewPage() {
    const [agents, setAgents] = useState<Agent[]>([]);
    const [online, setOnline] = useState(0);
    const [offline, setOffline] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const load = async () => {
        try {
            const data = await agentsApi.list();
            setAgents(data.items);
            setOnline(data.online);
            setOffline(data.offline);
        } catch (e) {
            setError(e instanceof Error ? e.message : "Failed to load");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        load();
        const interval = setInterval(load, 15000);
        return () => clearInterval(interval);
    }, []);

    if (loading) return <div className="loading-bar" />;

    return (
        <>
            <PageHeader
                title="Agents"
                subtitle="Manage Mission Control Agents across your infrastructure"
            />

            {error && (
                <div className="error-banner">
                    {error}
                    <button
                        className="btn btn-link"
                        onClick={() => setError(null)}
                    >
                        Dismiss
                    </button>
                </div>
            )}

            <div className="dashboard-stats">
                <div className="stat-card">
                    <div className="stat-card-value">{agents.length}</div>
                    <div className="stat-card-label">Total Agents</div>
                </div>
                <div className="stat-card">
                    <div
                        className="stat-card-value"
                        style={{ color: "#22c55e" }}
                    >
                        {online}
                    </div>
                    <div className="stat-card-label">Online</div>
                </div>
                <div className="stat-card">
                    <div
                        className="stat-card-value"
                        style={{ color: "#ef4444" }}
                    >
                        {offline}
                    </div>
                    <div className="stat-card-label">Offline</div>
                </div>
            </div>

            {agents.length === 0 && !error ? (
                <EmptyState
                    icon="🤖"
                    title="No agents registered"
                    description="Deploy the Mission Control Agent to your systems and register them here."
                />
            ) : (
                <div className="agent-grid">
                    {agents.map((agent) => (
                        <Link
                            key={agent.id}
                            to={`/agents/${agent.id}`}
                            className={`agent-card ${agent.status}`}
                            style={{ textDecoration: "none", color: "inherit" }}
                        >
                            <div className="agent-card-header">
                                <div className="agent-card-title">
                                    <StatusBadge
                                        status={
                                            agent.status === "online"
                                                ? "healthy"
                                                : "error"
                                        }
                                        label={
                                            agent.status === "online"
                                                ? "Online"
                                                : "Offline"
                                        }
                                    />
                                    <h3>{agent.name}</h3>
                                </div>
                                <span className="agent-card-hostname">
                                    {agent.hostname}
                                </span>
                            </div>

                            <div className="agent-card-meta">
                                {agent.operating_system && (
                                    <span className="agent-meta-item">
                                        {agent.operating_system}
                                    </span>
                                )}
                                {agent.agent_version && (
                                    <span className="agent-meta-item">
                                        v{agent.agent_version}
                                    </span>
                                )}
                                {agent.ip_address && (
                                    <span className="agent-meta-item">
                                        {agent.ip_address}
                                    </span>
                                )}
                            </div>

                            {agent.status === "online" && (
                                <div className="agent-card-health">
                                    <HealthBar
                                        label="CPU"
                                        value={agent.cpu_percent}
                                    />
                                    <HealthBar
                                        label="RAM"
                                        value={agent.memory_percent}
                                    />
                                    <HealthBar
                                        label="Disk"
                                        value={agent.disk_percent}
                                    />
                                </div>
                            )}

                            <div className="agent-card-footer">
                                <span className="agent-heartbeat">
                                    Last heartbeat:{" "}
                                    {formatUptime(agent.last_heartbeat)}
                                </span>
                                {agent.active_plugins && (
                                    <span className="agent-plugins">
                                        Plugins: {agent.active_plugins}
                                    </span>
                                )}
                            </div>
                        </Link>
                    ))}
                </div>
            )}
        </>
    );
}
