import { useCallback, useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import { useToast } from "../../contexts/ToastContext";
import { usersApi, UserData } from "../../services/users";

export default function UsersPage() {
    const [users, setUsers] = useState<UserData[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [showModal, setShowModal] = useState(false);
    const [editingUser, setEditingUser] = useState<UserData | undefined>(undefined);
    const { showToast } = useToast();

    const loadData = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await usersApi.list();
            setUsers(data);
        } catch (e: any) {
            setError(e.message || "Failed to load users");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { loadData(); }, [loadData]);

    const handleDelete = async (user: UserData) => {
        if (!window.confirm(`Delete user "${user.display_name}"?`)) return;
        try {
            await usersApi.remove(user.id);
            showToast("User deleted", "success");
            loadData();
        } catch (e: any) {
            showToast(e.message || "Delete failed", "error");
        }
    };

    const handleToggle = async (user: UserData) => {
        try {
            await usersApi.update(user.id, { enabled: !user.enabled });
            showToast(user.enabled ? "User disabled" : "User enabled", "success");
            loadData();
        } catch (e: any) {
            showToast(e.message || "Update failed", "error");
        }
    };

    const ROLE_LABELS: Record<string, string> = {
        global_admin: "Global Admin",
        company_admin: "Company Admin",
        site_admin: "Site Admin",
        operator: "Operator",
        readonly: "Read Only",
    };

    return (
        <>
            <PageHeader
                title="Users"
                subtitle="Manage user accounts and roles"
                actions={
                    <button className="btn btn-primary" onClick={() => { setEditingUser(undefined); setShowModal(true); }}>
                        + Add User
                    </button>
                }
            />

            {error && <div className="error-banner">{error}</div>}

            {loading ? (
                <div className="loading-bar" />
            ) : users.length === 0 ? (
                <div className="empty-state">
                    <h3>No Users</h3>
                    <p>Create your first user account.</p>
                    <button className="btn btn-primary" onClick={() => { setEditingUser(undefined); setShowModal(true); }}>
                        + Add User
                    </button>
                </div>
            ) : (
                <div className="table-container">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Email</th>
                                <th>Name</th>
                                <th>Role</th>
                                <th>Status</th>
                                <th>Last Login</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {users.map((u) => (
                                <tr key={u.id}>
                                    <td>{u.email}</td>
                                    <td>{u.display_name}</td>
                                    <td>{ROLE_LABELS[u.role] || u.role}</td>
                                    <td>
                                        <span className={`status-badge ${u.enabled ? "status-ok" : "status-disabled"}`}>
                                            {u.enabled ? "Active" : "Disabled"}
                                        </span>
                                    </td>
                                    <td>{u.last_login ? new Date(u.last_login).toLocaleDateString() : "Never"}</td>
                                    <td>
                                        <button className="btn btn-sm" onClick={() => { setEditingUser(u); setShowModal(true); }}>
                                            Edit
                                        </button>
                                        <button className="btn btn-sm" onClick={() => handleToggle(u)}>
                                            {u.enabled ? "Disable" : "Enable"}
                                        </button>
                                        <button className="btn btn-sm btn-danger" onClick={() => handleDelete(u)}>
                                            Delete
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {showModal && (
                <UserModal
                    user={editingUser}
                    onSave={() => { setShowModal(false); setEditingUser(undefined); loadData(); showToast(editingUser ? "User updated" : "User created", "success"); }}
                    onCancel={() => { setShowModal(false); setEditingUser(undefined); }}
                />
            )}
        </>
    );
}

function UserModal({ user, onSave, onCancel }: { user?: UserData; onSave: () => void; onCancel: () => void }) {
    const [email, setEmail] = useState(user?.email ?? "");
    const [displayName, setDisplayName] = useState(user?.display_name ?? "");
    const [password, setPassword] = useState("");
    const [role, setRole] = useState(user?.role ?? "readonly");
    const [error, setError] = useState<string | null>(null);
    const [saving, setSaving] = useState(false);

    const handleSave = async () => {
        if (!email.trim() || !displayName.trim()) { setError("Email and name required"); return; }
        if (!user && !password) { setError("Password required for new user"); return; }

        setSaving(true);
        setError(null);
        try {
            if (user) {
                await usersApi.update(user.id, { display_name: displayName, role });
            } else {
                await usersApi.create({ email, display_name: displayName, password, role });
            }
            onSave();
        } catch (e: any) {
            setError(e.message || "Save failed");
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="modal-overlay" onClick={onCancel}>
            <div className="modal" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>{user ? "Edit User" : "New User"}</h2>
                    <button className="modal-close" onClick={onCancel}>&times;</button>
                </div>
                <div className="modal-body">
                    {error && <div className="alert alert-error">{error}</div>}
                    <div className="form-group">
                        <label>Email *</label>
                        <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} disabled={!!user} />
                    </div>
                    <div className="form-group">
                        <label>Display Name *</label>
                        <input value={displayName} onChange={(e) => setDisplayName(e.target.value)} />
                    </div>
                    {!user && (
                        <div className="form-group">
                            <label>Password *</label>
                            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
                        </div>
                    )}
                    <div className="form-group">
                        <label>Role</label>
                        <select value={role} onChange={(e) => setRole(e.target.value)}>
                            <option value="readonly">Read Only</option>
                            <option value="operator">Operator</option>
                            <option value="site_admin">Site Admin</option>
                            <option value="company_admin">Company Admin</option>
                            <option value="global_admin">Global Admin</option>
                        </select>
                    </div>
                </div>
                <div className="modal-footer">
                    <button className="btn" onClick={onCancel} disabled={saving}>Cancel</button>
                    <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
                        {saving ? "Saving..." : user ? "Update" : "Create"}
                    </button>
                </div>
            </div>
        </div>
    );
}
