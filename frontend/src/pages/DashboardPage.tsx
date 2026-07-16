import { useEffect, useState } from "react";
import { api } from "../services/api";
import { DashboardResponse } from "../types/dashboard";
import StatCard from "../components/dashboard/StatCard";
import HealthBadges from "../components/dashboard/HealthBadges";
import QuickActions from "../components/dashboard/QuickActions";
import IntegrationsCard from "../components/dashboard/IntegrationsCard";
import HyperVCard from "../components/dashboard/HyperVCard";
import AICard from "../components/dashboard/AICard";
import AgentCard from "../components/dashboard/AgentCard";
import AutomationCard from "../components/dashboard/AutomationCard";
import PageHeader from "../components/common/PageHeader";

export default function DashboardPage() {
    const [data, setData] = useState<DashboardResponse | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        api
            .getDashboard()
            .then(setData)
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (loading) return <div className="loading-bar" />;
    if (error) return <div className="error-banner">{error}</div>;
    if (!data) return null;

    const healthItems = [
        {
            label: "Docker",
            status: data.docker.running > 0 ? ("healthy" as const) : ("neutral" as const),
        },
        {
            label: "Git",
            status: data.git.working_tree_clean ? ("healthy" as const) : ("warning" as const),
        },
        {
            label: "Tasks",
            status: data.tasks.count > 0 ? ("healthy" as const) : ("neutral" as const),
        },
    ];

    return (
        <>
            <PageHeader title="Dashboard" subtitle="Infrastructure at a glance" />
            <div className="dashboard-stats">
                <StatCard
                    label="Projects"
                    value={data.projects.count}
                    icon="📁"
                    to="/infrastructure/system"
                    status={data.projects.count > 0 ? "green" : "gray"}
                />
                <StatCard
                    label="Tasks"
                    value={data.tasks.count}
                    icon="✅"
                    to="/infrastructure/system"
                    status={data.tasks.statistics.blocked > 0 ? "amber" : "green"}
                />
                <StatCard
                    label="Containers"
                    value={data.docker.container_count}
                    icon="🐳"
                    to="/infrastructure/docker"
                    status={data.docker.stopped > 0 ? "amber" : "green"}
                />
                <StatCard
                    label="Git Repos"
                    value={data.git.repository_name ? 1 : 0}
                    icon="📦"
                    to="/infrastructure/git"
                    status={data.git.working_tree_clean ? "green" : "amber"}
                />
                <StatCard
                    label="Parking Lot"
                    value={data.parking_lot.count}
                    icon="📋"
                    status={data.parking_lot.count > 0 ? "amber" : "gray"}
                />
            </div>
            <div className="dashboard-row">
                <div className="dashboard-section">
                    <h3>System Health</h3>
                    <HealthBadges items={healthItems} />
                </div>
                <div className="dashboard-section">
                    <h3>Quick Actions</h3>
                    <QuickActions />
                </div>
                {data.integrations?.profiles && (
                    <IntegrationsCard items={data.integrations.profiles.items} />
                )}
                <HyperVCard />
                {data.agents && <AgentCard data={data.agents} />}
                {data.automation && <AutomationCard data={data.automation} />}
                {data.ai && <AICard data={data.ai} />}
            </div>
        </>
    );
}
