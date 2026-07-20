import { useEffect, useState } from "react";
import {
    aiApi,
    type AIIncident,
    type AIRisk,
} from "../../services/ai";
import PageHeader from "../../components/common/PageHeader";

const CRIT_CONFIG: Record<string, { color: string; label: string; icon: string }> = {
    critical: { color: "var(--danger)", label: "Critical", icon: "\u{1F534}" },
    high:     { color: "var(--warning)", label: "High",     icon: "\u{1F7E0}" },
    medium:   { color: "var(--primary)", label: "Medium",   icon: "\u{1F535}" },
    low:      { color: "var(--success)", label: "Low",      icon: "\u{1F7E2}" },
};

const SOURCE_LABELS: Record<string, string> = {
    zabbix: "Zabbix",
    hyperv: "Hyper-V",
    proxmox: "Proxmox",
    ad: "Active Directory",
    m365: "Microsoft 365",
    docker: "Docker",
    nginx: "Nginx",
    linux: "Linux",
    windows: "Windows",
};

function ConfidenceBar({ score }: { score: number }) {
    const pct = Math.round(score * 100);
    let color = "var(--success)";
    if (pct < 50) color = "var(--danger)";
    else if (pct < 75) color = "var(--warning)";

    return (
        <div className="ai-rec-confidence-bar">
            <div className="ai-rec-confidence-track">
                <div
                    className="ai-rec-confidence-fill"
                    style={{ width: `${pct}%`, background: color }}
                />
            </div>
            <span className="ai-rec-confidence-text">{pct}%</span>
        </div>
    );
}

