import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import LoadingButton from "../../components/common/LoadingButton";
import AgentRemoteTargetsTab from "./AgentRemoteTargetsTab";
import { formatDateTime } from "../../utils/dateFormat";
import {
    agentsApi,
    Agent,
    AgentCommand,
    AgentInventory,
} from "../../services/agents";

type Tab =
    | "overview"
    | "performance"
    | "commands"
    | "inventory"
    | "diagnostics"
    | "configuration"
    | "remote_targets"
    | "history";

function formatDuration(ms: number | null): string {
    if (ms == null) return "—";
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
}

function HealthBar({ label, value }: { label: string; value: number | null }) {
    const pct = value ?? 0;
    const color = pct >= 90 ? "#ef4444" : pct >= 70 ? "#f59e0b" : "#22c55e";
    return (
        <div className="agent-health-bar">
            <span className="agent-health-label">{label}</span>
            <div className="agent-health-track">
                <div className="agent-health-fill" style={{ width: `${pct}%`, backgroundColor: color }} />
            </div>
            <span className="agent-health-value">{pct.toFixed(1)}%</span>
        </div>
    );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
    return (
        <div className="agent-section-card" style={{ marginBottom: 16 }}>
            <div className="agent-section-title" style={{ marginBottom: 8 }}>{title}</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>{children}</div>
        </div>
    );
}

function KeyValue({ label, value }: { label: string; value: React.ReactNode }) {
    return (
        <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
            <span style={{ opacity: 0.8 }}>{label}</span>
            <span style={{ fontWeight: 600 }}>{value}</span>
        </div>
    );
}

