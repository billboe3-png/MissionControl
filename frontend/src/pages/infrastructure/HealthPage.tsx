import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import { api } from "../../services/api";
import { DashboardResponse } from "../../types/dashboard";

export default function HealthPage() {
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

    const checks = [
        {
            label: "Backend",
            status: data.health.backend.status === "healthy" ? ("healthy" as const) : ("error" as const),
        },
        {
            label: "Database",
            status: data.health.database.status === "healthy" ? ("healthy" as const) : ("error" as const),
        },
        {
            label: "Redis",
            status: data.health.redis.status === "healthy"
                ? ("healthy" as const)
                : data.health.redis.status === "unavailable"
                  ? ("neutral" as const)
                  : ("error" as const),
        },
        {
            label: "Docker",
            status: data.docker.container_count > 0 ? ("healthy" as const) : ("neutral" as const),
        },
        {
            label: "Git",
            status: gitStatus(data),
        },
        {
            label: "Projects",
            status: data.projects.count > 0 ? ("healthy" as const) : ("neutral" as const),
        },
        {
            label: "Resume",
            status: data.resume.available ? ("info" as const) : ("neutral" as const),
        },
    ];

    return (
        <>
            <PageHeader
                title="Health"
                subtitle="System health checks"
            />
            <div className="health-checks">
                {checks.map((check) => (
                    <div key={check.label} className="health-check-item">
                        <span className="health-check-label">{check.label}</span>
                        <StatusBadge
                            status={check.status}
                            label={check.status}
                        />
                    </div>
                ))}
            </div>
        </>
    );
}

function gitStatus(data: DashboardResponse): "healthy" | "warning" | "neutral" {
    if (!data.git.available) return "neutral";
    return data.git.working_tree_clean ? "healthy" : "warning";
}
