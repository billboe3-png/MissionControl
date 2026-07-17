import { Link } from "react-router-dom";

interface AgentCardProps {
    data: {
        total: number;
        online: number;
        offline: number;
        avg_cpu: number;
        avg_memory: number;
    };
}

export default function AgentCard({ data }: AgentCardProps) {
    return (
        <div className="dashboard-section dashboard-agent-card">
            <div className="dashboard-agent-header">
                <h3>Agents</h3>
                <Link to="/agents" className="btn btn-link btn-sm">
                    Manage
                </Link>
            </div>
            <div className="dashboard-agent-stats">
                <div className="dashboard-agent-stat">
                    <span className="dashboard-agent-stat-label">Total</span>
                    <span className="dashboard-agent-stat-value">{data.total}</span>
                </div>
                <div className="dashboard-agent-stat">
                    <span className="dashboard-agent-stat-label">Online</span>
                    <span className={`dashboard-agent-stat-value ${data.online > 0 ? "agent-online" : ""}`}>
                        {data.online}
                    </span>
                </div>
                <div className="dashboard-agent-stat">
                    <span className="dashboard-agent-stat-label">Offline</span>
                    <span className={`dashboard-agent-stat-value ${data.offline > 0 ? "agent-offline" : ""}`}>
                        {data.offline}
                    </span>
                </div>
            </div>
            {data.online > 0 && (
                <div className="dashboard-agent-metrics">
                    <div className="dashboard-agent-metric">
                        <span className="dashboard-agent-metric-label">Avg CPU</span>
                        <span className={`dashboard-agent-metric-value ${data.avg_cpu >= 80 ? "danger" : data.avg_cpu >= 60 ? "warning" : ""}`}>
                            {data.avg_cpu}%
                        </span>
                    </div>
                    <div className="dashboard-agent-metric">
                        <span className="dashboard-agent-metric-label">Avg Memory</span>
                        <span className={`dashboard-agent-metric-value ${data.avg_memory >= 80 ? "danger" : data.avg_memory >= 60 ? "warning" : ""}`}>
                            {data.avg_memory}%
                        </span>
                    </div>
                </div>
            )}
        </div>
    );
}
