import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import LoadingButton from "../../components/common/LoadingButton";
import StatusBadge from "../../components/common/StatusBadge";
import EmptyState from "../../components/common/EmptyState";
import { proxmoxApi, ProxmoxLxc, ProxmoxLxcTemplate } from "../../services/proxmox";

function formatUptime(seconds: number): string {
    if (seconds === 0) return "—";
    const d = Math.floor(seconds / 86400);
    const h = Math.floor((seconds % 86400) / 3600);
    if (d > 0) return `${d}d ${h}h`;
    return `${h}h`;
}

function formatBytes(mb: number): string {
    if (mb >= 1024) return `${(mb / 1024).toFixed(1)} GB`;
    return `${mb} MB`;
}

function formatSize(bytes: number): string {
    if (bytes === 0) return "—";
    if (bytes >= 1073741824) return `${(bytes / 1073741824).toFixed(1)} GB`;
    if (bytes >= 1048576) return `${(bytes / 1048576).toFixed(0)} MB`;
    return `${(bytes / 1024).toFixed(0)} KB`;
}

const stateColors: Record<string, "healthy" | "warning" | "error" | "neutral"> = {
    running: "healthy",
    stopped: "error",
    paused: "warning",
};

export default function ContainersPage() {
    const [containers, setContainers] = useState<ProxmoxLxc[]>([]);
    const [templates, setTemplates] = useState<ProxmoxLxcTemplate[]>([]);
    const [nodes, setNodes] = useState<string[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [actionId, setActionId] = useState<string | null>(null);
    const [showCreate, setShowCreate] = useState(false);
    const [creating, setCreating] = useState(false);
    const [createError, setCreateError] = useState<string | null>(null);

    const [form, setForm] = useState({
        node: "",
        ostemplate: "",
        hostname: "mission-control",
        cores: 2,
        memory: 4096,
        disk: 8,
        storage: "local-lvm",
        password: "",
        net_bridge: "vmbr0",
        net_ip: "dhcp",
        nesting: true,
    });

    const load = async () => {
        try {
            const [lxcList, tmplList, nodeList] = await Promise.all([
                proxmoxApi.listLxc(),
                proxmoxApi.listLxcTemplates(),
                proxmoxApi.listNodes(),
            ]);
            setContainers(lxcList);
            setTemplates(tmplList);
            setNodes(nodeList.map((n) => n.name));
            if (nodeList.length > 0 && !form.node) {
                setForm((f) => ({ ...f, node: nodeList[0].name }));
            }
        } catch (e) {
            setError(e instanceof Error ? e.message : "Failed to load");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { load(); }, []);

    const doAction = async (vmId: string, action: () => Promise<unknown>) => {
        setActionId(vmId);
        try {
            await action();
            await load();
        } catch (e) {
            setError(e instanceof Error ? e.message : "Action failed");
        } finally {
            setActionId(null);
        }
    };

    const handleCreate = async () => {
        if (!form.ostemplate) {
            setCreateError("Please select a template");
            return;
        }
        setCreating(true);
        setCreateError(null);
        try {
            const result = await proxmoxApi.createLxc({
                node: form.node,
                ostemplate: form.ostemplate,
                hostname: form.hostname,
                cores: form.cores,
                memory: form.memory,
                disk: form.disk,
                storage: form.storage,
                password: form.password || undefined,
                net_bridge: form.net_bridge,
                net_ip: form.net_ip,
                nesting: form.nesting,
            });
            if (result.success) {
                setShowCreate(false);
                setForm({
                    node: nodes[0] || "",
                    ostemplate: "",
                    hostname: "mission-control",
                    cores: 2,
                    memory: 4096,
                    disk: 8,
                    storage: "local-lvm",
                    password: "",
                    net_bridge: "vmbr0",
                    net_ip: "dhcp",
                    nesting: true,
                });
                await load();
            } else {
                setCreateError(result.error || "Failed to create container");
            }
        } catch (e) {
            setCreateError(e instanceof Error ? e.message : "Failed to create container");
        } finally {
            setCreating(false);
        }
    };

    const handleDelete = async (vmId: string, name: string) => {
        if (!window.confirm(`Delete container "${name}" (${vmId})? This cannot be undone.`)) return;
        setActionId(vmId);
        try {
            await proxmoxApi.deleteLxc(vmId);
            await load();
        } catch (e) {
            setError(e instanceof Error ? e.message : "Delete failed");
        } finally {
            setActionId(null);
        }
    };

    const handleClone = async (vmId: string) => {
        const newHostname = window.prompt(`Clone container ${vmId} — enter hostname (optional):`);
        if (newHostname === null) return;
        setActionId(vmId);
        try {
            await proxmoxApi.cloneLxc(vmId, undefined, newHostname || undefined);
            await load();
        } catch (e) {
            setError(e instanceof Error ? e.message : "Clone failed");
        } finally {
            setActionId(null);
        }
    };

    if (loading) return <div className="loading-bar" />;

    return (
        <>
            <PageHeader
                title="LXC Containers"
                subtitle="Manage Proxmox LXC containers"
                actions={
                    <button className="btn btn-primary" onClick={() => setShowCreate(!showCreate)}>
                        {showCreate ? "Cancel" : "New Container"}
                    </button>
                }
            />

            {error && (
                <div className="error-banner">
                    {error}
                    <button className="btn btn-link" onClick={() => setError(null)}>Dismiss</button>
                </div>
            )}

            {showCreate && (
                <div className="card" style={{ marginBottom: 24, padding: 20 }}>
                    <h3 style={{ marginTop: 0, marginBottom: 16 }}>Create LXC Container</h3>
                    {createError && <div className="alert alert-error" style={{ marginBottom: 12 }}>{createError}</div>}

                    <div className="form-row">
                        <div className="form-group">
                            <label>Node *</label>
                            <select className="form-select" value={form.node} onChange={(e) => setForm({ ...form, node: e.target.value })}>
                                {nodes.map((n) => <option key={n} value={n}>{n}</option>)}
                            </select>
                        </div>
                        <div className="form-group" style={{ flex: 2 }}>
                            <label>Template *</label>
                            <select className="form-select" value={form.ostemplate} onChange={(e) => setForm({ ...form, ostemplate: e.target.value })}>
                                <option value="">Select a template...</option>
                                {templates.map((t) => (
                                    <option key={t.id} value={t.file}>
                                        {t.name} ({formatSize(t.size_bytes)})
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label>Hostname</label>
                            <input className="form-input" value={form.hostname} onChange={(e) => setForm({ ...form, hostname: e.target.value })} />
                        </div>
                        <div className="form-group">
                            <label>Storage</label>
                            <input className="form-input" value={form.storage} onChange={(e) => setForm({ ...form, storage: e.target.value })} />
                        </div>
                        <div className="form-group">
                            <label>Password (root)</label>
                            <input className="form-input" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} placeholder="Auto-generated if empty" />
                        </div>
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label>CPU Cores</label>
                            <input className="form-input" type="number" min={1} max={32} value={form.cores} onChange={(e) => setForm({ ...form, cores: Number(e.target.value) })} />
                        </div>
                        <div className="form-group">
                            <label>Memory (MB)</label>
                            <input className="form-input" type="number" min={256} step={256} value={form.memory} onChange={(e) => setForm({ ...form, memory: Number(e.target.value) })} />
                        </div>
                        <div className="form-group">
                            <label>Disk (GB)</label>
                            <input className="form-input" type="number" min={2} value={form.disk} onChange={(e) => setForm({ ...form, disk: Number(e.target.value) })} />
                        </div>
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label>Network Bridge</label>
                            <input className="form-input" value={form.net_bridge} onChange={(e) => setForm({ ...form, net_bridge: e.target.value })} />
                        </div>
                        <div className="form-group">
                            <label>IP Config</label>
                            <input className="form-input" value={form.net_ip} onChange={(e) => setForm({ ...form, net_ip: e.target.value })} placeholder="dhcp or 192.168.1.100/24" />
                        </div>
                        <div className="form-group" style={{ flex: 0, minWidth: 140 }}>
                            <label>&nbsp;</label>
                            <label style={{ display: "flex", alignItems: "center", gap: 6, cursor: "pointer", padding: "8px 0" }}>
                                <input type="checkbox" checked={form.nesting} onChange={(e) => setForm({ ...form, nesting: e.target.checked })} />
                                Docker (nesting)
                            </label>
                        </div>
                    </div>

                    <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                        <LoadingButton loading={creating} className="btn btn-primary" onClick={handleCreate}>
                            Create Container
                        </LoadingButton>
                        <button className="btn" onClick={() => setShowCreate(false)}>Cancel</button>
                    </div>
                </div>
            )}

            {containers.length === 0 ? (
                <EmptyState icon="📦" title="No containers" description="No LXC containers found in the cluster." />
            ) : (
                <div className="proxmox-lxc-grid">
                    {containers.map((lxc) => (
                        <div key={lxc.id} className={`proxmox-lxc-card state-${lxc.state}`}>
                            <div className="proxmox-lxc-header">
                                <h3>{lxc.name}</h3>
                                <StatusBadge status={stateColors[lxc.state] ?? "neutral"} label={lxc.state} />
                            </div>
                            <div className="proxmox-lxc-meta">
                                <span>Node: {lxc.host_server}</span>
                                <span>ID: {lxc.id}</span>
                                {lxc.guest_os && <span>OS: {lxc.guest_os}</span>}
                                <span>CPU: {lxc.cpu_count} cores ({lxc.cpu_usage_percent}%)</span>
                                <span>RAM: {formatBytes(lxc.memory_assigned_mb)}</span>
                                <span>Uptime: {formatUptime(lxc.uptime_seconds)}</span>
                            </div>
                            <div className="proxmox-lxc-actions">
                                {lxc.state !== "running" && (
                                    <LoadingButton
                                        loading={actionId === lxc.id}
                                        className="btn btn-primary btn-sm"
                                        onClick={() => doAction(lxc.id, () => proxmoxApi.startLxc(lxc.id))}
                                    >
                                        Start
                                    </LoadingButton>
                                )}
                                {lxc.state === "running" && (
                                    <LoadingButton
                                        loading={actionId === lxc.id}
                                        className="btn btn-danger btn-sm"
                                        onClick={() => doAction(lxc.id, () => proxmoxApi.stopLxc(lxc.id))}
                                    >
                                        Stop
                                    </LoadingButton>
                                )}
                                <button
                                    className="btn btn-sm"
                                    disabled={actionId === lxc.id}
                                    onClick={() => handleClone(lxc.id)}
                                >
                                    Clone
                                </button>
                                <button
                                    className="btn btn-sm btn-danger"
                                    disabled={actionId === lxc.id || lxc.state === "running"}
                                    onClick={() => handleDelete(lxc.id, lxc.name)}
                                >
                                    Delete
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </>
    );
}
