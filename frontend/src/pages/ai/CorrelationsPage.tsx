import { useEffect, useState } from "react";
import {
    aiApi,
    type AICorrelationResult,
} from "../../services/ai";
import PageHeader from "../../components/common/PageHeader";

export default function CorrelationsPage() {
    const [data, setData] = useState<AICorrelationResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        aiApi
            .getCorrelations()
            .then(setData)
            .catch((e: Error) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (loading) return <div className="loading-bar" />;
    if (error) return <div className="error-banner">{error}</div>;
    if (!data) return null;

    const s = data.summary;

    return (
        <>
            <PageHeader
                title="Alert Correlations"
                subtitle="Cross-source incident correlation"
            />
            <div className="dashboard-stats">
                <div className="stat-card stat-card-gray">
                    <span className="stat-card-icon">📊</span>
                    <div className="stat-card-body">
                        <span className="stat-card-value">
                            {s.total_alerts}
                        </span>
                        <span className="stat-card-label">Total Alerts</span>
                    </div>
                </div>
                <div className="stat-card stat-card-amber">
                    <span className="stat-card-icon">🔗</span>
                    <div className="stat-card-body">
                        <span className="stat-card-value">
                            {s.total_groups}
                        </span>
                        <span className="stat-card-label">Groups</span>
                    </div>
                </div>
                <div className="stat-card stat-card-green">
                    <span className="stat-card-icon">📋</span>
                    <div className="stat-card-body">
                        <span className="stat-card-value">
                            {s.total_duplicates}
                        </span>
                        <span className="stat-card-label">Duplicates</span>
                    </div>
                </div>
                <div className="stat-card stat-card-red">
                    <span className="stat-card-icon">🌊</span>
                    <div className="stat-card-body">
                        <span className="stat-card-value">
                            {s.total_cascading}
                        </span>
                        <span className="stat-card-label">Cascading</span>
                    </div>
                </div>
            </div>

            <div className="dashboard-row">
                <div className="dashboard-section">
                    <h3>Correlated Groups</h3>
                    {data.groups.length > 0 ? (
                        <div className="ai-corr-list">
                            {data.groups.map((grp) => (
                                <div
                                    key={grp.group_id}
                                    className={`ai-corr-item ai-risk-${grp.max_severity}`}
                                >
                                    <div className="ai-corr-header">
                                        <span className="ai-corr-id">
                                            {grp.group_id}
                                        </span>
                                        <span className="ai-corr-host">
                                            {grp.host_name}
                                        </span>
                                        <span className="ai-corr-count">
                                            {grp.alert_count} alerts
                                        </span>
                                        <span className="ai-corr-type">
                                            {grp.correlation_type}
                                        </span>
                                    </div>
                                    <div className="ai-corr-sources">
                                        Sources:{" "}
                                        {grp.sources.join(", ")}
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="empty-text">
                            No correlated groups
                        </p>
                    )}
                </div>

                <div className="dashboard-section">
                    <h3>Severity Distribution</h3>
                    {Object.keys(s.severity_distribution).length > 0 ? (
                        <div className="ai-severity-dist">
                            {Object.entries(s.severity_distribution).map(
                                ([sev, count]) => (
                                    <div
                                        key={sev}
                                        className="ai-severity-item"
                                    >
                                        <span className="ai-severity-label">
                                            {sev}
                                        </span>
                                        <span className="ai-severity-count">
                                            {count}
                                        </span>
                                    </div>
                                )
                            )}
                        </div>
                    ) : (
                        <p className="empty-text">
                            No severity data
                        </p>
                    )}

                    <h3>Sources</h3>
                    <div className="ai-source-list">
                        {s.sources.map((src) => (
                            <span key={src} className="ai-source-badge">
                                {src}
                            </span>
                        ))}
                    </div>
                </div>
            </div>
        </>
    );
}