function IncidentCard({ inc }: { inc: AIIncident }) {
    const crit = CRIT_CONFIG[inc.criticality] ?? CRIT_CONFIG.medium;

    return (
        <div className="ai-rec-card" style={{ borderTopColor: crit.color }}>
            <div className="ai-rec-card-header">
                <div className="ai-rec-card-title">
                    <span className="ai-rec-card-icon">{crit.icon}</span>
                    <span>{inc.message}</span>
                </div>
                <div className="ai-rec-card-badges">
                    <span
                        className="ai-rec-badge"
                        style={{ background: crit.color + "22", color: crit.color, borderColor: crit.color }}
                    >
                        {crit.label}
                    </span>
                    <span className="ai-rec-badge ai-rec-badge-category">
                        {inc.priority}
                    </span>
                    <span className="ai-rec-badge ai-rec-badge-category">
                        {SOURCE_LABELS[inc.source] ?? inc.source}
                    </span>
                </div>
            </div>

            <div className="ai-rec-card-body">
                <div className="ai-rec-card-row ai-rec-card-row-host">
                    <span className="ai-rec-card-label">Host</span>
                    <span className="ai-rec-card-host">
                        <span className="ai-rec-host-icon">&#128421;</span>
                        {inc.host_name}
                        <span className="ai-rec-host-source">
                            ({SOURCE_LABELS[inc.source] ?? inc.source})
                        </span>
                    </span>
                </div>

                <div className="ai-rec-card-row">
                    <span className="ai-rec-card-label">Confidence</span>
                    <div className="ai-rec-card-value-row">
                        <ConfidenceBar score={inc.confidence.score} />
                        <span className="ai-rec-conf-level">({inc.confidence.level})</span>
                    </div>
                </div>

                <div className="ai-rec-card-row">
                    <span className="ai-rec-card-label">Reason</span>
                    <span className="ai-rec-card-text">{inc.reasoning}</span>
                </div>

                <div className="ai-rec-card-row">
                    <span className="ai-rec-card-label">Impact</span>
                    <span className="ai-rec-card-text">{inc.business_impact}</span>
                </div>

                {inc.suggested_actions.length > 0 && (
                    <div className="ai-rec-card-row">
                        <span className="ai-rec-card-label">Actions</span>
                        <ul className="ai-incident-actions-list">
                            {inc.suggested_actions.map((action, aIdx) => (
                                <li key={aIdx} className="ai-incident-action-item">
                                    {action}
                                </li>
                            ))}
                        </ul>
                    </div>
                )}
            </div>
        </div>
    );
}

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

    if (loading) return <div className="loading-bar" />;
    if (error) return <div className="error-banner">{error}</div>;

    const critCount = incidents.filter((i) => i.criticality === "critical").length;
    const highCount = incidents.filter((i) => i.criticality === "high").length;
    const medCount = incidents.filter((i) => i.criticality === "medium").length;
    const lowCount = incidents.filter((i) => i.criticality === "low").length;

    return (
        <>
            <PageHeader
                title="Incident Analysis"
                subtitle="Classified incidents with priority and reasoning"
            />

            <div className="dashboard-stats">
                <div className="stat-card stat-card-gray">
                    <span className="stat-card-icon">&#9888;</span>
                    <div className="stat-card-body">
                        <span className="stat-card-value">{incidents.length}</span>
                        <span className="stat-card-label">Total</span>
                    </div>
                </div>
                <div className="stat-card stat-card-red">
                    <span className="stat-card-icon">&#128308;</span>
                    <div className="stat-card-body">
                        <span className="stat-card-value">{critCount}</span>
                        <span className="stat-card-label">Critical</span>
                    </div>
                </div>
                <div className="stat-card stat-card-amber">
                    <span className="stat-card-icon">&#128992;</span>
                    <div className="stat-card-body">
                        <span className="stat-card-value">{highCount + medCount}</span>
                        <span className="stat-card-label">High/Med</span>
                    </div>
                </div>
                <div className="stat-card stat-card-green">
                    <span className="stat-card-icon">&#128994;</span>
                    <div className="stat-card-body">
                        <span className="stat-card-value">{lowCount}</span>
                        <span className="stat-card-label">Low</span>
                    </div>
                </div>
            </div>

            {risks.length > 0 && (
                <div className="dashboard-section">
                    <h3>Top Risks</h3>
                    <div className="ai-rec-grid">
                        {risks.map((risk, idx) => {
                            const rc = CRIT_CONFIG[risk.criticality] ?? CRIT_CONFIG.medium;
                            return (
                                <div key={idx} className="ai-rec-card" style={{ borderTopColor: rc.color }}>
                                    <div className="ai-rec-card-header">
                                        <div className="ai-rec-card-title">
                                            <span className="ai-rec-card-icon">{rc.icon}</span>
                                            <span>{risk.message}</span>
                                        </div>
                                        <div className="ai-rec-card-badges">
                                            <span
                                                className="ai-rec-badge"
                                                style={{ background: rc.color + "22", color: rc.color, borderColor: rc.color }}
                                            >
                                                {rc.label}
                                            </span>
                                        </div>
                                    </div>
                                    <div className="ai-rec-card-body">
                                        <div className="ai-rec-card-row ai-rec-card-row-host">
                                            <span className="ai-rec-card-label">Host</span>
                                            <span className="ai-rec-card-host">
                                                <span className="ai-rec-host-icon">&#128421;</span>
                                                {risk.host_name}
                                                <span className="ai-rec-host-source">
                                                    ({SOURCE_LABELS[risk.source] ?? risk.source})
                                                </span>
                                            </span>
                                        </div>
                                        <div className="ai-rec-card-row">
                                            <span className="ai-rec-card-label">Impact</span>
                                            <span className="ai-rec-card-text">{risk.business_impact}</span>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            <div className="dashboard-section">
                <h3>Classified Incidents ({incidents.length})</h3>
                {incidents.length > 0 ? (
                    <div className="ai-rec-grid">
                        {incidents.map((inc, idx) => (
                            <IncidentCard key={idx} inc={inc} />
                        ))}
                    </div>
                ) : (
                    <p className="empty-text">No classified incidents</p>
                )}
            </div>
        </>
    );
}
