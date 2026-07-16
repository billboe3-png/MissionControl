import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import { api } from "../../services/api";
import { DashboardResponse } from "../../types/dashboard";

export default function DockerPage() {
    const [data, setData] = useState<DashboardResponse | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        api
            .getDashboard()
            .then(setData)
            .catch((e) => setError(e.message));
    }, []);

    if (error) return <div className="error-banner">{error}</div>;
    if (!data) return <div className="loading-bar" />;

    const { docker } = data;

    return (
        <>
            <PageHeader
                title="Docker"
                subtitle="Container status and overview"
            />
            <div className="docker-stats">
                <div className="docker-stat">
                    <span className="docker-stat-label">Total</span>
                    <span className="docker-stat-value">{docker.container_count}</span>
                </div>
                <div className="docker-stat">
                    <span className="docker-stat-label">Running</span>
                    <StatusBadge status="healthy" label={String(docker.running)} />
                </div>
                <div className="docker-stat">
                    <span className="docker-stat-label">Stopped</span>
                    <StatusBadge
                        status={docker.stopped > 0 ? "warning" : "neutral"}
                        label={String(docker.stopped)}
                    />
                </div>
            </div>
            {docker.containers.length > 0 && (
                <div className="docker-container-list">
                    <h3>Containers</h3>
                    <ul>
                        {docker.containers.map((c) => (
                            <li key={c.id} className="docker-container-item">
                                <span className="docker-container-name">{c.name}</span>
                                <StatusBadge
                                    status={c.state === "running" ? "healthy" : "error"}
                                    label={c.state}
                                />
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </>
    );
}
