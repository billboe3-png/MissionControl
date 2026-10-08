import { useState, useEffect } from "react";
import LoadingButton from "../../components/common/LoadingButton";
import StatusBadge from "../../components/common/StatusBadge";
import { formatDateTime } from "../../utils/dateFormat";
import {
    agentRemoteTargetApi,
    RemoteTarget,
    RemoteTargetCreate,
} from "../../services/agentRemoteTarget";
import { agentsApi, Agent } from "../../services/agents";

interface Props {
    agentId: number;
}

const PROTOCOL_DEFAULTS: Record<string, number> = {
    psremoting: 5985,
    ssh: 22,
    winrm: 5985,
};

const TARGET_PLUGIN_OPTIONS = [
    { label: "Active Directory", value: "active_directory" },
    { label: "Docker", value: "docker" },
    { label: "Hyper-V", value: "hyperv" },
    { label: "Linux", value: "linux" },
    { label: "Microsoft 365", value: "microsoft_365" },
    { label: "MikroTik", value: "mikrotik" },
    { label: "Veeam", value: "veeam" },
    { label: "Windows", value: "windows" },
    { label: "Windows Docker", value: "windows_docker" },
    { label: "Zabbix", value: "zabbix" },
];

const selectedPlugins = (raw?: string | null): string[] =>
    (raw || "")
        .split(",")
        .map((p) => p.trim())
        .filter(Boolean);

