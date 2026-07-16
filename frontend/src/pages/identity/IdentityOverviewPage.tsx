import { useEffect, useState } from "react";
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
    if (!data) return <div className="loading-bar" />;

    const ad = data.overview.ad;
    const m365 = data.overview.m365;

    return (
        <>
            <PageHeader
                title="Identity & Access"
                subtitle="Active Directory and Microsoft 365 overview"
            />
            <div className="identity-overview-section">
                <h3>Active Directory</h3>
                <div className="infra-overview-grid">
                    <div className="infra-overview-card">
                        <div className="infra-card-header">
                            <span className="infra-card-label">Status</span>
                            <StatusBadge
                                status={ad.connected ? "healthy" : "error"}
                                label={ad.connected ? "Connected" : "Disconnected"}
                            />
                        </div>
                    </div>
                    <div className="infra-overview-card">
                        <div className="infra-card-header">
                            <span className="infra-card-label">Domain</span>
                            <StatusBadge status="info" label={ad.domain} />
                        </div>
                    </div>
                    <div className="infra-overview-card">
                        <div className="infra-card-header">
                            <span className="infra-card-label">Users</span>
                            <StatusBadge
                                status={ad.user_count > 0 ? "healthy" : "neutral"}
                                label={String(ad.user_count)}
                            />
                        </div>
                    </div>
                    <div className="infra-overview-card">
                        <div className="infra-card-header">
                            <span className="infra-card-label">Groups</span>
                            <StatusBadge
                                status={ad.group_count > 0 ? "healthy" : "neutral"}
                                label={String(ad.group_count)}
                            />
                        </div>
                    </div>
                    <div className="infra-overview-card">
                        <div className="infra-card-header">
                            <span className="infra-card-label">Computers</span>
                            <StatusBadge
                                status={ad.computer_count > 0 ? "healthy" : "neutral"}
                                label={String(ad.computer_count)}
                            />
                        </div>
                    </div>
                    <div className="infra-overview-card">
                        <div className="infra-card-header">
                            <span className="infra-card-label">Health</span>
                            <StatusBadge
                                status={ad.health === "healthy" ? "healthy" : ad.health === "degraded" ? "warning" : "neutral"}
                                label={ad.health}
                            />
                        </div>
                    </div>
                </div>
            </div>
            <div className="identity-overview-section">
                <h3>Microsoft 365</h3>
                <div className="infra-overview-grid">
                    <div className="infra-overview-card">
                        <div className="infra-card-header">
                            <span className="infra-card-label">Status</span>
                            <StatusBadge
                                status={m365.connected ? "healthy" : "error"}
                                label={m365.connected ? "Connected" : "Disconnected"}
                            />
                        </div>
                    </div>
                    <div className="infra-overview-card">
                        <div className="infra-card-header">
                            <span className="infra-card-label">Tenant</span>
                            <StatusBadge status="info" label={m365.tenant} />
                        </div>
                    </div>
                    <div className="infra-overview-card">
                        <div className="infra-card-header">
                            <span className="infra-card-label">Licensed Users</span>
                            <StatusBadge
                                status={m365.licensed_users > 0 ? "healthy" : "neutral"}
                                label={String(m365.licensed_users)}
                            />
                        </div>
                    </div>
                    <div className="infra-overview-card">
                        <div className="infra-card-header">
                            <span className="infra-card-label">Licenses</span>
                            <StatusBadge
                                status="info"
                                label={String(m365.license_count)}
                            />
                        </div>
                    </div>
                    <div className="infra-overview-card">
                        <div className="infra-card-header">
                            <span className="infra-card-label">Service Health</span>
                            <StatusBadge
                                status={m365.health === "healthy" ? "healthy" : m365.health === "degraded" ? "warning" : "neutral"}
                                label={m365.health}
                            />
                        </div>
                    </div>
                    <div className="infra-overview-card">
                        <div className="infra-card-header">
                            <span className="infra-card-label">Active Incidents</span>
                            <StatusBadge
                                status={m365.active_incidents > 0 ? "warning" : "healthy"}
                                label={String(m365.active_incidents)}
                            />
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
}
