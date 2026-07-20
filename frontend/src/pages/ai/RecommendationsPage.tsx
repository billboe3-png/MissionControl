import { useCallback, useEffect, useState } from "react";
import {
    aiApi,
    type AIRecommendation,
} from "../../services/ai";
import PageHeader from "../../components/common/PageHeader";
import { useToast } from "../../contexts/ToastContext";

const RISK_CONFIG: Record<string, { color: string; label: string; icon: string }> = {
    critical: { color: "var(--danger)", label: "Critical", icon: "\u{1F534}" },
    high:     { color: "var(--warning)", label: "High",     icon: "\u{1F7E0}" },
    medium:   { color: "var(--primary)", label: "Medium",   icon: "\u{1F535}" },
    low:      { color: "var(--success)", label: "Low",      icon: "\u{1F7E2}" },
};

const CATEGORY_LABELS: Record<string, string> = {
    remediation: "Remediation",
    diagnostic: "Diagnostic",
    optimization: "Optimization",
    security: "Security",
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

function RecommendationCard({
    rec,
    onApprove,
    onReject,
}: {
    rec: AIRecommendation;
    onApprove: (id: string) => void;
    onReject: (id: string) => void;
}) {
    const risk = RISK_CONFIG[rec.risk] ?? RISK_CONFIG.medium;
    const confLevel = rec.confidence.level;
    const isResolved = rec.status === "approved" || rec.status === "rejected";

    return (
        <div className={`ai-rec-card ${isResolved ? "ai-rec-card-resolved" : ""}`} style={{ borderTopColor: risk.color }}>
            <div className="ai-rec-card-header">
                <div className="ai-rec-card-title">
                    <span className="ai-rec-card-icon">{risk.icon}</span>
                    <span>{rec.action}</span>
                </div>
                <div className="ai-rec-card-badges">
                    <span
                        className="ai-rec-badge"
                        style={{ background: risk.color + "22", color: risk.color, borderColor: risk.color }}
                    >
                        {risk.label}
                    </span>
                    <span className="ai-rec-badge ai-rec-badge-category">
                        {CATEGORY_LABELS[rec.category] ?? rec.category}
                    </span>
                    {rec.status === "approved" && (
                        <span className="ai-rec-badge ai-rec-badge-approved">Approved</span>
                    )}
                    {rec.status === "rejected" && (
                        <span className="ai-rec-badge ai-rec-badge-rejected">Rejected</span>
                    )}
                </div>
            </div>

            <div className="ai-rec-card-body">
                <div className="ai-rec-card-row ai-rec-card-row-host">
                    <span className="ai-rec-card-label">Host</span>
                    <span className="ai-rec-card-host">
                        <span className="ai-rec-host-icon">&#128421;</span>
                        {rec.host_name}
                        <span className="ai-rec-host-source">
                            ({SOURCE_LABELS[rec.source] ?? rec.source})
                        </span>
                    </span>
                </div>

                <div className="ai-rec-card-row">
                    <span className="ai-rec-card-label">Confidence</span>
                    <div className="ai-rec-card-value-row">
                        <ConfidenceBar score={rec.confidence.score} />
                        <span className="ai-rec-conf-level">({confLevel})</span>
                    </div>
                </div>

                <div className="ai-rec-card-row">
                    <span className="ai-rec-card-label">Reason</span>
                    <span className="ai-rec-card-text">{rec.explanation}</span>
                </div>

                <div className="ai-rec-card-row">
                    <span className="ai-rec-card-label">Impact</span>
                    <span className="ai-rec-card-text">{rec.estimated_impact}</span>
                </div>
            </div>

            <div className="ai-rec-card-footer">
                {rec.requires_approval && !isResolved && (
                    <div className="ai-rec-card-actions">
                        <span className="ai-rec-approval-hint">
                            <span className="ai-rec-approval-icon">&#128274;</span>
                            Requires approval
                        </span>
                        <div className="ai-rec-action-buttons">
                            <button
                                className="btn btn-sm ai-rec-btn-approve"
                                onClick={() => onApprove(rec.id)}
                            >
                                &#10003; Approve
                            </button>
                            <button
                                className="btn btn-sm ai-rec-btn-reject"
                                onClick={() => onReject(rec.id)}
                            >
                                &#10007; Reject
                            </button>
                        </div>
                    </div>
                )}
                {isResolved && (
                    <span className="ai-rec-resolved-text">
                        {rec.status === "approved" ? "Approved" : "Rejected"}
                    </span>
                )}
            </div>
        </div>
    );
}

export default function RecommendationsPage() {
    const { showToast } = useToast();
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

    const handleApprove = useCallback(async (id: string) => {
        try {
            await aiApi.approveRecommendation(id);
            setRecs((prev) =>
                prev.map((r) => (r.id === id ? { ...r, status: "approved" as const } : r))
            );
            showToast("Recommendation approved", undefined);
        } catch (e: unknown) {
            const msg = e instanceof Error ? e.message : "Approval failed";
            showToast(msg, "error");
        }
    }, [showToast]);

    const handleReject = useCallback(async (id: string) => {
        try {
            await aiApi.rejectRecommendation(id);
            setRecs((prev) =>
                prev.map((r) => (r.id === id ? { ...r, status: "rejected" as const } : r))
            );
            showToast("Recommendation rejected", undefined);
        } catch (e: unknown) {
            const msg = e instanceof Error ? e.message : "Rejection failed";
            showToast(msg, "error");
        }
    }, [showToast]);

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
                    <span className="stat-card-icon">&#128161;</span>
                    <div className="stat-card-body">
                        <span className="stat-card-value">{recs.length}</span>
                        <span className="stat-card-label">Total</span>
                    </div>
                </div>
                <div className="stat-card stat-card-red">
                    <span className="stat-card-icon">&#128308;</span>
                    <div className="stat-card-body">
                        <span className="stat-card-value">
                            {byRisk.critical ?? 0}
                        </span>
                        <span className="stat-card-label">Critical</span>
                    </div>
                </div>
                <div className="stat-card stat-card-amber">
                    <span className="stat-card-icon">&#128992;</span>
                    <div className="stat-card-body">
                        <span className="stat-card-value">
                            {byRisk.high ?? 0}
                        </span>
                        <span className="stat-card-label">High</span>
                    </div>
                </div>
                <div className="stat-card stat-card-green">
                    <span className="stat-card-icon">&#128994;</span>
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
                    <div className="ai-rec-grid">
                        {recs.map((rec) => (
                            <RecommendationCard
                                key={rec.id}
                                rec={rec}
                                onApprove={handleApprove}
                                onReject={handleReject}
                            />
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
