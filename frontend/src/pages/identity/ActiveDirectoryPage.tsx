import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import DataTable, { Column } from "../../components/common/DataTable";
import { identityApi, DomainController, Domain, Forest, OrganizationalUnit, UserSummary, GroupSummary, ComputerSummary, GPO, FSMORoles, DNSHealth, DHCPHealth } from "../../services/identity";

type ADTab = "overview" | "users" | "computers" | "groups" | "ous" | "gpos" | "fsmo" | "dns" | "dhcp";

export default function ActiveDirectoryPage() {
    const [tab, setTab] = useState<ADTab>("overview");
    const [dcs, setDCs] = useState<DomainController[]>([]);
    const [domain, setDomain] = useState<Domain | null>(null);
    const [forest, setForest] = useState<Forest | null>(null);
    const [ous, setOUs] = useState<OrganizationalUnit[]>([]);
    const [users, setUsers] = useState<UserSummary[]>([]);
    const [groups, setGroups] = useState<GroupSummary[]>([]);
    const [computers, setComputers] = useState<ComputerSummary[]>([]);
    const [gpos, setGPOs] = useState<GPO[]>([]);
    const [fsmo, setFSMO] = useState<FSMORoles | null>(null);
    const [dns, setDNS] = useState<DNSHealth | null>(null);
    const [dhcp, setDHCP] = useState<DHCPHealth | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        Promise.all([
            identityApi.getDomainControllers(),
            identityApi.getDomain(),
            identityApi.getForest(),
            identityApi.getOUs(),
            identityApi.getUsers(),
            identityApi.getGroups(),
            identityApi.getComputers(),
            identityApi.getGPOs(),
            identityApi.getFSMORoles(),
            identityApi.getDNSHealth(),
            identityApi.getDHCPHealth(),
        ])
            .then(([dcRes, domRes, forRes, ouRes, uRes, gRes, cRes, gpoRes, fsmoRes, dnsRes, dhcpRes]) => {
                setDCs(dcRes.domain_controllers);
                setDomain(domRes.domain);
                setForest(forRes.forest);
                setOUs(ouRes.organizational_units);
                setUsers(uRes.users);
                setGroups(gRes.groups);
                setComputers(cRes.computers);
                setGPOs(gpoRes.gpos);
                setFSMO(fsmoRes.fsmo_roles);
                setDNS(dnsRes.dns_health);
                setDHCP(dhcpRes.dhcp_health);
            })
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (error) return <div className="error-banner">{error}</div>;
    if (loading) return <div className="loading">Loading…</div>;

    const tabs: { key: ADTab; label: string }[] = [
        { key: "overview", label: "Overview" },
        { key: "users", label: "Users" },
        { key: "computers", label: "Computers" },
        { key: "groups", label: "Groups" },
        { key: "ous", label: "OUs" },
        { key: "gpos", label: "GPOs" },
        { key: "fsmo", label: "FSMO" },
        { key: "dns", label: "DNS" },
        { key: "dhcp", label: "DHCP" },
    ];

    const userColumns: Column<UserSummary>[] = [
        { key: "sam_account_name", header: "Username" },
        { key: "display_name", header: "Display Name" },
        { key: "email", header: "Email" },
        { key: "department", header: "Department" },
        { key: "title", header: "Title" },
        { key: "ou", header: "OU" },
        {
            key: "enabled",
            header: "Status",
            render: (row) => <StatusBadge status={row.enabled ? "healthy" : "error"} label={row.enabled ? "Enabled" : "Disabled"} />,
        },
    ];

    const computerColumns: Column<ComputerSummary>[] = [
        { key: "name", header: "Name" },
        { key: "ip_address", header: "IP Address" },
        { key: "os_version", header: "OS" },
        { key: "ou", header: "OU" },
        {
            key: "is_domain_controller",
            header: "Role",
            render: (row) => <span className="tag">{row.is_domain_controller ? "DC" : "Member"}</span>,
        },
        {
            key: "enabled",
            header: "Status",
            render: (row) => <StatusBadge status={row.enabled ? "healthy" : "error"} label={row.enabled ? "Enabled" : "Disabled"} />,
        },
    ];

    const groupColumns: Column<GroupSummary>[] = [
        { key: "name", header: "Name" },
        { key: "scope", header: "Scope" },
        { key: "category", header: "Category" },
        { key: "member_count", header: "Members" },
        { key: "description", header: "Description" },
    ];

    const ouColumns: Column<OrganizationalUnit>[] = [
        { key: "name", header: "Name" },
        { key: "path", header: "Path" },
        { key: "user_count", header: "Users" },
        { key: "computer_count", header: "Computers" },
        { key: "group_count", header: "Groups" },
        { key: "gpo_count", header: "GPOs" },
    ];

    const gpoColumns: Column<GPO>[] = [
        { key: "name", header: "Name" },
        { key: "version", header: "Version" },
        {
            key: "enabled",
            header: "Status",
            render: (row) => <StatusBadge status={row.enabled ? "healthy" : "error"} label={row.enabled ? "Enabled" : "Disabled"} />,
        },
        { key: "computer_count", header: "Computers" },
        { key: "user_count", header: "Users" },
    ];

    return (
        <>
            <PageHeader
                title="Active Directory"
                subtitle={domain ? `${domain.name} (${domain.netbios_name})` : "Active Directory management"}
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
            {tab === "overview" && domain && forest && (
                <div className="ad-overview">
                    <div className="ad-info-grid">
                        <div className="ad-info-card">
                            <h4>Domain</h4>
                            <p><strong>Name:</strong> {domain.name}</p>
                            <p><strong>NetBIOS:</strong> {domain.netbios_name}</p>
                            <p><strong>Functional Level:</strong> {domain.functional_level}</p>
                            <p><strong>Users:</strong> {domain.user_count}</p>
                            <p><strong>Computers:</strong> {domain.computer_count}</p>
                            <p><strong>Groups:</strong> {domain.group_count}</p>
                            <p><strong>OUs:</strong> {domain.ou_count}</p>
                        </div>
                        <div className="ad-info-card">
                            <h4>Forest</h4>
                            <p><strong>Name:</strong> {forest.name}</p>
                            <p><strong>Functional Level:</strong> {forest.functional_level}</p>
                            <p><strong>Domains:</strong> {forest.domain_count}</p>
                            <p><strong>Global Catalogs:</strong> {forest.global_catalog_count}</p>
                            <p><strong>Sites:</strong> {forest.site_count}</p>
                            <p><strong>Schema Master:</strong> {forest.schema_master}</p>
                        </div>
                        <div className="ad-info-card">
                            <h4>Domain Controllers</h4>
                            {dcs.map((dc) => (
                                <div key={dc.name} className="ad-dc-item">
                                    <StatusBadge status={dc.status === "online" ? "healthy" : "error"} label={dc.status} />
                                    <span>{dc.name} ({dc.ip_address})</span>
                                    <span className="tag">{dc.site}</span>
                                    {dc.is_global_catalog && <span className="tag">GC</span>}
                                    {dc.is_fsmo && <span className="tag">FSMO</span>}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}
            {tab === "users" && <DataTable columns={userColumns} data={users} emptyMessage="No users found" />}
            {tab === "computers" && <DataTable columns={computerColumns} data={computers} emptyMessage="No computers found" />}
            {tab === "groups" && <DataTable columns={groupColumns} data={groups} emptyMessage="No groups found" />}
            {tab === "ous" && <DataTable columns={ouColumns} data={ous} emptyMessage="No OUs found" />}
            {tab === "gpos" && <DataTable columns={gpoColumns} data={gpos} emptyMessage="No GPOs found" />}
            {tab === "fsmo" && fsmo && (
                <div className="ad-overview">
                    <div className="ad-info-grid">
                        <div className="ad-info-card">
                            <h4>Forest Roles</h4>
                            {Object.entries(fsmo.forest_roles).map(([key, role]) => (
                                <div key={key} className="ad-fsmo-item">
                                    <strong>{role.role}:</strong> {role.holder}
                                    <StatusBadge status={role.status === "online" ? "healthy" : "error"} label={role.status} />
                                </div>
                            ))}
                        </div>
                        <div className="ad-info-card">
                            <h4>Domain Roles</h4>
                            {Object.entries(fsmo.domain_roles).map(([key, role]) => (
                                <div key={key} className="ad-fsmo-item">
                                    <strong>{role.role}:</strong> {role.holder}
                                    <StatusBadge status={role.status === "online" ? "healthy" : "error"} label={role.status} />
                                </div>
                            ))}
                            {fsmo.all_roles_held_by_single_dc && (
                                <p className="warning-text">⚠ All roles held by a single DC</p>
                            )}
                        </div>
                    </div>
                </div>
            )}
            {tab === "dns" && dns && (
                <div className="ad-overview">
                    <div className="ad-info-grid">
                        {dns.servers.map((srv) => (
                            <div key={srv.name} className="ad-info-card">
                                <h4>{srv.name} ({srv.ip_address})</h4>
                                <p><strong>Status:</strong> <StatusBadge status={srv.status === "healthy" ? "healthy" : "error"} label={srv.status} /></p>
                                <p><strong>Zones:</strong> {srv.zones_count}</p>
                                <p><strong>Records:</strong> {srv.records_count}</p>
                                <p><strong>Response Time:</strong> {srv.response_time_ms}ms</p>
                                <p><strong>Forwarders:</strong> {srv.forwarders.join(", ")}</p>
                            </div>
                        ))}
                    </div>
                    <div className="ad-summary">
                        <p><strong>Total Zones:</strong> {dns.total_zones}</p>
                        <p><strong>Total Records:</strong> {dns.total_records}</p>
                        <p><strong>DNSSEC:</strong> {dns.dnssec_enabled ? "Enabled" : "Disabled"}</p>
                    </div>
                </div>
            )}
            {tab === "dhcp" && dhcp && (
                <div className="ad-overview">
                    <div className="ad-info-grid">
                        {dhcp.servers.map((srv) => (
                            <div key={srv.name} className="ad-info-card">
                                <h4>{srv.name} ({srv.ip_address})</h4>
                                <p><strong>Status:</strong> <StatusBadge status={srv.status === "healthy" ? "healthy" : "error"} label={srv.status} /></p>
                                <p><strong>Scopes:</strong> {srv.scopes_count}</p>
                                <p><strong>Utilization:</strong> {srv.utilization_percent}%</p>
                                <p><strong>Used:</strong> {srv.used_addresses} / {srv.total_addresses}</p>
                            </div>
                        ))}
                    </div>
                    <div className="ad-summary">
                        <p><strong>Total Scopes:</strong> {dhcp.total_scopes}</p>
                        <p><strong>Overall Utilization:</strong> {dhcp.overall_utilization_percent}%</p>
                        <p><strong>Authorized:</strong> {dhcp.authorized ? "Yes" : "No"}</p>
                    </div>
                </div>
            )}
        </>
    );
}
