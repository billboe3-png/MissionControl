import { Link } from "react-router-dom";

interface AutomationCardProps {
    data: {
        total_playbooks: number;
        total_executions: number;
        running: number;
        completed: number;
        failed: number;
        pending_approvals: number;
        audit_entries: number;
    };
}

export default function AutomationCard({ data }: AutomationCardProps) {
    return (
        <div className="dashboard-section dashboard-agent-card">
            <div className="dashboard-agent-header">
                <h3>Automation</h3>
                <Link to="/automation" className="btn btn-link btn-sm">
                    Manage
                </Link>
            </div>
            <div className="dashboard-agent-stats">
                <div className="dashboard-agent-stat">
                    <span className="dashboard-agent-stat-label">Playbooks</span>
                    <span className="dashboard-agent-stat-value">{data.total_playbooks}</span>
                </div>
                <div className="dashboard-agent-stat">
                    <span className="dashboard-agent-stat-label">Executions</span>
                    <span className="dashboard-agent-stat-value">{data.total_executions}</span>
                </div>
                <div className="dashboard-agent-stat">
                    <span className="dashboard-agent-stat-label">Running</span>
                    <span className={`dashboard-agent-stat-value ${data.running > 0 ? "agent-online" : ""}`}>
                        {data.running}
                    </span>
                </div>
                <div className="dashboard-agent-stat">
                    <span className="dashboard-agent-stat-label">Failed</span>
                    <span className={`dashboard-agent-stat-value ${data.failed > 0 ? "agent-offline" : ""}`}>
                        {data.failed}
                    </span>
                </div>
            </div>
            <div className="dashboard-agent-metrics">
                <div className="dashboard-agent-metric">
                    <span className="dashboard-agent-metric-label">Success Rate</span>
                    <span className={`dashboard-agent-metric-value ${data.total_executions > 0 && data.failed === 0 ? "" : data.failed > 0 ? "warning" : ""}`}>
                        {data.total_executions > 0
                            ? `${Math.round((data.completed / data.total_executions) * 100)}%`
                            : "—"}
                    </span>
                </div>
                <div className="dashboard-agent-metric">
                    <span className="dashboard-agent-metric-label">Pending</span>
                    <span className={`dashboard-agent-metric-value ${data.pending_approvals > 0 ? "warning" : ""}`}>
                        {data.pending_approvals}
                    </span>
                </div>
            </div>
        </div>
    );
}
