import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import { veeamApi, VeeamHealth } from "../../services/veeam";

export default function VeeamHealthPage() {
    const [health, setHealth] = useState<VeeamHealth | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        veeamApi
            .getHealth()
            .then(setHealth)
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (loading) return <div className="loading-bar" />;
    if (error) return <div className="error-banner">{error}</div>;
    if (!health) return null;

    return (
        <>
            <PageHeader title="Veeam Health" subtitle="Veeam B&amp;R server health status" />
            <div className="health-card">
                <div className="health-card-row">
                    <StatusBadge
                        status={health.healthy ? "healthy" : "error"}
                        label={health.healthy ? "Healthy" : "Error"}
                    />
                    <span className="health-status-label">
                        {health.healthy ? "Server is healthy" : "Server is unreachable"}
                    </span>
                </div>
                <div className="health-card-details">
                    <div className="health-detail">
                        <span className="health-detail-label">Name</span>
                        <span className="health-detail-value">{health.name ?? "-"}</span>
                    </div>
                    <div className="health-detail">
                        <span className="health-detail-label">Version</span>
                        <span className="health-detail-value">{health.version ?? "-"}</span>
                    </div>
                    {health.error && (
                        <div className="health-detail">
                            <span className="health-detail-label">Error</span>
                            <span className="health-detail-value error">{health.error}</span>
                        </div>
                    )}
                </div>
            </div>
        </>
    );
}
