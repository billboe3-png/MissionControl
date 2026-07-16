import { useEffect, useState } from "react";
import { aiApi, type AIOverview } from "../../services/ai";
import PageHeader from "../../components/common/PageHeader";
import StatCard from "../../components/dashboard/StatCard";

export default function AIOverviewPage() {
    const [data, setData] = useState<AIOverview | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        aiApi
            .getOverview()
            .then(setData)
            .catch((e: Error) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (loading) return <div className="loading-bar" />;
    if (error) return <div className="error-banner">{error}</div>;
    if (!data) return null;

    const hs = data.health_score;

    return (
        <>
            <PageHeader
                title="AI Operations"
                subtitle="Intelligent infrastructure analysis"
            />
            <div className="dashboard-stats">
                <StatCard
                    label="Health Score"
                    value={`${hs.score.toFixed(0)} (${hs.grade})`}
                    icon="🤖"
                    to="/ai/health"
                    status={
                        hs.score >= 80 ? "green" :
                        hs.score >= 60 ? "amber" : "red"
                    }
                />
                <StatCard
                    label="Critical Incidents"
                    value={data.critical_incidents}
                    icon="🚨"
                    to="/ai/incidents"
                    status={data.critical_incidents > 0 ? "red" : "green"}
                />
                <StatCard
                    label="High Incidents"
                    value={data.high_incidents}
                    icon="⚠️"
                    to="/ai/incidents"
                    status={data.high_incidents > 0 ? "amber" : "green"}
                />
                <StatCard
                    label="Recommendations"
                    value={data.recommendations}
                    icon="💡"
                    to="/ai/recommendations"
                    status={data.recommendations > 0 ? "amber" : "gray"}
                />
                <StatCard
                    label="Correlated Alerts"
                    value={data.correlated_alerts}
                    icon="🔗"
                    to="/ai/correlations"
                    status={data.correlated_alerts > 0 ? "amber" : "green"}
                />
            </div>

            <div className="dashboard-row">
                <div className="dashboard-section">
                    <h3>System Health</h3>
                    {hs.breakdown && hs.breakdown.length > 0 ? (
                        <div className="ai-health-breakdown">
                            {hs.breakdown.map((item) => (
                                <div
                                    key={item.source}
                                    className="ai-health-item"
                                >
                                    <span className="ai-health-source">
                                        {item.source}
                                    </span>
                                    <span
                                        className={`ai-health-status ai-health-${item.status}`}
                                    >
                                        {item.status} ({item.score.toFixed(0)})
                                    </span>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="empty-text">No health data available</p>
                    )}
                </div>

                <div className="dashboard-section">
                    <h3>Top Risks</h3>
                    {data.top_risks && data.top_risks.length > 0 ? (
                        <div className="ai-risk-list">
                            {data.top_risks.slice(0, 5).map((risk, idx) => (
                                <div
                                    key={idx}
                                    className={`ai-risk-item ai-risk-${risk.criticality}`}
                                >
                                    <span className="ai-risk-source">
                                        {risk.source}
                                    </span>
                                    <span className="ai-risk-host">
                                        {risk.host_name}
                                    </span>
                                    <span className="ai-risk-priority">
                                        {risk.priority}
                                    </span>
                                    <span className="ai-risk-message">
                                        {risk.message.substring(0, 80)}
                                    </span>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="empty-text">No risks detected</p>
                    )}
                </div>
            </div>
        </>
    );
}
