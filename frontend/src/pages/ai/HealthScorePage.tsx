import { useEffect, useState } from "react";
import { aiApi, type AIHealthScore } from "../../services/ai";
import PageHeader from "../../components/common/PageHeader";

export default function HealthScorePage() {
    const [data, setData] = useState<AIHealthScore | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        aiApi
            .getHealthScore()
            .then(setData)
            .catch((e: Error) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (loading) return <div className="loading-bar" />;
    if (error) return <div className="error-banner">{error}</div>;
    if (!data) return null;

    const scoreColor =
        data.score >= 80 ? "green" :
        data.score >= 60 ? "amber" : "red";

    return (
        <>
            <PageHeader
                title="System Health Score"
                subtitle="AI-calculated infrastructure health"
            />

            <div className="dashboard-section">
                <div className="ai-health-hero">
                    <span className={`ai-health-grade ai-grade-${scoreColor}`}>
                        {data.grade}
                    </span>
                    <span className="ai-health-score-big">
                        {data.score.toFixed(0)}
                    </span>
                    <span className="ai-health-score-label">/ 100</span>
                </div>
            </div>

            <div className="dashboard-section">
                <h3>Health Breakdown</h3>
                {data.breakdown.length > 0 ? (
                    <div className="ai-health-breakdown-full">
                        {data.breakdown.map((item) => (
                            <div
                                key={item.source}
                                className="ai-health-row"
                            >
                                <span className="ai-health-source-name">
                                    {item.source}
                                </span>
                                <div className="ai-health-bar-container">
                                    <div
                                        className={`ai-health-bar ai-health-bar-${item.status}`}
                                        style={{
                                            width: `${item.score}%`,
                                        }}
                                    />
                                </div>
                                <span className="ai-health-score-num">
                                    {item.score.toFixed(0)}
                                </span>
                                <span
                                    className={`ai-health-status-badge ai-health-${item.status}`}
                                >
                                    {item.status}
                                </span>
                                {item.details && (
                                    <span className="ai-health-details">
                                        {item.details}
                                    </span>
                                )}
                            </div>
                        ))}
                    </div>
                ) : (
                    <p className="empty-text">
                        No health breakdown data available
                    </p>
                )}
            </div>

            <div className="dashboard-section">
                <h3>Health Factors</h3>
                <div className="ai-factors-grid">
                    {Object.entries(data.factors).map(([key, value]) => (
                        <div key={key} className="ai-factor-item">
                            <span className="ai-factor-name">{key}</span>
                            <span className="ai-factor-value">
                                {(value as number).toFixed(0)}
                            </span>
                        </div>
                    ))}
                </div>
            </div>
        </>
    );
}
