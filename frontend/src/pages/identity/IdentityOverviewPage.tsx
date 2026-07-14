import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import { identityApi, IdentityOverview } from "../../services/identity";

export default function IdentityOverviewPage() {
    const [data, setData] = useState<IdentityOverview | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        identityApi
            .getOverview()
            .then(setData)
            .catch((e) => setError(e.message));
    }, []);

    if (error) return <div className="error-banner">{error}</div>;
    if (!data) return <div className="loading">Loading…</div>;

    const adCards = [
        { label: "Domain Controllers", count: data.ad_domain_controllers, path: "/identity/active-directory", status: data.ad_domain_controllers > 0 ? ("healthy" as const) : ("neutral" as const) },
        { label: "Users", count: data.ad_users_total, path: "/identity/active-directory", status: data.ad_users_total > 0 ? ("healthy" as const) : ("neutral" as const) },
        { label: "Computers", count: data.ad_computers_total, path: "/identity/active-directory", status: data.ad_computers_total > 0 ? ("healthy" as const) : ("neutral" as const) },
        { label: "Groups", count: data.ad_groups_total, path: "/identity/active-directory", status: data.ad_groups_total > 0 ? ("healthy" as const) : ("neutral" as const) },
        { label: "GPOs", count: data.ad_gpos_total, path: "/identity/active-directory", status: data.ad_gpos_total > 0 ? ("info" as const) : ("neutral" as const) },
    ];

    const m365Cards = [
        { label: "Total Users", count: data.m365_total_users, path: "/identity/microsoft-365", status: data.m365_total_users > 0 ? ("healthy" as const) : ("neutral" as const) },
        { label: "Licensed Users", count: data.m365_licensed_users, path: "/identity/microsoft-365", status: data.m365_licensed_users > 0 ? ("healthy" as const) : ("neutral" as const) },
        { label: "Service Status", count: 0, path: "/identity/microsoft-365", status: data.m365_overall_status === "healthy" ? ("healthy" as const) : data.m365_overall_status === "degraded" ? ("warning" as const) : ("neutral" as const) },
        { label: "Active Incidents", count: data.m365_active_incidents, path: "/identity/microsoft-365", status: data.m365_active_incidents > 0 ? ("warning" as const) : ("healthy" as const) },
        { label: "Secure Score", count: Math.round(data.m365_secure_score), path: "/identity/microsoft-365", status: data.m365_secure_score >= 70 ? ("healthy" as const) : data.m365_secure_score >= 50 ? ("warning" as const) : ("error" as const) },
    ];

    return (
        <>
            <PageHeader
                title="Identity & Access"
                subtitle="Active Directory and Microsoft 365 overview"
            />
            <div className="identity-overview-section">
                <h3>Active Directory</h3>
                <div className="infra-overview-grid">
                    {adCards.map((card) => (
                        <Link key={card.label} to={card.path} className="infra-overview-card">
                            <div className="infra-card-header">
                                <span className="infra-card-label">{card.label}</span>
                                <StatusBadge status={card.status} label={String(card.count)} />
                            </div>
                        </Link>
                    ))}
                </div>
            </div>
            <div className="identity-overview-section">
                <h3>Microsoft 365</h3>
                <div className="infra-overview-grid">
                    {m365Cards.map((card) => (
                        <Link key={card.label} to={card.path} className="infra-overview-card">
                            <div className="infra-card-header">
                                <span className="infra-card-label">{card.label}</span>
                                <StatusBadge
                                    status={card.status}
                                    label={card.label === "Service Status" ? data.m365_overall_status : card.label === "Secure Score" ? `${data.m365_secure_score}%` : String(card.count)}
                                />
                            </div>
                        </Link>
                    ))}
                </div>
            </div>
        </>
    );
}
