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
    ADActionResponse,
    ADUserGroup,
    ConnectionTestResult,
} from "../../services/identity";

type ADTab = "overview" | "users" | "groups" | "devices" | "health";

type ModalState =
    | null
    | { type: "password"; user: ADUser }
    | { type: "rename"; user: ADUser }
    | { type: "groups"; user: ADUser }
    | { type: "confirm-disable"; user: ADUser }
    | { type: "confirm-enable"; user: ADUser };

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
    const [modal, setModal] = useState<ModalState>(null);
    const [actionResult, setActionResult] = useState<ADActionResponse | null>(null);
    const [userSearch, setUserSearch] = useState("");

    const reloadUsers = () => identityApi.getADUsers().then((r) => setUsers(r.users));

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
    if (loading) return <div className="loading-bar" />;

    const tabs: { key: ADTab; label: string }[] = [
        { key: "overview", label: "Overview" },
        { key: "users", label: "Users" },
        { key: "groups", label: "Groups" },
        { key: "devices", label: "Devices" },
        { key: "health", label: "Health" },
    ];

    const filteredUsers = users.filter((u) => {
        if (!userSearch) return true;
        const q = userSearch.toLowerCase();
        return (
            u.sam_account_name.toLowerCase().includes(q) ||
            u.display_name.toLowerCase().includes(q) ||
            (u.email && u.email.toLowerCase().includes(q))
        );
    });

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
        {
            key: "sam_account_name",
            header: "Actions",
            render: (row) => (
                <div className="ad-actions">
                    <button
                        className="btn btn-sm btn-primary"
                        onClick={() => setModal({ type: "password", user: row })}
                        title="Reset Password"
                    >
                        Reset PW
                    </button>
                    {row.enabled ? (
                        <button
                            className="btn btn-sm btn-warning"
                            onClick={() => setModal({ type: "confirm-disable", user: row })}
                            title="Disable Account"
                        >
                            Disable
                        </button>
                    ) : (
                        <button
                            className="btn btn-sm btn-success"
                            onClick={async () => {
                                const res = await identityApi.enableAccount(row.sam_account_name);
                                setActionResult(res);
                                if (res.success) reloadUsers();
                            }}
                            title="Enable Account"
                        >
                            Enable
                        </button>
                    )}
                    <button
                        className="btn btn-sm btn-secondary"
                        onClick={() => setModal({ type: "rename", user: row })}
                        title="Rename"
                    >
                        Rename
                    </button>
                    <button
                        className="btn btn-sm btn-secondary"
                        onClick={() => setModal({ type: "groups", user: row })}
                        title="Manage Groups"
                    >
                        Groups
                    </button>
                </div>
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

            {actionResult && (
                <div className={`alert ${actionResult.success ? "alert-success" : "alert-error"}`}>
                    {actionResult.success ? actionResult.message : actionResult.error}
                    <button className="alert-close" onClick={() => setActionResult(null)}>×</button>
                </div>
            )}

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
                <>
                    <div className="ad-search-bar">
                        <input
                            type="text"
                            placeholder="Search users by name, username, or email..."
                            value={userSearch}
                            onChange={(e) => setUserSearch(e.target.value)}
                            className="form-input"
                        />
                    </div>
                    <DataTable columns={userColumns} data={filteredUsers} emptyMessage="No users found" />
                </>
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

            {modal?.type === "password" && (
                <PasswordResetModal
                    user={modal.user}
                    onClose={() => setModal(null)}
                    onDone={(res) => {
                        setActionResult(res);
                        setModal(null);
                    }}
                />
            )}
            {modal?.type === "rename" && (
                <RenameUserModal
                    user={modal.user}
                    onClose={() => setModal(null)}
                    onDone={(res) => {
                        setActionResult(res);
                        if (res.success) reloadUsers();
                        setModal(null);
                    }}
                />
            )}
            {modal?.type === "groups" && (
                <GroupMembershipModal
                    user={modal.user}
                    allGroups={groups}
                    onClose={() => setModal(null)}
                />
            )}
            {modal?.type === "confirm-disable" && (
                <ConfirmModal
                    title="Disable Account"
                    message={`Are you sure you want to disable ${modal.user.sam_account_name}?`}
                    confirmLabel="Disable"
                    confirmClass="btn-danger"
                    onConfirm={async () => {
                        const res = await identityApi.disableAccount(modal.user.sam_account_name);
                        setActionResult(res);
                        if (res.success) reloadUsers();
                        setModal(null);
                    }}
                    onCancel={() => setModal(null)}
                />
            )}
        </>
    );
}

