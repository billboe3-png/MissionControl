import { useEffect, useState } from "react";
import {
    aiApi,
    type AIIncident,
    type AIRisk,
} from "../../services/ai";
import PageHeader from "../../components/common/PageHeader";

export default function IncidentAnalysisPage() {
    const [incidents, setIncidents] = useState<AIIncident[]>([]);
    const [risks, setRisks] = useState<AIRisk[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        aiApi
            .getIncidents()
            .then((data) => {
                setIncidents(data.incidents);
                setRisks(data.top_risks);
            })
            .catch((e: Error) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (loading) return <div className="loading">Loading...</div>;
    if (error) return <div className="error-banner">{error}</div>;

    return (
        <>
            <PageHeader
                title="Incident Analysis"
                subtitle="Classified incidents with priority and reasoning"
            />

            <div className="dashboard-section">
                <h3>Top Risks</h3>
                {risks.length > 0 ? (
                    <div className="ai-risk-list">
                        {risks.map((risk, idx) => (
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
                                <span className="ai-risk-impact">
                                    {risk.business_impact}
                                </span>
                                <span className="ai-risk-message">
                                    {risk.message.substring(0, 100)}
                                </span>
                            </div>
                        ))}
                    </div>
                ) : (
                    <p className="empty-text">No risks detected</p>
                )}
            </div>

            <div className="dashboard-section">
                <h3>Classified Incidents ({incidents.length})</h3>
                {incidents.length > 0 ? (
                    <div className="ai-incident-list">
                        {incidents.map((inc, idx) => (
                            <div
                                key={idx}
                                className={`ai-incident-item ai-risk-${inc.criticality}`}
                            >
                                <div className="ai-incident-header">
                                    <span className="ai-incident-priority">
                                        {inc.priority}
                                    </span>
                                    <span
                                        className={`ai-incident-criticality ai-crit-${inc.criticality}`}
                                    >
                                        {inc.criticality}
                                    </span>
                                    <span className="ai-incident-source">
                                        {inc.source}
                                    </span>
                                    <span className="ai-incident-host">
                                        {inc.host_name}
                                    </span>
                                </div>
                                <div className="ai-incident-message">
                                    {inc.message}
                                </div>
                                <div className="ai-incident-reasoning">
                                    {inc.reasoning}
                                </div>
                                <div className="ai-incident-confidence">
                                    Confidence:{" "}
                                    {(inc.confidence.score * 100).toFixed(0)}%
                                </div>
                                {inc.suggested_actions.length > 0 && (
                                    <div className="ai-incident-actions">
                                        <strong>Suggested actions:</strong>
                                        <ul>
                                            {inc.suggested_actions.map(
                                                (action, aIdx) => (
                                                    <li key={aIdx}>
                                                        {action}
                                                    </li>
                                                )
                                            )}
                                        </ul>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                ) : (
                    <p className="empty-text">
                        No classified incidents
                    </p>
                )}
            </div>
        </>
    );
}