function ListItems({ items }: { items: Array<Record<string, unknown>> }) {
    if (!items.length) return <div className="empty-text">No items</div>;
    return (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {items.map((item, idx) => (
                <div
                    key={idx}
                    style={{
                        border: "1px solid rgba(255,255,255,0.08)",
                        borderRadius: 8,
                        padding: 10,
                    }}
                >
                    <div style={{ display: "flex", flexDirection: "column", gap: 4, fontSize: 13 }}>
                        {(Object.keys(item) as Array<keyof typeof item>).map((key) => (
                            <div key={String(key)} style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                                <span style={{ opacity: 0.75, textTransform: "capitalize" }}>{String(key)}</span>
                                <span style={{ fontWeight: 500, wordBreak: "break-word" }}>
                                    {typeof item[key] === "object" ? JSON.stringify(item[key]) : String(item[key] ?? "—")}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            ))}
        </div>
    );
}

const TABS: { key: Tab; label: string; icon: string }[] = [
    { key: "overview", label: "Overview", icon: "📋" },
    { key: "performance", label: "Performance", icon: "📊" },
    { key: "commands", label: "Commands", icon: "⚡" },
    { key: "inventory", label: "Inventory", icon: "📦" },
    { key: "diagnostics", label: "Diagnostics", icon: "🔍" },
    { key: "configuration", label: "Configuration", icon: "⚙️" },
    { key: "remote_targets", label: "Remote Targets", icon: "🌐" },
    { key: "history", label: "History", icon: "📜" },
];

function PluginInventory({ inventory }: { inventory: Record<string, unknown> }) {
    const entries = Object.entries(inventory);
    if (!entries.length) return <div className="empty-text">No plugin data collected yet.</div>;

    return (
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {entries.map(([key, value]) => {
                const data = value as Record<string, unknown> | undefined;
                if (!data || typeof data !== "object") return null;

                return (
                    <div key={key} className="agent-section-card">
                        <div className="agent-section-title" style={{ marginBottom: 8, textTransform: "capitalize" }}>
                            {key}
                        </div>
                        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                            {key === "docker" && (
                                <>
                                    {data.available !== undefined && (
                                        <KeyValue label="Available" value={String(data.available)} />
                                    )}
                                    {data.version && <KeyValue label="Version" value={String(data.version)} />}
                                    {data.container_count != null && (
                                        <KeyValue label="Containers" value={String(data.container_count)} />
                                    )}
                                    {data.image_count != null && (
                                        <KeyValue label="Images" value={String(data.image_count)} />
                                    )}
                                    {Array.isArray(data.containers) && data.containers.length > 0 && (
                                        <div>
                                            <div style={{ opacity: 0.85, marginBottom: 6 }}>Containers</div>
                                            <ListItems items={data.containers as Array<Record<string, unknown>>} />
                                        </div>
                                    )}
                                </>
                            )}

                            {key === "hyperv" && (
                                <>
                                    {data.vm_count != null && (
                                        <KeyValue label="VMs" value={String(data.vm_count)} />
                                    )}
                                    {Array.isArray(data.vms) && data.vms.length > 0 && (
                                        <div>
                                            <div style={{ opacity: 0.85, marginBottom: 6 }}>Virtual Machines</div>
                                            <ListItems items={data.vms as Array<Record<string, unknown>>} />
                                        </div>
                                    )}
                                    {Array.isArray(data.switches) && data.switches.length > 0 && (
                                        <div>
                                            <div style={{ opacity: 0.85, marginBottom: 6 }}>Switches</div>
                                            <ListItems items={data.switches as Array<Record<string, unknown>>} />
                                        </div>
                                    )}
                                </>
                            )}

                            {key === "linux" && (
                                <>
                                    {data.distro && <KeyValue label="Distro" value={String(data.distro)} />}
                                    {data.kernel && <KeyValue label="Kernel" value={String(data.kernel)} />}
                                    {Array.isArray(data.systemd_services) && (
                                        <div>
                                            <div style={{ opacity: 0.85, marginBottom: 6 }}>Systemd Services</div>
                                            <ListItems items={data.systemd_services as Array<Record<string, unknown>>} />
                                        </div>
                                    )}
                                    {Array.isArray(data.cron_jobs) && (
                                        <div>
                                            <div style={{ opacity: 0.85, marginBottom: 6 }}>Cron Jobs</div>
                                            <ListItems items={data.cron_jobs.map((name: string) => ({ name }))} />
                                        </div>
                                    )}
                                </>
                            )}

                            {key === "zabbix" && (
                                <>
                                    {data.available !== undefined && (
                                        <KeyValue label="Available" value={String(data.available)} />
                                    )}
                                    {data.host_count != null && (
                                        <KeyValue label="Hosts" value={String(data.host_count)} />
                                    )}
                                    {Array.isArray(data.hosts) && data.hosts.length > 0 && (
                                        <div>
                                            <div style={{ opacity: 0.85, marginBottom: 6 }}>Hosts</div>
                                            <ListItems items={data.hosts as Array<Record<string, unknown>>} />
                                        </div>
                                    )}
                                </>
                            )}

                            {key === "veeam" && (
                                <>
                                    {data.available !== undefined && (
                                        <KeyValue label="Available" value={String(data.available)} />
                                    )}
                                    {(data as Record<string, unknown>).server && (
                                        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                                            <KeyValue label="Server" value={String(((data as Record<string, unknown>).server as Record<string, unknown>).name)} />
                                            <KeyValue label="Version" value={String(((data as Record<string, unknown>).server as Record<string, unknown>).version)} />
                                            <KeyValue label="Server ID" value={String(((data as Record<string, unknown>).server as Record<string, unknown>).server_id)} />
                                        </div>
                                    )}
                                    {Array.isArray(data.jobs) && data.jobs.length > 0 && (
                                        <div>
                                            <div style={{ opacity: 0.85, marginBottom: 6 }}>Jobs</div>
                                            <ListItems items={data.jobs as Array<Record<string, unknown>>} />
                                        </div>
                                    )}
                                    {Array.isArray(data.sessions) && data.sessions.length > 0 && (
                                        <div>
                                            <div style={{ opacity: 0.85, marginBottom: 6 }}>Sessions</div>
                                            <ListItems items={data.sessions as Array<Record<string, unknown>>} />
                                        </div>
                                    )}
                                    {Array.isArray(data.repositories) && data.repositories.length > 0 && (
                                        <div>
                                            <div style={{ opacity: 0.85, marginBottom: 6 }}>Repositories</div>
                                            <ListItems items={data.repositories as Array<Record<string, unknown>>} />
                                        </div>
                                    )}
                                    {Array.isArray(data.managed_servers) && data.managed_servers.length > 0 && (
                                        <div>
                                            <div style={{ opacity: 0.85, marginBottom: 6 }}>Managed Servers</div>
                                            <ListItems items={data.managed_servers as Array<Record<string, unknown>>} />
                                        </div>
                                    )}
                                </>
                            )}

                            {key === "proxmox" && (
                                <>
                                    {data.available !== undefined && (
                                        <KeyValue label="Available" value={String(data.available)} />
                                    )}
                                    {data.cluster_name && <KeyValue label="Cluster" value={String(data.cluster_name)} />}
                                    {data.version && <KeyValue label="Version" value={String(data.version)} />}
                                    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                                        {typeof data.nodes_total === "number" && <KeyValue label="Nodes" value={`${data.nodes_online ?? 0}/${data.nodes_total}`} />}
                                        {typeof data.total_vms === "number" && <KeyValue label="VMs" value={`${data.running_vms ?? 0} running / ${data.total_vms}`} />}
                                        {typeof data.total_lxc === "number" && <KeyValue label="LXCs" value={`${data.running_lxc ?? 0} running / ${data.total_lxc}`} />}
                                        {typeof data.storage_count === "number" && <KeyValue label="Storage" value={String(data.storage_count)} />}
                                    </div>
                                    {Array.isArray(data.nodes) && data.nodes.length > 0 && (
                                        <div>
                                            <div style={{ opacity: 0.85, marginBottom: 6 }}>Nodes</div>
                                            <ListItems items={data.nodes as Array<Record<string, unknown>>} />
                                        </div>
                                    )}
                                    {Array.isArray(data.vms) && data.vms.length > 0 && (
                                        <div>
                                            <div style={{ opacity: 0.85, marginBottom: 6 }}>VMs</div>
                                            <ListItems items={data.vms as Array<Record<string, unknown>>} />
                                        </div>
                                    )}
                                    {Array.isArray(data.lxcs) && data.lxcs.length > 0 && (
                                        <div>
                                            <div style={{ opacity: 0.85, marginBottom: 6 }}>LXCs</div>
                                            <ListItems items={data.lxcs as Array<Record<string, unknown>>} />
                                        </div>
                                    )}
                                    {Array.isArray(data.storage) && data.storage.length > 0 && (
                                        <div>
                                            <div style={{ opacity: 0.85, marginBottom: 6 }}>Storage</div>
                                            <ListItems items={data.storage as Array<Record<string, unknown>>} />
                                        </div>
                                    )}
                                </>
                            )}

                            {!["docker", "hyperv", "linux", "zabbix"].includes(key) && (
                                <pre className="inventory-data" style={{ margin: 0 }}>
                                    {JSON.stringify(data, null, 2)}
                                </pre>
                            )}
                        </div>
                    </div>
                );
            })}
        </div>
    );
}

export default function AgentDetailPage() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const agentId = parseInt(id || "0", 10);

    const [agent, setAgent] = useState<Agent | null>(null);
    const [initialAgent, setInitialAgent] = useState<Agent | null>(null);
    const [commands, setCommands] = useState<AgentCommand[]>([]);
    const [inventory, setInventory] = useState<AgentInventory | null>(null);
    const [activeTab, setActiveTab] = useState<Tab>("overview");
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const [cmdType, setCmdType] = useState("execute");
    const [cmdText, setCmdText] = useState("");
    const [cmdTimeout, setCmdTimeout] = useState(60);
    const [executing, setExecuting] = useState(false);
    const [cmdStatusFilter, setCmdStatusFilter] = useState<string>("all");
    const [expandedCmd, setExpandedCmd] = useState<number | null>(null);
    const [savingPlugins, setSavingPlugins] = useState(false);
    const [draftPlugins, setDraftPlugins] = useState<Set<string>>(new Set());

    const PLUGIN_OPTIONS = [
        { label: "Active Directory", value: "active_directory" },
        { label: "Docker", value: "docker" },
        { label: "Hyper-V", value: "hyperv" },
        { label: "Linux", value: "linux" },
        { label: "Microsoft 365", value: "microsoft_365" },
        { label: "Windows", value: "windows" },
        { label: "Windows Docker", value: "windows_docker" },
        { label: "Zabbix", value: "zabbix" },
    ];

    const enabledSet = (agent?.enabled_plugins || "")
        .split(",")
        .map((p) => p.trim())
        .filter(Boolean);

    useEffect(() => {
        setDraftPlugins((prev) => {
            const next = new Set(enabledSet);
            if (prev.size === 0 && next.size === 0) return next;
            return next;
        });
    }, [agent?.enabled_plugins]);

    const load = async () => {
        try {
            const [a, c] = await Promise.all([
                agentsApi.get(agentId),
                agentsApi.getCommands(agentId),
            ]);
            setAgent(a);
            setInitialAgent((prev) => prev ?? a);
            setCommands(c.items);
        } catch (e) {
            setError(e instanceof Error ? e.message : "Failed to load");
        } finally {
            setLoading(false);
        }
    };

    const loadInventory = async () => {
        try {
            const inv = await agentsApi.getInventory(agentId);
            setInventory(inv);
        } catch (e) {
            setError(e instanceof Error ? e.message : "Failed to load inventory");
        }
    };

    useEffect(() => {
        if (agentId) load();
    }, [agentId]);

    useEffect(() => {
        if (activeTab === "inventory" && !inventory) {
            loadInventory();
        }
    }, [activeTab]);

    const handleToggle = async () => {
        if (!agent) return;
        try {
            if (agent.enabled) {
                await agentsApi.disable(agentId);
            } else {
                await agentsApi.enable(agentId);
            }
            await load();
        } catch (e) {
            setError(e instanceof Error ? e.message : "Toggle failed");
        }
    };

    const handleDelete = async () => {
        if (!window.confirm("Delete this agent? This action cannot be undone.")) return;
        try {
            await agentsApi.remove(agentId);
            navigate("/agents");
        } catch (e) {
            setError(e instanceof Error ? e.message : "Delete failed");
        }
    };

    const handleExecute = async () => {
        if (!cmdText.trim()) return;
        setExecuting(true);
        try {
            await agentsApi.execute(agentId, {
                command_type: cmdType,
                command: cmdText,
                timeout: cmdTimeout,
                requested_by: "dashboard",
            });
            setCmdText("");
            await load();
            setActiveTab("commands");
        } catch (e) {
            setError(e instanceof Error ? e.message : "Execute failed");
        } finally {
            setExecuting(false);
        }
    };

    const filteredCommands = cmdStatusFilter === "all"
        ? commands
        : commands.filter((c) => c.status === cmdStatusFilter);

    const pendingCount = commands.filter((c) => c.status === "pending").length;
    const runningCount = commands.filter((c) => c.status === "running").length;
    const completedCount = commands.filter((c) => c.status === "completed").length;
    const failedCount = commands.filter((c) => c.status === "failed").length;

    if (loading) return <div className="loading-bar" />;
    if (error && !agent) return <div className="error-banner">{error}</div>;
    if (!agent) return <div className="error-banner">Agent not found</div>;

    const inv = inventory?.inventory as Record<string, unknown> | null;

    return (
        <>
            <PageHeader
                title={agent.name}
                subtitle={`${agent.hostname} — ${agent.operating_system || "Unknown OS"} — ${agent.ip_address || "No IP"}`}
                actions={
                    <div className="page-header-actions">
                        <StatusBadge
                            status={agent.status === "online" ? "healthy" : "error"}
                            label={agent.status}
                        />
                        <LoadingButton
                            loading={false}
                            className={`btn btn-sm ${agent.enabled ? "btn-warning" : "btn-primary"}`}
                            onClick={handleToggle}
                        >
                            {agent.enabled ? "Disable" : "Enable"}
                        </LoadingButton>
                        <button className="btn btn-danger btn-sm" onClick={handleDelete}>
                            Delete
                        </button>
                    </div>
                }
            />

            {error && (
                <div className="error-banner">
                    {error}
                    <button className="btn btn-link" onClick={() => setError(null)}>Dismiss</button>
                </div>
            )}

            <div className="agent-detail-tabs">
                {TABS.map((tab) => (
                    <button
                        key={tab.key}
                        className={`tab-btn ${activeTab === tab.key ? "active" : ""}`}
                        onClick={() => setActiveTab(tab.key)}
                    >
                        {tab.icon} {tab.label}
                    </button>
                ))}
            </div>

            {activeTab === "overview" && (
                <div className="agent-overview-grid">
                    <div className="agent-overview-card">
                        <span className="agent-overview-label">Status</span>
                        <StatusBadge
                            status={agent.status === "online" ? "healthy" : "error"}
                            label={agent.status}
                        />
                    </div>
                    <div className="agent-overview-card">
                        <span className="agent-overview-label">Health</span>
                        <StatusBadge
                            status={
                                agent.health === "healthy" ? "healthy"
                                : agent.health === "warning" ? "warning"
                                : "error"
                            }
                            label={agent.health}
                        />
                    </div>
                    <div className="agent-overview-card">
                        <span className="agent-overview-label">Hostname</span>
                        <span className="agent-overview-value mono">{agent.hostname}</span>
                    </div>
                    <div className="agent-overview-card">
                        <span className="agent-overview-label">IP Address</span>
                        <span className="agent-overview-value mono">{agent.ip_address || "—"}</span>
                    </div>
                    <div className="agent-overview-card">
                        <span className="agent-overview-label">Operating System</span>
                        <span className="agent-overview-value">{agent.operating_system || "—"}</span>
                    </div>
                    <div className="agent-overview-card">
                        <span className="agent-overview-label">OS Version</span>
                        <span className="agent-overview-value">{agent.os_version || "—"}</span>
                    </div>
                    <div className="agent-overview-card">
                        <span className="agent-overview-label">Agent Version</span>
                        <span className="agent-overview-value">{agent.agent_version || "—"}</span>
                    </div>
                    <div className="agent-overview-card">
                        <span className="agent-overview-label">Last Heartbeat</span>
                        <span className="agent-overview-value">
                            {agent.last_heartbeat
                                ? formatDateTime(agent.last_heartbeat)
                                : "Never"}
                        </span>
                    </div>
                    <div className="agent-overview-card">
                        <span className="agent-overview-label">Heartbeat Interval</span>
                        <span className="agent-overview-value">{agent.heartbeat_interval}s</span>
                    </div>
                    <div className="agent-overview-card">
                        <span className="agent-overview-label">Registered</span>
                        <span className="agent-overview-value">
                            {agent.registered_at
                                ? formatDateTime(agent.registered_at)
                                : "—"}
                        </span>
                    </div>
                    <div className="agent-overview-card">
                        <span className="agent-overview-label">Tags</span>
                        <span className="agent-overview-value">{agent.tags || "—"}</span>
                    </div>
                    <div className="agent-overview-card">
                        <span className="agent-overview-label">Active Plugins</span>
                        <span className="agent-overview-value">{agent.active_plugins || "None"}</span>
                    </div>
                </div>
            )}

            {activeTab === "performance" && (
                <div>
                    <div className="agent-section-title">Resource Utilization</div>
                    <div className="agent-section-card">
                        <div style={{ display: "flex", flexDirection: "column", gap: 12, maxWidth: 500 }}>
                            <HealthBar label="CPU" value={agent.cpu_percent} />
                            <HealthBar label="Memory" value={agent.memory_percent} />
                            <HealthBar label="Disk" value={agent.disk_percent} />
                        </div>
                    </div>
                    {inv && (
                        <>
                            <div className="agent-section-title">Hardware Information</div>
                            <div className="agent-section-card">
                                <div className="agent-overview-grid">
                                    {typeof inv.cpu_count === "number" && (
                                        <div className="agent-overview-card">
                                            <span className="agent-overview-label">CPU Cores</span>
                                            <span className="agent-overview-value">{String(inv.cpu_count)}</span>
                                        </div>
                                    )}
                                    {typeof inv.memory_total_gb === "number" && (
                                        <div className="agent-overview-card">
                                            <span className="agent-overview-label">Total Memory</span>
                                            <span className="agent-overview-value">{String(inv.memory_total_gb)} GB</span>
                                        </div>
                                    )}
                                    {typeof inv.disk_total_gb === "number" && (
                                        <div className="agent-overview-card">
                                            <span className="agent-overview-label">Total Disk</span>
                                            <span className="agent-overview-value">{String(inv.disk_total_gb)} GB</span>
                                        </div>
                                    )}
                                    {typeof inv.uptime_seconds === "number" && (
                                        <div className="agent-overview-card">
                                            <span className="agent-overview-label">Uptime</span>
                                            <span className="agent-overview-value">
                                                {Math.floor((inv.uptime_seconds as number) / 86400)}d{" "}
                                                {Math.floor(((inv.uptime_seconds as number) % 86400) / 3600)}h
                                            </span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </>
                    )}
                </div>
            )}

            {activeTab === "commands" && (
                <div>
                    <div className="command-center-filters">
                        {["all", "pending", "running", "completed", "failed"].map((s) => (
                            <button
                                key={s}
                                className={`tab-btn ${cmdStatusFilter === s ? "active" : ""}`}
                                onClick={() => setCmdStatusFilter(s)}
                            >
                                {s.charAt(0).toUpperCase() + s.slice(1)}
                                {s === "pending" && pendingCount > 0 && ` (${pendingCount})`}
                                {s === "running" && runningCount > 0 && ` (${runningCount})`}
                                {s === "completed" && completedCount > 0 && ` (${completedCount})`}
                                {s === "failed" && failedCount > 0 && ` (${failedCount})`}
                            </button>
                        ))}
                    </div>

                    {filteredCommands.length === 0 ? (
                        <div className="empty-state">
                            <p>No commands{cmdStatusFilter !== "all" ? ` with status "${cmdStatusFilter}"` : ""}</p>
                        </div>
                    ) : (
                        <div className="data-table-wrapper">
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Type</th>
                                        <th>Command</th>
                                        <th>Status</th>
                                        <th>Exit Code</th>
                                        <th>Duration</th>
                                        <th>Time</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filteredCommands.map((cmd) => (
                                        <>
                                            <tr key={cmd.id}>
                                                <td>{cmd.id}</td>
                                                <td>{cmd.command_type}</td>
                                                <td className="cmd-text">
                                                    {cmd.command.length > 60
                                                        ? cmd.command.substring(0, 60) + "…"
                                                        : cmd.command}
                                                </td>
                                                <td>
                                                    <StatusBadge
                                                        status={
                                                            cmd.status === "completed"
                                                                ? cmd.success ? "healthy" : "error"
                                                                : cmd.status === "failed" ? "error"
                                                                : cmd.status === "running" ? "info"
                                                                : "warning"
                                                        }
                                                        label={cmd.status}
                                                    />
                                                </td>
                                                <td>{cmd.exit_code ?? "—"}</td>
                                                <td>{formatDuration(cmd.duration_ms)}</td>
                                                <td>
                                                    {cmd.created_at
                                                        ? formatDateTime(cmd.created_at)
                                                        : "—"}
                                                </td>
                                                <td>
                                                    <div className="cmd-action-btns">
                                                        {(cmd.stdout || cmd.stderr) && (
                                                            <button
                                                                className="btn btn-sm btn-secondary"
                                                                onClick={() =>
                                                                    setExpandedCmd(expandedCmd === cmd.id ? null : cmd.id)
                                                                }
                                                            >
                                                                {expandedCmd === cmd.id ? "Hide" : "Output"}
                                                            </button>
                                                        )}
                                                    </div>
                                                </td>
                                            </tr>
                                            {expandedCmd === cmd.id && (
                                                <tr key={`${cmd.id}-output`}>
                                                    <td colSpan={8}>
                                                        <div className="cmd-output-expand">
                                                            {cmd.stdout && (
                                                                <div className="cmd-output-text">{cmd.stdout}</div>
                                                            )}
                                                            {cmd.stderr && (
                                                                <div className="cmd-output-text" style={{ borderColor: "rgba(239, 68, 68, 0.3)", color: "var(--danger)" }}>
                                                                    {cmd.stderr}
                                                                </div>
                                                            )}
                                                        </div>
                                                    </td>
                                                </tr>
                                            )}
                                        </>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}

                    <div className="agent-section-title" style={{ marginTop: 24 }}>Execute Command</div>
                    <div className="execute-form">
                        <div className="form-row">
                            <label>Command Type</label>
                            <select value={cmdType} onChange={(e) => setCmdType(e.target.value)}>
                                <option value="execute">Shell Execute</option>
                                <option value="script">Run Script</option>
                            </select>
                        </div>
                        <div className="form-row">
                            <label>Command</label>
                            <textarea
                                value={cmdText}
                                onChange={(e) => setCmdText(e.target.value)}
                                placeholder={cmdType === "execute" ? "Enter command..." : "Enter script..."}
                                rows={4}
                            />
                        </div>
                        <div className="form-row">
                            <label>Timeout (seconds)</label>
                            <input
                                type="number"
                                value={cmdTimeout}
                                onChange={(e) => setCmdTimeout(parseInt(e.target.value) || 60)}
                                min={1}
                                max={3600}
                            />
                        </div>
                        <LoadingButton
                            loading={executing}
                            className="btn btn-primary"
                            onClick={handleExecute}
                        >
                            Execute Command
                        </LoadingButton>
                    </div>
                </div>
            )}

            {activeTab === "inventory" && (
                <div>
                    <div className="agent-section-title">Plugin Inventory</div>
                    {inv ? (
                        <PluginInventory inventory={inv} />
                    ) : (
                        <div className="empty-state">
                            <p>No inventory data available</p>
                        </div>
                    )}
                </div>
            )}

            {activeTab === "diagnostics" && (
                <div>
                    <div className="agent-section-title">Self-Diagnostics</div>
                    <div className="agent-section-card">
                        <div className="empty-text">
                            Diagnostics data will be available when the agent reports self-health checks via heartbeat.
                        </div>
                        <div className="agent-overview-grid" style={{ marginTop: 12 }}>
                            <div className="agent-overview-card">
                                <span className="agent-overview-label">Connectivity</span>
                                <StatusBadge
                                    status={agent.status === "online" ? "healthy" : "error"}
                                    label={agent.status === "online" ? "Connected" : "Disconnected"}
                                />
                            </div>
                            <div className="agent-overview-card">
                                <span className="agent-overview-label">Heartbeat</span>
                                <StatusBadge
                                    status={agent.last_heartbeat ? "healthy" : "error"}
                                    label={agent.last_heartbeat ? "Active" : "No heartbeat"}
                                />
                            </div>
                            <div className="agent-overview-card">
                                <span className="agent-overview-label">Health Score</span>
                                <StatusBadge
                                    status={
                                        agent.health === "healthy" ? "healthy"
                                            : agent.health === "warning" ? "warning"
                                            : "error"
                                    }
                                    label={agent.health}
                                />
                            </div>
                            <div className="agent-overview-card">
                                <span className="agent-overview-label">Enabled</span>
                                <StatusBadge
                                    status={agent.enabled ? "healthy" : "warning"}
                                    label={agent.enabled ? "Yes" : "No"}
                                />
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {activeTab === "configuration" && (
                <div>
                    <div className="agent-section-title">Plugin Configuration</div>
                    <div className="agent-section-card">
                        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                            {PLUGIN_OPTIONS.map((plugin) => {
                                const enabled = draftPlugins.has(plugin.value);
                                return (
                                    <label key={plugin.value} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                        <input
                                            type="checkbox"
                                            checked={enabled}
                                            onChange={(e) => {
                                                setDraftPlugins((prev) => {
                                                    const next = new Set(prev);
                                                    if (e.target.checked) {
                                                        next.add(plugin.value);
                                                    } else {
                                                        next.delete(plugin.value);
                                                    }
                                                    return next;
                                                });
                                            }}
                                        />
                                        <span>{plugin.label}</span>
                                        <span style={{ opacity: 0.7, fontSize: 12 }}>{plugin.value}</span>
                                    </label>
                                );
                            })}
                        </div>
                        <div style={{ marginTop: 12, display: "flex", gap: 10 }}>
                            <LoadingButton
                                loading={savingPlugins}
                                className="btn btn-primary"
                                onClick={async () => {
                                    setSavingPlugins(true);
                                    try {
                                        const updated = await agentsApi.update(agentId, {
                                            enabled_plugins: Array.from(draftPlugins).join(",") || null,
                                        });
                                        setAgent(updated);
                                        setInitialAgent((prev) => prev ?? updated);
                                        setError(null);
                                    } catch (e) {
                                        setError(e instanceof Error ? e.message : "Failed to save plugins");
                                    } finally {
                                        setSavingPlugins(false);
                                    }
                                }}
                            >
                                Save Plugins
                            </LoadingButton>
                            <button
                                className="btn btn-secondary"
                                onClick={() => {
                                    setDraftPlugins(
                                        new Set(
                                            (initialAgent?.enabled_plugins || "")
                                                .split(",")
                                                .map((p) => p.trim())
                                                .filter(Boolean)
                                        )
                                    );
                                }}
                            >
                                Reset
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {activeTab === "remote_targets" && (
                <div>
                    <div className="agent-section-title">Remote Targets</div>
                    <div className="agent-section-card">
                        <AgentRemoteTargetsTab agentId={agentId} />
                    </div>
                </div>
            )}

            {activeTab === "history" && (
                <div>
                    <div className="agent-section-title">State Changes & Events</div>
                    <div className="agent-section-card">
                        {commands.length === 0 ? (
                            <div className="empty-text">No command history</div>
                        ) : (
                            <div className="timeline-list">
                                {commands.slice(0, 50).map((cmd) => (
                                    <div key={cmd.id} className="timeline-item">
                                        <div
                                            className={`timeline-dot ${
                                                cmd.status === "completed"
                                                    ? cmd.success ? "green" : "red"
                                                    : cmd.status === "failed" ? "red"
                                                    : cmd.status === "running" ? "blue"
                                                    : "amber"
                                            }`}
                                        />
                                        <div className="timeline-content">
                                            <div style={{ fontWeight: 600 }}>{cmd.command_type}</div>
                                            <div style={{ fontSize: 13, opacity: 0.85 }}>
                                                {cmd.command.length > 140 ? cmd.command.slice(0, 140) + "…" : cmd.command}
                                            </div>
                                            <div style={{ fontSize: 12, opacity: 0.7 }}>
                                                {cmd.created_at ? formatDateTime(cmd.created_at) : ""}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            )}
        </>
    );
}