function PasswordResetModal({
    user,
    onClose,
    onDone,
}: {
    user: ADUser;
    onClose: () => void;
    onDone: (res: ADActionResponse) => void;
}) {
    const [password, setPassword] = useState("");
    const [confirm, setConfirm] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async () => {
        if (password.length < 8) {
            setError("Password must be at least 8 characters");
            return;
        }
        if (password !== confirm) {
            setError("Passwords do not match");
            return;
        }
        setSubmitting(true);
        setError(null);
        try {
            const res = await identityApi.resetPassword(user.sam_account_name, password);
            onDone(res);
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : "Failed");
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h3>Reset Password — {user.sam_account_name}</h3>
                    <button className="modal-close" onClick={onClose}>×</button>
                </div>
                <div className="modal-body">
                    {error && <div className="alert alert-error">{error}</div>}
                    <label className="form-label">New Password</label>
                    <input
                        type="password"
                        className="form-input"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        autoFocus
                    />
                    <label className="form-label">Confirm Password</label>
                    <input
                        type="password"
                        className="form-input"
                        value={confirm}
                        onChange={(e) => setConfirm(e.target.value)}
                    />
                </div>
                <div className="modal-footer">
                    <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
                    <button
                        className="btn btn-primary"
                        onClick={handleSubmit}
                        disabled={submitting}
                    >
                        {submitting ? "Resetting..." : "Reset Password"}
                    </button>
                </div>
            </div>
        </div>
    );
}

