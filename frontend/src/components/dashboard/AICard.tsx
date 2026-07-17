import { Link } from "react-router-dom";

interface AICardProps {
    data: {
        health_score?: { score?: number; grade?: string };
        critical_incidents?: number;
        recommendations?: number;
        correlated_alerts?: number;
        top_risks?: Array<{ title?: string; message?: string; severity?: string }>;
    };
}

export default function AICard({ data }: AICardProps) {
    const healthScore = data.health_score?.score ?? 0;
    const grade = data.health_score?.grade ?? "N/A";
    const critical = data.critical_incidents ?? 0;
    const recommendations = data.recommendations ?? 0;

    const scoreColor =
        healthScore >= 80 ? "green" :
        healthScore >= 60 ? "amber" : "red";

    return (
        <div className="dashboard-section ai-card">
            <h3>AI Operations</h3>
            <div className="ai-card-score">
                <span className={`ai-grade ai-grade-${scoreColor}`}>
                    {grade}
                </span>
                <span className="ai-score-value">
                    {healthScore.toFixed(0)}
                </span>
            </div>
            <div className="ai-card-stats">
                <div className="ai-stat">
                    <span className="ai-stat-label">Critical</span>
                    <span className={`ai-stat-value ${critical > 0 ? "ai-critical" : ""}`}>
                        {critical}
                    </span>
                </div>
                <div className="ai-stat">
                    <span className="ai-stat-label">Recommendations</span>
                    <span className="ai-stat-value">
                        {recommendations}
                    </span>
                </div>
                <div className="ai-stat">
                    <span className="ai-stat-label">Correlated</span>
                    <span className="ai-stat-value">
                        {data.correlated_alerts ?? 0}
                    </span>
                </div>
            </div>
            <div className="ai-card-links">
                <Link to="/ai" className="ai-link">
                    Overview
                </Link>
                <Link to="/ai/recommendations" className="ai-link">
                    Recommendations
                </Link>
                <Link to="/ai/health" className="ai-link">
                    Health
                </Link>
            </div>
        </div>
    );
}
