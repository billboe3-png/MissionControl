import { useEffect, useState } from "react";
import {
    aiApi,
    type AIRecommendation,
} from "../../services/ai";
import PageHeader from "../../components/common/PageHeader";

export default function RecommendationsPage() {
    const [recs, setRecs] = useState<AIRecommendation[]>([]);
    const [byRisk, setByRisk] = useState<Record<string, number>>({});
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        aiApi
            .getRecommendations()
            .then((data) => {
                setRecs(data.recommendations);
                setByRisk(data.by_risk);
            })
            .catch((e: Error) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (loading) return <div className="loading-bar" />;
    if (error) return <div className="error-banner">{error}</div>;

    return (
        <>
            <PageHeader
                title="AI Recommendations"
                subtitle="Actionable insights with confidence scores"
            />
            <div className="dashboard-stats">
                <div className="stat-card stat-card-gray">
                    <span className="stat-card-icon">💡</span>
                    <div className="stat-card-body">
                        <span className="stat-card-value">{recs.length}</span>
                        <span className="stat-card-label">Total</span>
                    </div>
                </div>
                <div className="stat-card stat-card-red">
                    <span className="stat-card-icon">🔴</span>
                    <div className="stat-card-body">
                        <span className="stat-card-value">
                            {byRisk.critical ?? 0}
                        </span>
                        <span className="stat-card-label">Critical</span>
                    </div>
                </div>
                <div className="stat-card stat-card-amber">
                    <span className="stat-card-icon">🟠</span>
                    <div className="stat-card-body">
                        <span className="stat-card-value">
                            {byRisk.high ?? 0}
                        </span>
                        <span className="stat-card-label">High</span>
                    </div>
                </div>
                <div className="stat-card stat-card-green">
                    <span className="stat-card-icon">🟢</span>
                    <div className="stat-card-body">
                        <span className="stat-card-value">
                            {byRisk.low ?? 0}
                        </span>
                        <span className="stat-card-label">Low</span>
                    </div>
                </div>
            </div>

            <div className="dashboard-section">
                <h3>Recommendations</h3>
                {recs.length > 0 ? (
                    <div className="ai-rec-list">
                        {recs.map((rec) => (
                            <div
                                key={rec.id}
                                className={`ai-rec-item ai-risk-${rec.risk}`}
                            >
                                <div className="ai-rec-header">
                                    <span className="ai-rec-action">
                                        {rec.action}
                                    </span>
                                    <span
                                        className={`ai-rec-risk ai-risk-badge-${rec.risk}`}
                                    >
                                        {rec.risk}
                                    </span>
                                    <span className="ai-rec-category">
                                        {rec.category}
                                    </span>
                                </div>
                                <div className="ai-rec-confidence">
                                    Confidence:{" "}
                                    {(rec.confidence.score * 100).toFixed(0)}%
                                    ({rec.confidence.level})
                                </div>
                                <div className="ai-rec-explanation">
                                    {rec.explanation}
                                </div>
                                <div className="ai-rec-impact">
                                    Impact: {rec.estimated_impact}
                                </div>
                                <div className="ai-rec-approval">
                                    Requires human approval
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <p className="empty-text">
                        No recommendations at this time
                    </p>
                )}
            </div>
        </>
    );
}