function RenameUserModal({
    user,
    onClose,
    onDone,
}: {
    user: ADUser;
    onClose: () => void;
    onDone: (res: ADActionResponse) => void;
}) {
    const [displayName, setDisplayName] = useState(user.display_name || "");
    const [firstName, setFirstName] = useState("");
    const [lastName, setLastName] = useState("");
    const [submitting, setSubmitting] = useState(false);

    const handleSubmit = async () => {
        if (!displayName.trim()) return;
        setSubmitting(true);
        try {
            const res = await identityApi.renameUser(
                user.sam_account_name,
                displayName,
                firstName || undefined,
                lastName || undefined,
            );
            onDone(res);
        } catch {
            onDone({ success: false, error: "Request failed", message: null });
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h3>Rename — {user.sam_account_name}</h3>
                    <button className="modal-close" onClick={onClose}>×</button>
                </div>
                <div className="modal-body">
                    <label className="form-label">Display Name</label>
                    <input
                        className="form-input"
                        value={displayName}
                        onChange={(e) => setDisplayName(e.target.value)}
                        autoFocus
                    />
                    <label className="form-label">First Name</label>
                    <input
                        className="form-input"
                        value={firstName}
                        onChange={(e) => setFirstName(e.target.value)}
                        placeholder="Optional"
                    />
                    <label className="form-label">Last Name</label>
                    <input
                        className="form-input"
                        value={lastName}
                        onChange={(e) => setLastName(e.target.value)}
                        placeholder="Optional"
                    />
                </div>
                <div className="modal-footer">
                    <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
                    <button
                        className="btn btn-primary"
                        onClick={handleSubmit}
                        disabled={submitting || !displayName.trim()}
                    >
                        {submitting ? "Saving..." : "Save"}
                    </button>
                </div>
            </div>
        </div>
    );
}

function GroupMembershipModal({
    user,
    allGroups,
    onClose,
}: {
    user: ADUser;
    allGroups: ADGroup[];
    onClose: () => void;
}) {
    const [userGroups, setUserGroups] = useState<ADUserGroup[]>([]);
    const [loading, setLoading] = useState(true);
    const [result, setResult] = useState<ADActionResponse | null>(null);
    const [groupSearch, setGroupSearch] = useState("");

    useEffect(() => {
        identityApi.getUserGroups(user.sam_account_name).then((r) => {
            setUserGroups(r.groups || []);
            setLoading(false);
        });
    }, [user.sam_account_name]);

    const memberNames = new Set(userGroups.map((g) => g.name));
    const availableGroups = allGroups.filter(
        (g) => !memberNames.has(g.name) && (!groupSearch || g.name.toLowerCase().includes(groupSearch.toLowerCase())),
    );

    const handleAdd = async (groupName: string) => {
        const res = await identityApi.addToGroup(user.sam_account_name, groupName);
        setResult(res);
        if (res.success) {
            setUserGroups([...userGroups, { name: groupName, dn: "" }]);
        }
    };

    const handleRemove = async (groupName: string) => {
        const res = await identityApi.removeFromGroup(user.sam_account_name, groupName);
        setResult(res);
        if (res.success) {
            setUserGroups(userGroups.filter((g) => g.name !== groupName));
        }
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal modal-wide" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h3>Groups — {user.sam_account_name}</h3>
                    <button className="modal-close" onClick={onClose}>×</button>
                </div>
                <div className="modal-body">
                    {result && (
                        <div className={`alert ${result.success ? "alert-success" : "alert-error"}`}>
                            {result.success ? result.message : result.error}
                        </div>
                    )}
                    <div className="ad-groups-layout">
                        <div className="ad-groups-section">
                            <h4>Member Of ({userGroups.length})</h4>
                            {loading ? (
                                <div className="loading-bar" />
                            ) : userGroups.length === 0 ? (
                                <p className="text-muted">Not a member of any groups</p>
                            ) : (
                                <ul className="ad-group-list">
                                    {userGroups.map((g) => (
                                        <li key={g.name}>
                                            <span>{g.name}</span>
                                            <button
                                                className="btn btn-sm btn-danger"
                                                onClick={() => handleRemove(g.name)}
                                            >
                                                Remove
                                            </button>
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </div>
                        <div className="ad-groups-section">
                            <h4>Add to Group</h4>
                            <input
                                type="text"
                                className="form-input"
                                placeholder="Search groups..."
                                value={groupSearch}
                                onChange={(e) => setGroupSearch(e.target.value)}
                            />
                            <ul className="ad-group-list">
                                {availableGroups.slice(0, 50).map((g) => (
                                    <li key={g.name}>
                                        <span>{g.name}</span>
                                        <button
                                            className="btn btn-sm btn-primary"
                                            onClick={() => handleAdd(g.name)}
                                        >
                                            Add
                                        </button>
                                    </li>
                                ))}
                                {availableGroups.length === 0 && (
                                    <li className="text-muted">No matching groups</li>
                                )}
                            </ul>
                        </div>
                    </div>
                </div>
                <div className="modal-footer">
                    <button className="btn btn-secondary" onClick={onClose}>Close</button>
                </div>
            </div>
        </div>
    );
}

function ConfirmModal({
    title,
    message,
    confirmLabel,
    confirmClass,
    onConfirm,
    onCancel,
}: {
    title: string;
    message: string;
    confirmLabel: string;
    confirmClass: string;
    onConfirm: () => void;
    onCancel: () => void;
}) {
    return (
        <div className="modal-overlay" onClick={onCancel}>
            <div className="modal modal-sm" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h3>{title}</h3>
                    <button className="modal-close" onClick={onCancel}>×</button>
                </div>
                <div className="modal-body">
                    <p>{message}</p>
                </div>
                <div className="modal-footer">
                    <button className="btn btn-secondary" onClick={onCancel}>Cancel</button>
                    <button className={`btn ${confirmClass}`} onClick={onConfirm}>
                        {confirmLabel}
                    </button>
                </div>
            </div>
        </div>
    );
}