const DB_TYPE_OPTIONS = [
    { label: "Auto detect", value: "auto" },
    { label: "PostgreSQL", value: "postgresql" },
    { label: "MSSQL", value: "mssql" },
];

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
        db_type: "auto",
    });
    const [saving, setSaving] = useState(false);
    const [testing, setTesting] = useState<number | null>(null);

    const [agents, setAgents] = useState<Agent[]>([]);
    const [movingTarget, setMovingTarget] = useState<RemoteTarget | null>(null);
    const [moveNewAgentId, setMoveNewAgentId] = useState("");
    const [moveProfiles, setMoveProfiles] = useState(true);
    const [moving, setMoving] = useState(false);

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
        agentsApi
            .list()
            .then((r) => setAgents(r.items || []))
            .catch(() => setAgents([]));
    }, [agentId]);

    const handleProtocolChange = (protocol: string) => {
        setForm((f) => ({
            ...f,
            protocol,
            port: PROTOCOL_DEFAULTS[protocol] || 5985,
        }));
    };

    const handlePluginToggle = (plugin: string) => {
        setForm((f) => {
            const current = selectedPlugins(f.target_plugins);
            const next = current.includes(plugin)
                ? current.filter((p) => p !== plugin)
                : [...current, plugin];
            return { ...f, target_plugins: next.join(",") };
        });
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
            setForm({ name: "", hostname: "", protocol: "psremoting", username: "", password: "", target_plugins: "", db_type: "auto" });
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
            target_plugins: target.target_plugins || "",
            db_type: target.db_type || "auto",
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

    const handleMove = async () => {
        if (!movingTarget || !moveNewAgentId) return;
        setMoving(true);
        setError(null);
        try {
            await agentRemoteTargetApi.moveTarget(agentId, movingTarget.id, {
                new_agent_id: Number(moveNewAgentId),
                move_profiles: moveProfiles,
            });
            setMovingTarget(null);
            setMoveNewAgentId("");
            setMoveProfiles(true);
            await load();
        } catch (e) {
            setError(e instanceof Error ? e.message : "Move failed");
        } finally {
            setMoving(false);
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
                        setForm({ name: "", hostname: "", protocol: "psremoting", username: "", password: "", target_plugins: "", db_type: "auto" });
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
                            <label>{form.protocol === "ssh" ? "Password (preferred)" : "Password"}</label>
                            <input
                                type="password"
                                value={form.password || ""}
                                onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
                                placeholder={editingTarget ? "Leave blank to keep current" : ""}
                            />
                        </div>
                        <div className="form-row">
                            <label>SSH Key</label>
                            <textarea
                                value={form.ssh_key || ""}
                                onChange={(e) => setForm((f) => ({ ...f, ssh_key: e.target.value }))}
                                placeholder="Leave empty unless password auth is unavailable"
                                rows={3}
                            />
                            <small className="form-hint">
                                Only used if no password is configured.
                            </small>
                        </div>
                        <div className="form-row">
                            <label>Tags</label>
                            <input
                                value={form.tags || ""}
                                onChange={(e) => setForm((f) => ({ ...f, tags: e.target.value }))}
                                placeholder="e.g. hyper-v, production"
                            />
                        </div>
                        <div className="form-row">
                            <label>Plugins</label>
                            <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
                                {TARGET_PLUGIN_OPTIONS.map((p) => (
                                    <label key={p.value} style={{ display: "flex", alignItems: "center", gap: 5 }}>
                                        <input
                                            type="checkbox"
                                            checked={selectedPlugins(form.target_plugins).includes(p.value)}
                                            onChange={() => handlePluginToggle(p.value)}
                                        />
                                        <span>{p.label}</span>
                                    </label>
                                ))}
                            </div>
                            <small className="form-hint">
                                Controls which plugins collect data through this target.
                            </small>
                        </div>
                        {selectedPlugins(form.target_plugins).includes("veeam") && (
                            <div className="form-row">
                                <label>Veeam Database</label>
                                <select
                                    value={form.db_type || "auto"}
                                    onChange={(e) => setForm((f) => ({ ...f, db_type: e.target.value }))}
                                >
                                    {DB_TYPE_OPTIONS.map((o) => (
                                        <option key={o.value} value={o.value}>
                                            {o.label}
                                        </option>
                                    ))}
                                </select>
                                <small className="form-hint">
                                    Backing database of the Veeam server. Auto-detect probes the host
                                    (used when SQLCMD and psql.exe are both present).
                                </small>
                            </div>
                        )}
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

            {movingTarget && (
                <div className="target-form card">
                    <h4>Move '{movingTarget.name}' to another agent</h4>
                    <div className="form-grid">
                        <div className="form-row">
                            <label>Destination agent</label>
                            <select
                                value={moveNewAgentId}
                                onChange={(e) => setMoveNewAgentId(e.target.value)}
                            >
                                <option value="">Select an agent...</option>
                                {agents
                                    .filter((a) => a.id !== agentId)
                                    .map((a) => (
                                        <option key={a.id} value={a.id}>
                                            {a.name} ({a.status})
                                        </option>
                                    ))}
                            </select>
                            <small className="form-hint">
                                The target moves to the selected agent and its plugins are
                                enabled there for collection.
                            </small>
                        </div>
                        <div className="form-row">
                            <label
                                style={{ display: "flex", alignItems: "center", gap: 6 }}
                            >
                                <input
                                    type="checkbox"
                                    checked={moveProfiles}
                                    onChange={(e) => setMoveProfiles(e.target.checked)}
                                />
                                <span>Also move matching integration profiles</span>
                            </label>
                            <small className="form-hint">
                                Moves profiles whose SSH host matches this target's hostname
                                so credentials follow the target.
                            </small>
                        </div>
                    </div>
                    <div className="form-actions">
                        <LoadingButton
                            loading={moving}
                            className="btn btn-primary"
                            onClick={handleMove}
                        >
                            Move
                        </LoadingButton>
                        <button
                            className="btn btn-secondary"
                            onClick={() => setMovingTarget(null)}
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
                                <th>Plugins</th>
                                <th>Veeam DB</th>
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
                                        <td className="muted">
                                            {selectedPlugins(t.target_plugins).join(", ") || "—"}
                                        </td>
                                        <td className="muted">
                                            {selectedPlugins(t.target_plugins).includes("veeam")
                                                ? (t.db_type || "auto")
                                                : "—"}
                                        </td>
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
                                                ? formatDateTime(t.last_collected_at)
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
                                                    className="btn btn-sm btn-secondary"
                                                    onClick={() => {
                                                        setMovingTarget(t);
                                                        setMoveNewAgentId("");
                                                        setMoveProfiles(true);
                                                    }}
                                                >
                                                    Move
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
