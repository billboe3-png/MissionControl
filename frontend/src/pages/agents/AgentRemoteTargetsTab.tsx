import { useState, useEffect } from "react";
import LoadingButton from "../../components/common/LoadingButton";
import StatusBadge from "../../components/common/StatusBadge";
import {
    agentRemoteTargetApi,
    RemoteTarget,
    RemoteTargetCreate,
    RemoteInventory,
} from "../../services/agentRemoteTarget";

interface Props {
    agentId: number;
}

const PROTOCOL_DEFAULTS: Record<string, number> = {
    psremoting: 5985,
    ssh: 22,
    winrm: 5985,
};

function formatBytes(mb: number): string {
    if (mb >= 1024) return `${(mb / 1024).toFixed(1)} GB`;
    return `${mb} MB`;
}

function formatUptime(seconds: number): string {
    if (!seconds) return "—";
    const d = Math.floor(seconds / 86400);
    const h = Math.floor((seconds % 86400) / 3600);
    if (d > 0) return `${d}d ${h}h`;
    return `${h}h`;
}

const vmStateColors: Record<string, "healthy" | "warning" | "error" | "neutral"> = {
    running: "healthy",
    stopped: "error",
    paused: "warning",
    saved: "neutral",
};

function TargetInventory({ inventory }: { inventory: Record<string, unknown> }) {
    const [open, setOpen] = useState(false);
    const system = inventory.system as Record<string, unknown> | undefined;
    const hyperv = inventory.hyperv as Record<string, unknown> | undefined;
    const services = inventory.services as Array<Record<string, unknown>> | undefined;

    return (
        <div className="target-inventory" style={{ marginTop: 8 }}>
            <button className="btn btn-sm btn-secondary" onClick={() => setOpen(!open)}>
                {open ? "Hide Details" : "Show Details"}
            </button>
            {open && (
                <div style={{ marginTop: 8 }}>
                    {system && (
                        <div className="card" style={{ padding: 12, marginBottom: 8 }}>
                            <h5 style={{ margin: "0 0 8px" }}>System</h5>
                            <div className="detail-grid">
                                <div><strong>OS:</strong> {(system.os as string) || "—"}</div>
                                <div><strong>Hostname:</strong> {(system.hostname as string) || "—"}</div>
                                <div><strong>CPU:</strong> {(system.cpu_percent as number)?.toFixed(1) ?? "—"}%</div>
                                <div><strong>Memory:</strong> {(system.memory_percent as number)?.toFixed(1) ?? "—"}% ({formatBytes((system.memory_used_mb as number) ?? 0)} / {formatBytes((system.memory_total_mb as number) ?? 0)})</div>
                                {system.uptime != null && <div><strong>Uptime:</strong> {formatUptime(system.uptime as number)}</div>}
                                {system.os_version ? <div><strong>Version:</strong> {String(system.os_version)}</div> : null}
                            </div>
                        </div>
                    )}
                    {hyperv && (
                        <div className="card" style={{ padding: 12, marginBottom: 8 }}>
                            <h5 style={{ margin: "0 0 8px" }}>Hyper-V ({(hyperv.vm_count as number) ?? 0} VMs)</h5>
                            {Array.isArray(hyperv.vms) && hyperv.vms.length > 0 ? (
                                <div className="data-table-wrapper">
                                    <table className="data-table">
                                        <thead>
                                            <tr>
                                                <th>Name</th>
                                                <th>State</th>
                                                <th>CPU</th>
                                                <th>Memory</th>
                                                <th>Uptime</th>
                                                <th>Generation</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {(hyperv.vms as Array<Record<string, unknown>>).map((vm, i) => (
                                                <tr key={(vm.vm_id as string) || i}>
                                                    <td className="font-medium">{vm.name as string}</td>
                                                    <td>
                                                        <StatusBadge
                                                            status={vmStateColors[(vm.state as string)] ?? "neutral"}
                                                            label={vm.state as string}
                                                        />
                                                    </td>
                                                    <td>{vm.cpu_usage != null ? `${vm.cpu_usage}%` : "—"}</td>
                                                    <td>{formatBytes((vm.memory_mb as number) ?? 0)}</td>
                                                    <td>{formatUptime((vm.uptime_seconds as number) ?? 0)}</td>
                                                    <td>{vm.generation != null ? String(vm.generation) : "—"}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            ) : (
                                <p style={{ color: "var(--text-muted)", margin: 0 }}>No VMs found.</p>
                            )}
                            {Array.isArray(hyperv.switches) && hyperv.switches.length > 0 && (
                                <>
                                    <h5 style={{ margin: "12px 0 8px" }}>Virtual Switches ({hyperv.switches.length})</h5>
                                    <div className="data-table-wrapper">
                                        <table className="data-table">
                                            <thead>
                                                <tr>
                                                    <th>Name</th>
                                                    <th>Type</th>
                                                    <th>NetAdapter</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {(hyperv.switches as Array<Record<string, unknown>>).map((sw, i) => (
                                                    <tr key={(sw.name as string) || i}>
                                                        <td>{sw.name as string}</td>
                                                        <td><span className="badge badge-info">{sw.type as string}</span></td>
                                                        <td>{(sw.net_adapter as string) || "—"}</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </>
                            )}
                        </div>
                    )}
                    {Array.isArray(services) && services.length > 0 && (
                        <div className="card" style={{ padding: 12 }}>
                            <h5 style={{ margin: "0 0 8px" }}>Services ({services.length})</h5>
                            <div style={{ maxHeight: 200, overflow: "auto" }}>
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>Name</th>
                                            <th>Status</th>
                                            <th>Start Type</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {services.map((svc, i) => (
                                            <tr key={(svc.name as string) || i}>
                                                <td>{svc.name as string}</td>
                                                <td>{svc.status as string}</td>
                                                <td>{svc.start_type as string}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}
                    {!system && !hyperv && (!services || services.length === 0) && (
                        <p style={{ color: "var(--text-muted)", marginTop: 8 }}>No inventory data collected yet.</p>
                    )}
                </div>
            )}
        </div>
    );
}

export default function AgentRemoteTargetsTab({ agentId }: Props) {
    const [targets, setTargets] = useState<RemoteTarget[]>([]);
    const [inventory, setInventory] = useState<RemoteInventory | null>(null);
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
            const [targetsData, inventoryData] = await Promise.all([
                agentRemoteTargetApi.listTargets(agentId),
                agentRemoteTargetApi.getRemoteInventory(agentId).catch(() => null),
            ]);
            setTargets(targetsData);
            setInventory(inventoryData);
        } catch (e) {
            setError(e instanceof Error ? e.message : "Failed to load targets");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (agentId) load();
    }, [agentId]);

    useEffect(() => {
        const interval = setInterval(() => {
            if (agentId) {
                agentRemoteTargetApi.getRemoteInventory(agentId)
                    .then(setInventory)
                    .catch(() => {});
            }
        }, 30000);
        return () => clearInterval(interval);
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

    const getInventoryForTarget = (targetId: number): Record<string, unknown> | null => {
        if (!inventory?.remote_targets) return null;
        return inventory.remote_targets[`target-${targetId}`]?.inventory as Record<string, unknown> ?? null;
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
                            {targets.map((t) => {
                                const inv = getInventoryForTarget(t.id);
                                const hyperv = inv?.hyperv as Record<string, unknown> | undefined;
                                return (
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
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            )}

            {targets.length > 0 && (
                <div style={{ marginTop: 16 }}>
                    {targets.map((t) => {
                        const inv = getInventoryForTarget(t.id);
                        if (!inv) return null;
                        return (
                            <div key={t.id} style={{ marginBottom: 16 }}>
                                <h4 style={{ marginBottom: 4 }}>{t.name} — Collected Inventory</h4>
                                <TargetInventory inventory={inv} />
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
