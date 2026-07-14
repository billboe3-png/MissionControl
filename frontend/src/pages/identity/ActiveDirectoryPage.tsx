import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import DataTable, { Column } from "../../components/common/DataTable";
import {
    identityApi,
    ADSummary,
    ADUser,
    ADGroup,
    ADDevice,
    ADHealthResponse,
    ConnectionTestResult,
} from "../../services/identity";

type ADTab = "overview" | "users" | "groups" | "devices" | "health";

export default function ActiveDirectoryPage() {
    const [tab, setTab] = useState<ADTab>("overview");
    const [summary, setSummary] = useState<ADSummary | null>(null);
    const [users, setUsers] = useState<ADUser[]>([]);
    const [groups, setGroups] = useState<ADGroup[]>([]);
    const [devices, setDevices] = useState<ADDevice[]>([]);
    const [health, setHealth] = useState<ADHealthResponse | null>(null);
    const [connTest, setConnTest] = useState<ConnectionTestResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        Promise.all([
            identityApi.testAD(),
            identityApi.getADSummary(),
            identityApi.getADUsers(),
            identityApi.getADGroups(),
            identityApi.getADDevices(),
            identityApi.getADHealth(),
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

    const tabs: { key: ADTab; label: string }[] = [
        { key: "overview", label: "Overview" },
        { key: "users", label: "Users" },
        { key: "groups", label: "Groups" },
        { key: "devices", label: "Devices" },
        { key: "health", label: "Health" },
    ];

    const userColumns: Column<ADUser>[] = [
        { key: "sam_account_name", header: "Username" },
        { key: "display_name", header: "Display Name" },
        { key: "email", header: "Email" },
        { key: "department", header: "Department" },
        { key: "title", header: "Title" },
        {
            key: "enabled",
            header: "Status",
            render: (row) => (
                <StatusBadge
                    status={row.enabled ? "healthy" : "error"}
                    label={row.enabled ? "Enabled" : "Disabled"}
                />
            ),
        },
    ];

    const groupColumns: Column<ADGroup>[] = [
        { key: "name", header: "Name" },
        { key: "description", header: "Description" },
    ];

    const deviceColumns: Column<ADDevice>[] = [
        { key: "name", header: "Name" },
        { key: "dns_name", header: "DNS Name" },
        { key: "os_version", header: "OS" },
    ];

    return (
        <>
            <PageHeader
                title="Active Directory"
                subtitle={summary?.domain?.name ?? "Active Directory management"}
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
                <div className="ad-overview">
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
                            <h4>Domain</h4>
                            <p><strong>Name:</strong> {summary.domain?.name ?? "N/A"}</p>
                            <p><strong>Base DN:</strong> {summary.domain?.base_dn ?? "N/A"}</p>
                        </div>
                        <div className="ad-info-card">
                            <h4>Counts</h4>
                            <p><strong>Users:</strong> {summary.user_count}</p>
                            <p><strong>Groups:</strong> {summary.group_count}</p>
                            <p><strong>Computers:</strong> {summary.computer_count}</p>
                        </div>
                        {health && (
                            <div className="ad-info-card">
                                <h4>Replication</h4>
                                <p>
                                    <strong>Status:</strong>{" "}
                                    <StatusBadge
                                        status={health.replication?.status === "healthy" ? "healthy" : "warning"}
                                        label={health.replication?.status ?? "unknown"}
                                    />
                                </p>
                                <p><strong>Pending:</strong> {health.replication?.pending_replications ?? 0}</p>
                                <p><strong>Failed:</strong> {health.replication?.failed_replications ?? 0}</p>
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
            {tab === "health" && health && (
                <div className="ad-overview">
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
                        </div>
                        <div className="ad-info-card">
                            <h4>Replication</h4>
                            <p><strong>Status:</strong> {health.replication?.status ?? "unknown"}</p>
                            <p><strong>Pending:</strong> {health.replication?.pending_replications ?? 0}</p>
                            <p><strong>Failed:</strong> {health.replication?.failed_replications ?? 0}</p>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}
