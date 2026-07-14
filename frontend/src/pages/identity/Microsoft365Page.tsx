import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import DataTable, { Column } from "../../components/common/DataTable";
import {
    identityApi,
    M365Summary,
    M365User,
    M365Group,
    M365Device,
    M365HealthResponse,
    M365License,
    ConnectionTestResult,
} from "../../services/identity";

type M365Tab = "overview" | "users" | "groups" | "devices" | "licenses" | "health";

export default function Microsoft365Page() {
    const [tab, setTab] = useState<M365Tab>("overview");
    const [summary, setSummary] = useState<M365Summary | null>(null);
    const [users, setUsers] = useState<M365User[]>([]);
    const [groups, setGroups] = useState<M365Group[]>([]);
    const [devices, setDevices] = useState<M365Device[]>([]);
    const [health, setHealth] = useState<M365HealthResponse | null>(null);
    const [connTest, setConnTest] = useState<ConnectionTestResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        Promise.all([
            identityApi.testM365(),
            identityApi.getM365Summary(),
            identityApi.getM365Users(),
            identityApi.getM365Groups(),
            identityApi.getM365Devices(),
            identityApi.getM365Health(),
        ])
            .then(([testRes, sumRes, uRes, gRes, dRes, hRes]) => {
                setConnTest(testRes);
                setSummary(sumRes);
                setUsers(uRes.users);
                setGroups(gRes.groups);
                setDevices(dRes.devices);
                setHealth(hRes);
            })
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (error) return <div className="error-banner">{error}</div>;
    if (loading) return <div className="loading">Loading…</div>;

    const tabs: { key: M365Tab; label: string }[] = [
        { key: "overview", label: "Overview" },
        { key: "users", label: "Users" },
        { key: "groups", label: "Groups" },
        { key: "devices", label: "Devices" },
        { key: "licenses", label: "Licenses" },
        { key: "health", label: "Health" },
    ];

    const userColumns: Column<M365User>[] = [
        { key: "display_name", header: "Display Name" },
        { key: "email", header: "Email" },
        { key: "department", header: "Department" },
        { key: "job_title", header: "Title" },
        {
            key: "account_enabled",
            header: "Status",
            render: (row) => (
                <StatusBadge
                    status={row.account_enabled ? "healthy" : "error"}
                    label={row.account_enabled ? "Enabled" : "Disabled"}
                />
            ),
        },
    ];

    const groupColumns: Column<M365Group>[] = [
        { key: "display_name", header: "Name" },
        { key: "mail", header: "Email" },
        { key: "type", header: "Type" },
    ];

    const deviceColumns: Column<M365Device>[] = [
        {
            key: "display_name",
            header: "Name",
            render: (row) => row.display_name ?? row.name ?? "N/A",
        },
        { key: "os", header: "OS" },
        { key: "version", header: "Version" },
        {
            key: "compliant",
            header: "Compliant",
            render: (row) => (
                <StatusBadge
                    status={row.compliant ? "healthy" : "warning"}
                    label={row.compliant ? "Yes" : "No"}
                />
            ),
        },
    ];

    const licenseColumns: Column<M365License>[] = [
        { key: "name", header: "License" },
        { key: "sku", header: "SKU" },
        { key: "assigned", header: "Assigned" },
        { key: "available", header: "Available" },
        { key: "total", header: "Total" },
    ];

    return (
        <>
            <PageHeader
                title="Microsoft 365"
                subtitle={summary?.tenant?.display_name ?? "Microsoft 365 management"}
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
            {tab === "overview" && summary && (
                <div className="m365-overview">
                    <div className="ad-info-grid">
                        <div className="ad-info-card">
                            <h4>Connection</h4>
                            <p>
                                <strong>Status:</strong>{" "}
                                <StatusBadge
                                    status={connTest?.connected ? "healthy" : "error"}
                                    label={connTest?.connected ? "Connected" : "Disconnected"}
                                />
                            </p>
                            {connTest?.latency_ms != null && (
                                <p><strong>Latency:</strong> {connTest.latency_ms}ms</p>
                            )}
                            {connTest?.message && (
                                <p><strong>Message:</strong> {connTest.message}</p>
                            )}
                        </div>
                        <div className="ad-info-card">
                            <h4>Tenant</h4>
                            <p><strong>Name:</strong> {summary.tenant?.display_name ?? "N/A"}</p>
                            <p><strong>Type:</strong> {summary.tenant?.tenant_type ?? "N/A"}</p>
                            <p><strong>Domains:</strong> {summary.tenant?.verified_domains?.join(", ") ?? "N/A"}</p>
                        </div>
                        <div className="ad-info-card">
                            <h4>Licensing</h4>
                            <p><strong>Licensed Users:</strong> {summary.licensed_users}</p>
                            <p><strong>License SKUs:</strong> {summary.licenses?.length ?? 0}</p>
                        </div>
                        {health && (
                            <div className="ad-info-card">
                                <h4>Service Health</h4>
                                <p>
                                    <strong>Status:</strong>{" "}
                                    <StatusBadge
                                        status={health.status === "healthy" ? "healthy" : "warning"}
                                        label={health.status}
                                    />
                                </p>
                                <p><strong>Active Incidents:</strong> {health.active_incidents}</p>
                            </div>
                        )}
                    </div>
                </div>
            )}
            {tab === "users" && (
                <DataTable columns={userColumns} data={users} emptyMessage="No users found" />
            )}
            {tab === "groups" && (
                <DataTable columns={groupColumns} data={groups} emptyMessage="No groups found" />
            )}
            {tab === "devices" && (
                <DataTable columns={deviceColumns} data={devices} emptyMessage="No devices found" />
            )}
            {tab === "licenses" && (
                <DataTable columns={licenseColumns} data={summary?.licenses ?? []} emptyMessage="No licenses found" />
            )}
            {tab === "health" && health && (
                <div className="m365-overview">
                    <div className="ad-info-grid">
                        <div className="ad-info-card">
                            <h4>Overall Health</h4>
                            <p>
                                <strong>Status:</strong>{" "}
                                <StatusBadge
                                    status={health.status === "healthy" ? "healthy" : "warning"}
                                    label={health.status}
                                />
                            </p>
                            <p><strong>Active Incidents:</strong> {health.active_incidents}</p>
                        </div>
                        {health.services.map((svc) => (
                            <div key={svc.name} className="ad-info-card">
                                <h4>{svc.name}</h4>
                                <p>
                                    <strong>Status:</strong>{" "}
                                    <StatusBadge
                                        status={svc.status === "healthy" ? "healthy" : svc.status === "degraded" ? "warning" : "error"}
                                        label={svc.status}
                                    />
                                </p>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </>
    );
}
