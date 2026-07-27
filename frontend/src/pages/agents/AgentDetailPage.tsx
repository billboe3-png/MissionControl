import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import LoadingButton from "../../components/common/LoadingButton";
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
    | "history";

function formatDuration(ms: number | null): string {
    if (ms == null) return "—";
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
}

function HealthBar({ label, value }: { label: string; value: number | null }) {
    const pct = value ?? 0;
    const color = pct > 90 ? "#ef4444" : pct > 70 ? "#f59e0b" : "#22c55e";
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

const TABS: { key: Tab; label: string; icon: string }[] = [
    { key: "overview", label: "Overview", icon: "📋" },
    { key: "performance", label: "Performance", icon: "📊" },
    { key: "commands", label: "Commands", icon: "⚡" },
    { key: "inventory", label: "Inventory", icon: "📦" },
    { key: "diagnostics", label: "Diagnostics", icon: "🔍" },
    { key: "configuration", label: "Configuration", icon: "⚙️" },
    { key: "history", label: "History", icon: "📜" },
];

export default function AgentDetailPage() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const agentId = parseInt(id || "0", 10);

    const [agent, setAgent] = useState<Agent | null>(null);
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

    const load = async () => {
        try {
            const [a, c] = await Promise.all([
                agentsApi.get(agentId),
                agentsApi.getCommands(agentId),
            ]);
            setAgent(a);
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
                                ? new Date(agent.last_heartbeat).toLocaleString()
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
                                ? new Date(agent.registered_at).toLocaleString()
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
                                                        ? new Date(cmd.created_at).toLocaleString()
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
                    <div className="agent-section-title">Inventory Data</div>
                    {inventory?.inventory ? (
                        <div className="agent-section-card">
                            <pre className="inventory-data">
                                {JSON.stringify(inventory.inventory, null, 2)}
                            </pre>
                        </div>
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
                    <div className="agent-section-title">Agent Configuration</div>
                    <div className="agent-section-card">
                        <div className="agent-overview-grid">
                            <div className="agent-overview-card">
                                <span className="agent-overview-label">Heartbeat Interval</span>
                                <span className="agent-overview-value">{agent.heartbeat_interval}s</span>
                            </div>
                            <div className="agent-overview-card">
                                <span className="agent-overview-label">Enabled</span>
                                <span className="agent-overview-value">{agent.enabled ? "Yes" : "No"}</span>
                            </div>
                            <div className="agent-overview-card">
                                <span className="agent-overview-label">Tags</span>
                                <span className="agent-overview-value">{agent.tags || "None"}</span>
                            </div>
                            <div className="agent-overview-card">
                                <span className="agent-overview-label">Notes</span>
                                <span className="agent-overview-value">{agent.notes || "None"}</span>
                            </div>
                        </div>
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
                                            <div className="timeline-message">
                                                <strong>{cmd.command_type}</strong>:{" "}
                                                {cmd.command.length > 80
                                                    ? cmd.command.substring(0, 80) + "…"
                                                    : cmd.command}
                                            </div>
                                            <div className="timeline-meta">
                                                <span>Status: {cmd.status}</span>
                                                {cmd.exit_code != null && <span>Exit: {cmd.exit_code}</span>}
                                                {cmd.duration_ms != null && <span>{formatDuration(cmd.duration_ms)}</span>}
                                            </div>
                                        </div>
                                        <span className="timeline-time">
                                            {cmd.created_at
                                                ? new Date(cmd.created_at).toLocaleString()
                                                : "—"}
                                        </span>
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
