import { useState, useEffect } from "react";
import LoadingButton from "../../components/common/LoadingButton";
import StatusBadge from "../../components/common/StatusBadge";
import {
    agentRemoteTargetApi,
    RemoteTarget,
    RemoteTargetCreate,
} from "../../services/agentRemoteTarget";

interface Props {
    agentId: number;
}

const PROTOCOL_DEFAULTS: Record<string, number> = {
    psremoting: 5985,
    ssh: 22,
    winrm: 5985,
};

export default function AgentRemoteTargetsTab({ agentId }: Props) {
    const [targets, setTargets] = useState<RemoteTarget[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const [showForm, setShowForm] = useState(false);
    const [editingTarget, setEditingTarget] = useState<RemoteTarget | null>(null);
    const [form, setForm] = useState<RemoteTargetCreate>({
        name: "",
        hostname: "",
        protocol: "psremoting",
        username: "",
        password: "",
    });
    const [saving, setSaving] = useState(false);
    const [testing, setTesting] = useState<number | null>(null);

    const load = async () => {
        try {
            const targetsData = await agentRemoteTargetApi.listTargets(agentId);
            setTargets(targetsData);
        } catch (e) {
            setError(e instanceof Error ? e.message : "Failed to load targets");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (agentId) load();
    }, [agentId]);

    const handleProtocolChange = (protocol: string) => {
        setForm((f) => ({
            ...f,
            protocol,
            port: PROTOCOL_DEFAULTS[protocol] || 5985,
        }));
    };

    const handleSave = async () => {
        if (!form.name.trim() || !form.hostname.trim() || !form.username.trim()) {
            setError("Name, hostname, and username are required");
            return;
        }
        setSaving(true);
        setError(null);
        try {
            if (editingTarget) {
                await agentRemoteTargetApi.updateTarget(agentId, editingTarget.id, form);
            } else {
                await agentRemoteTargetApi.createTarget(agentId, form);
            }
            setShowForm(false);
            setEditingTarget(null);
            setForm({ name: "", hostname: "", protocol: "psremoting", username: "", password: "" });
            await load();
        } catch (e) {
            setError(e instanceof Error ? e.message : "Save failed");
        } finally {
            setSaving(false);
        }
    };

    const handleEdit = (target: RemoteTarget) => {
        setEditingTarget(target);
        setForm({
            name: target.name,
            hostname: target.hostname,
            protocol: target.protocol,
            port: target.port,
            username: target.username,
            password: "",
        });
        setShowForm(true);
    };

    const handleDelete = async (target: RemoteTarget) => {
        if (!window.confirm(`Delete target '${target.name}'?`)) return;
        try {
            await agentRemoteTargetApi.deleteTarget(agentId, target.id);
            await load();
        } catch (e) {
            setError(e instanceof Error ? e.message : "Delete failed");
        }
    };

    const handleTest = async (target: RemoteTarget) => {
        setTesting(target.id);
        try {
            const result = await agentRemoteTargetApi.testTarget(agentId, target.id);
            alert(result.connected ? `Connected: ${result.message}` : `Failed: ${result.error}`);
        } catch (e) {
            setError(e instanceof Error ? e.message : "Test failed");
        } finally {
            setTesting(null);
        }
    };

    const handleToggle = async (target: RemoteTarget) => {
        try {
            await agentRemoteTargetApi.updateTarget(agentId, target.id, {
                enabled: !target.enabled,
            });
            await load();
        } catch (e) {
            setError(e instanceof Error ? e.message : "Toggle failed");
        }
    };

    if (loading) return <div className="loading-bar" />;

    return (
        <div className="agent-remote-targets">
            <div className="section-header">
                <h3>Remote Targets</h3>
                <button
                    className="btn btn-primary btn-sm"
                    onClick={() => {
                        setEditingTarget(null);
                        setForm({ name: "", hostname: "", protocol: "psremoting", username: "", password: "" });
                        setShowForm(!showForm);
                    }}
                >
                    {showForm ? "Cancel" : "+ Add Target"}
                </button>
            </div>

            {error && (
                <div className="error-banner">
                    {error}
                    <button className="btn btn-link" onClick={() => setError(null)}>
                        Dismiss
                    </button>
                </div>
            )}

            {showForm && (
                <div className="target-form card">
                    <h4>{editingTarget ? "Edit Target" : "New Target"}</h4>
                    <div className="form-grid">
                        <div className="form-row">
                            <label>Name</label>
                            <input
                                value={form.name}
                                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                                placeholder="e.g. Hyper-V Host 01"
                            />
                        </div>
                        <div className="form-row">
                            <label>Hostname / IP</label>
                            <input
                                value={form.hostname}
                                onChange={(e) => setForm((f) => ({ ...f, hostname: e.target.value }))}
                                placeholder="e.g. 192.168.1.50"
                            />
                        </div>
                        <div className="form-row">
                            <label>Protocol</label>
                            <select
                                value={form.protocol}
                                onChange={(e) => handleProtocolChange(e.target.value)}
                            >
                                <option value="psremoting">PowerShell Remoting</option>
                                <option value="ssh">SSH</option>
                                <option value="winrm">WinRM</option>
                            </select>
                        </div>
                        <div className="form-row">
                            <label>Port</label>
                            <input
                                type="number"
                                value={form.port || PROTOCOL_DEFAULTS[form.protocol] || 5985}
                                onChange={(e) => setForm((f) => ({ ...f, port: parseInt(e.target.value) || 5985 }))}
                            />
                        </div>
                        <div className="form-row">
                            <label>Username</label>
                            <input
                                value={form.username}
                                onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))}
                                placeholder="e.g. admin"
                            />
                        </div>
                        <div className="form-row">
                            <label>{form.protocol === "ssh" ? "SSH Key (optional)" : "Password"}</label>
                            {form.protocol === "ssh" ? (
                                <textarea
                                    value={form.ssh_key || ""}
                                    onChange={(e) => setForm((f) => ({ ...f, ssh_key: e.target.value }))}
                                    placeholder="Paste SSH private key (optional)"
                                    rows={3}
                                />
                            ) : (
                                <input
                                    type="password"
                                    value={form.password || ""}
                                    onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
                                    placeholder={editingTarget ? "Leave blank to keep current" : ""}
                                />
                            )}
                        </div>
                        <div className="form-row">
                            <label>Tags</label>
                            <input
                                value={form.tags || ""}
                                onChange={(e) => setForm((f) => ({ ...f, tags: e.target.value }))}
                                placeholder="e.g. hyper-v, production"
                            />
                        </div>
                    </div>
                    <div className="form-actions">
                        <LoadingButton
                            loading={saving}
                            className="btn btn-primary"
                            onClick={handleSave}
                        >
                            {editingTarget ? "Update" : "Create"}
                        </LoadingButton>
                        <button
                            className="btn btn-secondary"
                            onClick={() => { setShowForm(false); setEditingTarget(null); }}
                        >
                            Cancel
                        </button>
                    </div>
                </div>
            )}

            {targets.length === 0 && !showForm ? (
                <div className="empty-state">
                    <p>No remote targets configured.</p>
                    <p>Remote targets let this agent relay data from machines inside its network.</p>
                </div>
            ) : (
                <div className="data-table-wrapper">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Hostname</th>
                                <th>Protocol</th>
                                <th>Port</th>
                                <th>Username</th>
                                <th>Status</th>
                                <th>Last Collected</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {targets.map((t) => (
                            <tr key={t.id} className={!t.enabled ? "row-disabled" : ""}>
                                        <td className="font-medium">{t.name}</td>
                                        <td><code>{t.hostname}</code></td>
                                        <td>
                                            <span className="badge badge-info">{t.protocol}</span>
                                        </td>
                                        <td>{t.port}</td>
                                        <td>{t.username}</td>
                                        <td>
                                            <StatusBadge
                                                status={
                                                    t.last_status === "online"
                                                        ? "healthy"
                                                        : t.last_status === "error"
                                                        ? "error"
                                                        : "neutral"
                                                }
                                                label={t.last_status}
                                            />
                                        </td>
                                        <td>
                                            {t.last_collected_at
                                                ? new Date(t.last_collected_at).toLocaleString()
                                                : "Never"}
                                        </td>
                                        <td>
                                            <div className="action-buttons">
                                                <button
                                                    className="btn btn-sm btn-secondary"
                                                    onClick={() => handleTest(t)}
                                                    disabled={testing === t.id}
                                                >
                                                    {testing === t.id ? "Testing..." : "Test"}
                                                </button>
                                                <button
                                                    className="btn btn-sm btn-secondary"
                                                    onClick={() => handleToggle(t)}
                                                >
                                                    {t.enabled ? "Disable" : "Enable"}
                                                </button>
                                                <button
                                                    className="btn btn-sm btn-secondary"
                                                    onClick={() => handleEdit(t)}
                                                >
                                                    Edit
                                                </button>
                                                <button
                                                    className="btn btn-sm btn-danger"
                                                    onClick={() => handleDelete(t)}
                                                >
                                                    Delete
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}
