import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import DataTable, { Column } from "../../components/common/DataTable";
import { identityApi, Microsoft365Tenant, LicenseSummary, ServiceHealth, EntraHealth, ExchangeHealth, SecureScore, MessageCenterItem } from "../../services/identity";

type M365Tab = "overview" | "licenses" | "services" | "entra" | "exchange" | "secure-score" | "messages";

export default function Microsoft365Page() {
    const [tab, setTab] = useState<M365Tab>("overview");
    const [tenant, setTenant] = useState<Microsoft365Tenant | null>(null);
    const [licenses, setLicenses] = useState<LicenseSummary[]>([]);
    const [serviceHealth, setServiceHealth] = useState<ServiceHealth | null>(null);
    const [entra, setEntra] = useState<EntraHealth | null>(null);
    const [exchange, setExchange] = useState<ExchangeHealth | null>(null);
    const [score, setScore] = useState<SecureScore | null>(null);
    const [messages, setMessages] = useState<MessageCenterItem[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        Promise.all([
            identityApi.getTenant(),
            identityApi.getLicenses(),
            identityApi.getServiceHealth(),
            identityApi.getEntraHealth(),
            identityApi.getExchangeHealth(),
            identityApi.getSecureScore(),
            identityApi.getMessageCenter(),
        ])
            .then(([tenantRes, licRes, svcRes, entRes, exRes, scoreRes, msgRes]) => {
                setTenant(tenantRes.tenant);
                setLicenses(licRes.licenses);
                setServiceHealth(svcRes.service_health);
                setEntra(entRes.entra_health);
                setExchange(exRes.exchange_health);
                setScore(scoreRes.secure_score);
                setMessages(msgRes.items);
            })
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (error) return <div className="error-banner">{error}</div>;
    if (loading) return <div className="loading">Loading…</div>;

    const tabs: { key: M365Tab; label: string }[] = [
        { key: "overview", label: "Overview" },
        { key: "licenses", label: "Licenses" },
        { key: "services", label: "Service Health" },
        { key: "entra", label: "Entra ID" },
        { key: "exchange", label: "Exchange" },
        { key: "secure-score", label: "Secure Score" },
        { key: "messages", label: "Message Center" },
    ];

    const licenseColumns: Column<LicenseSummary>[] = [
        { key: "display_name", header: "License" },
        { key: "sku_part_number", header: "SKU" },
        { key: "assigned_licenses", header: "Assigned" },
        { key: "available_licenses", header: "Available" },
        { key: "total_licenses", header: "Total" },
        {
            key: "total_monthly_cost",
            header: "Monthly Cost",
            render: (row) => <span>${row.total_monthly_cost.toLocaleString()}</span>,
        },
    ];

    const messageColumns: Column<MessageCenterItem>[] = [
        { key: "id", header: "ID" },
        { key: "title", header: "Title" },
        { key: "category", header: "Category" },
        { key: "severity", header: "Severity" },
        {
            key: "action_required",
            header: "Action",
            render: (row) => <StatusBadge status={row.action_required ? "warning" : "healthy"} label={row.action_required ? "Required" : "None"} />,
        },
    ];

    return (
        <>
            <PageHeader
                title="Microsoft 365"
                subtitle={tenant ? `${tenant.display_name} (${tenant.domain})` : "Microsoft 365 management"}
            />
            <div className="tab-bar">
                {tabs.map((t) => (
                    <button
                        key={t.key}
                        className={`tab-btn${tab === t.key ? " active" : ""}`}
                        onClick={() => setTab(t.key)}
                    >
                        {t.label}
                    </button>
                ))}
            </div>
            {tab === "overview" && tenant && (
                <div className="m365-overview">
                    <div className="ad-info-grid">
                        <div className="ad-info-card">
                            <h4>Tenant</h4>
                            <p><strong>Name:</strong> {tenant.display_name}</p>
                            <p><strong>Domain:</strong> {tenant.domain}</p>
                            <p><strong>Type:</strong> {tenant.tenant_type}</p>
                            <p><strong>Directory Sync:</strong> {tenant.directory_sync_enabled ? "Enabled" : "Disabled"}</p>
                            <p><strong>MFA:</strong> {tenant.mfa_enabled ? "Enabled" : "Disabled"}</p>
                            <p><strong>Conditional Access:</strong> {tenant.conditional_access_enabled ? "Enabled" : "Disabled"}</p>
                        </div>
                        <div className="ad-info-card">
                            <h4>Counts</h4>
                            <p><strong>Users:</strong> {tenant.total_users}</p>
                            <p><strong>Licensed Users:</strong> {tenant.licensed_users}</p>
                            <p><strong>Groups:</strong> {tenant.total_groups}</p>
                            <p><strong>Devices:</strong> {tenant.total_devices}</p>
                        </div>
                        <div className="ad-info-card">
                            <h4>Service Health</h4>
                            <p><strong>Overall:</strong> <StatusBadge status={serviceHealth?.overall_status === "healthy" ? "healthy" : "warning"} label={serviceHealth?.overall_status ?? "unknown"} /></p>
                            <p><strong>Active Incidents:</strong> {serviceHealth?.active_incidents ?? 0}</p>
                            <p><strong>Resolved (30d):</strong> {serviceHealth?.resolved_last_30_days ?? 0}</p>
                        </div>
                    </div>
                </div>
            )}
            {tab === "licenses" && (
                <>
                    <div className="m365-license-summary">
                        <p><strong>Total Monthly Cost:</strong> ${licenses.reduce((sum, l) => sum + l.total_monthly_cost, 0).toLocaleString()}</p>
                        <p><strong>Total Assigned:</strong> {licenses.reduce((sum, l) => sum + l.assigned_licenses, 0)}</p>
                    </div>
                    <DataTable columns={licenseColumns} data={licenses} emptyMessage="No licenses found" />
                </>
            )}
            {tab === "services" && serviceHealth && (
                <div className="m365-services">
                    {serviceHealth.services.map((svc) => (
                        <div key={svc.name} className="m365-service-item">
                            <div className="m365-service-header">
                                <strong>{svc.name}</strong>
                                <StatusBadge
                                    status={svc.status === "healthy" ? "healthy" : svc.status === "degraded" ? "warning" : "error"}
                                    label={svc.status}
                                />
                            </div>
                            {svc.issues.length > 0 && (
                                <div className="m365-service-issues">
                                    {svc.issues.map((issue, i) => (
                                        <div key={i} className="m365-issue">
                                            <p><strong>{issue.title}</strong> ({issue.status})</p>
                                            <p>Impact: {issue.impact}</p>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
            {tab === "entra" && entra && (
                <div className="ad-overview">
                    <div className="ad-info-grid">
                        <div className="ad-info-card">
                            <h4>Sign-In Health</h4>
                            <p><strong>Status:</strong> <StatusBadge status={entra.status === "healthy" ? "healthy" : "error"} label={entra.status} /></p>
                            <p><strong>Success Rate:</strong> {entra.sign_in_success_rate}%</p>
                            <p><strong>Total Sign-Ins (24h):</strong> {entra.total_sign_ins_24h}</p>
                            <p><strong>Failed (24h):</strong> {entra.failed_sign_ins_24h}</p>
                            <p><strong>Blocked (24h):</strong> {entra.blocked_sign_ins_24h}</p>
                        </div>
                        <div className="ad-info-card">
                            <h4>Security</h4>
                            <p><strong>MFA Success Rate:</strong> {entra.mfa_success_rate}%</p>
                            <p><strong>Conditional Access Policies:</strong> {entra.conditional_access_policies}</p>
                            <p><strong>Risk Detections (24h):</strong> {entra.risk_detections_24h}</p>
                            <p><strong>Risky Users:</strong> {entra.risky_users}</p>
                        </div>
                        <div className="ad-info-card">
                            <h4>Password Management</h4>
                            <p><strong>SSPR Registrations:</strong> {entra.password_reset_registrations}</p>
                            <p><strong>SSPR Resets (30d):</strong> {entra.self_service_password_resets_30d}</p>
                            <p><strong>Deleted Objects (30d):</strong> {entra.deleted_objects_30d}</p>
                        </div>
                    </div>
                </div>
            )}
            {tab === "exchange" && exchange && (
                <div className="ad-overview">
                    <div className="ad-info-grid">
                        <div className="ad-info-card">
                            <h4>Mailboxes</h4>
                            <p><strong>Status:</strong> <StatusBadge status={exchange.status === "healthy" ? "healthy" : "error"} label={exchange.status} /></p>
                            <p><strong>Total:</strong> {exchange.mailboxes_total}</p>
                            <p><strong>Active:</strong> {exchange.mailboxes_active}</p>
                            <p><strong>Online:</strong> {exchange.mailboxes_online}</p>
                            <p><strong>Avg Size:</strong> {exchange.average_mailbox_size_gb} GB</p>
                        </div>
                        <div className="ad-info-card">
                            <h4>Mail Flow</h4>
                            <p><strong>Sent (24h):</strong> {exchange.daily_emails_sent.toLocaleString()}</p>
                            <p><strong>Received (24h):</strong> {exchange.daily_emails_received.toLocaleString()}</p>
                            <p><strong>Queue Length:</strong> {exchange.queue_length}</p>
                        </div>
                        <div className="ad-info-card">
                            <h4>Infrastructure</h4>
                            <p><strong>DAGs:</strong> {exchange.dags_count}</p>
                            <p><strong>Databases:</strong> {exchange.databases_count}</p>
                            <p><strong>Availability:</strong> {exchange.database_availability}%</p>
                            <p><strong>Transport Rules:</strong> {exchange.transport_rules_count}</p>
                        </div>
                    </div>
                </div>
            )}
            {tab === "secure-score" && score && (
                <div className="ad-overview">
                    <div className="ad-info-grid">
                        <div className="ad-info-card">
                            <h4>Overall Score</h4>
                            <p className="secure-score-big">{score.current_score} / {score.max_score}</p>
                            <p><strong>Industry Comparison:</strong> {score.comparison_to_industry.tier.replace("_", " ")}</p>
                            <p><strong>Industry Average:</strong> {score.comparison_to_industry.average_score}</p>
                            <p><strong>Recommended Actions:</strong> {score.recommended_actions_count}</p>
                            <p><strong>High Priority:</strong> {score.high_priority_actions}</p>
                        </div>
                        {score.categories.map((cat) => (
                            <div key={cat.name} className="ad-info-card">
                                <h4>{cat.name}</h4>
                                <div className="score-bar">
                                    <div className="score-fill" style={{ width: `${cat.percentage}%` }} />
                                </div>
                                <p>{cat.current_score} / {cat.max_score} ({cat.percentage}%)</p>
                            </div>
                        ))}
                    </div>
                </div>
            )}
            {tab === "messages" && (
                <DataTable columns={messageColumns} data={messages} emptyMessage="No messages" />
            )}
        </>
    );
}
