import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import { api } from "../../services/api";
import { DashboardResponse } from "../../types/dashboard";

export default function OverviewPage() {
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

    const infraCards = [
        {
            label: "Projects",
            count: data.projects.count,
            path: "/infrastructure/system",
            status: data.projects.count > 0 ? ("healthy" as const) : ("neutral" as const),
        },
        {
            label: "Tasks",
            count: data.tasks.count,
            path: "/infrastructure/system",
            status: data.tasks.statistics.blocked > 0
                ? ("warning" as const)
                : data.tasks.count > 0
                  ? ("healthy" as const)
                  : ("neutral" as const),
        },
        {
            label: "Docker Containers",
            count: data.docker.container_count,
            path: "/infrastructure/docker",
            status: data.docker.stopped > 0
                ? ("warning" as const)
                : data.docker.container_count > 0
                  ? ("healthy" as const)
                  : ("neutral" as const),
        },
        {
            label: "Git",
            count: data.git.repository_name ? 1 : 0,
            path: "/infrastructure/git",
            status: data.git.working_tree_clean ? ("healthy" as const) : ("warning" as const),
        },
        {
            label: "Parking Lot Items",
            count: data.parking_lot.count,
            path: "/infrastructure/system",
            status: data.parking_lot.count > 0 ? ("info" as const) : ("neutral" as const),
        },
    ];

    return (
        <>
            <PageHeader
                title="Infrastructure Overview"
                subtitle="Summary of all managed systems"
            />
            <div className="infra-overview-grid">
                {infraCards.map((card) => (
                    <Link key={card.label} to={card.path} className="infra-overview-card">
                        <div className="infra-card-header">
                            <span className="infra-card-label">{card.label}</span>
                            <StatusBadge status={card.status} label={String(card.count)} />
                        </div>
                    </Link>
                ))}
            </div>
        </>
    );
}
