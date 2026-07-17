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

export default function AgentDetailPage() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const agentId = parseInt(id || "0", 10);

    const [agent, setAgent] = useState<Agent | null>(null);
    const [commands, setCommands] = useState<AgentCommand[]>([]);
    const [inventory, setInventory] = useState<AgentInventory | null>(null);
    const [activeTab, setActiveTab] = useState<"overview" | "commands" | "inventory" | "execute">("overview");
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const [cmdType, setCmdType] = useState("execute");
    const [cmdText, setCmdText] = useState("");
    const [cmdTimeout, setCmdTimeout] = useState(60);
    const [executing, setExecuting] = useState(false);

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
        if (!window.confirm("Delete this agent? This action cannot be undone."))
            return;
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

    if (loading) return <div className="loading-bar" />;
    if (error && !agent) return <div className="error-banner">{error}</div>;
    if (!agent) return <div className="error-banner">Agent not found</div>;

    return (
        <>
            <PageHeader
                title={agent.name}
                subtitle={`${agent.hostname} — ${agent.operating_system || "Unknown OS"}`}
                actions={
                    <div className="page-header-actions">
                        <LoadingButton
                            loading={false}
                            className={`btn btn-sm ${agent.enabled ? "btn-warning" : "btn-primary"}`}
                            onClick={handleToggle}
                        >
                            {agent.enabled ? "Disable" : "Enable"}
                        </LoadingButton>
                        <button
                            className="btn btn-danger btn-sm"
                            onClick={handleDelete}
                        >
                            Delete
                        </button>
                    </div>
                }
            />

            {error && (
                <div className="error-banner">
                    {error}
                    <button className="btn btn-link" onClick={() => setError(null)}>
                        Dismiss
                    </button>
                </div>
            )}

            <div className="agent-detail-tabs">
                {(["overview", "commands", "inventory", "execute"] as const).map(
                    (tab) => (
                        <button
                            key={tab}
                            className={`tab-btn ${activeTab === tab ? "active" : ""}`}
                            onClick={() => setActiveTab(tab)}
                        >
                            {tab.charAt(0).toUpperCase() + tab.slice(1)}
                        </button>
                    )
                )}
            </div>

            {activeTab === "overview" && (
                <div className="agent-detail-overview">
                    <div className="detail-grid">
                        <div className="detail-item">
                            <label>Status</label>
                            <StatusBadge
                                status={agent.status === "online" ? "healthy" : "error"}
                                label={agent.status}
                            />
                        </div>
                        <div className="detail-item">
                            <label>Health</label>
                            <StatusBadge
                                status={
                                    agent.health === "healthy"
                                        ? "healthy"
                                        : agent.health === "warning"
                                        ? "warning"
                                        : "error"
                                }
                                label={agent.health}
                            />
                        </div>
                        <div className="detail-item">
                            <label>IP Address</label>
                            <span>{agent.ip_address || "—"}</span>
                        </div>
                        <div className="detail-item">
                            <label>Agent Version</label>
                            <span>{agent.agent_version || "—"}</span>
                        </div>
                        <div className="detail-item">
                            <label>OS</label>
                            <span>{agent.operating_system || "—"}</span>
                        </div>
                        <div className="detail-item">
                            <label>OS Version</label>
                            <span>{agent.os_version || "—"}</span>
                        </div>
                        <div className="detail-item">
                            <label>Last Heartbeat</label>
                            <span>
                                {agent.last_heartbeat
                                    ? new Date(agent.last_heartbeat).toLocaleString()
                                    : "Never"}
                            </span>
                        </div>
                        <div className="detail-item">
                            <label>Heartbeat Interval</label>
                            <span>{agent.heartbeat_interval}s</span>
                        </div>
                        <div className="detail-item">
                            <label>Tags</label>
                            <span>{agent.tags || "—"}</span>
                        </div>
                        <div className="detail-item">
                            <label>Active Plugins</label>
                            <span>{agent.active_plugins || "None"}</span>
                        </div>
                        <div className="detail-item">
                            <label>Registered</label>
                            <span>
                                {agent.registered_at
                                    ? new Date(agent.registered_at).toLocaleString()
                                    : "—"}
                            </span>
                        </div>
                    </div>
                </div>
            )}

            {activeTab === "commands" && (
                <div className="agent-commands-list">
                    {commands.length === 0 ? (
                        <div className="empty-state">
                            <p>No commands executed yet</p>
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
                                    </tr>
                                </thead>
                                <tbody>
                                    {commands.map((cmd) => (
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
                                                            ? cmd.success
                                                                ? "healthy"
                                                                : "error"
                                                            : cmd.status === "failed"
                                                            ? "error"
                                                            : "warning"
                                                    }
                                                    label={cmd.status}
                                                />
                                            </td>
                                            <td>{cmd.exit_code ?? "—"}</td>
                                            <td>
                                                {cmd.duration_ms != null
                                                    ? `${cmd.duration_ms}ms`
                                                    : "—"}
                                            </td>
                                            <td>
                                                {cmd.created_at
                                                    ? new Date(cmd.created_at).toLocaleString()
                                                    : "—"}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}

            {activeTab === "inventory" && (
                <div className="agent-inventory">
                    {inventory?.inventory ? (
                        <pre className="inventory-data">
                            {JSON.stringify(inventory.inventory, null, 2)}
                        </pre>
                    ) : (
                        <div className="empty-state">
                            <p>No inventory data available</p>
                        </div>
                    )}
                </div>
            )}

            {activeTab === "execute" && (
                <div className="agent-execute">
                    <div className="execute-form">
                        <div className="form-row">
                            <label>Command Type</label>
                            <select
                                value={cmdType}
                                onChange={(e) => setCmdType(e.target.value)}
                            >
                                <option value="execute">Shell Execute</option>
                                <option value="script">Run Script</option>
                            </select>
                        </div>
                        <div className="form-row">
                            <label>Command</label>
                            <textarea
                                value={cmdText}
                                onChange={(e) => setCmdText(e.target.value)}
                                placeholder={
                                    cmdType === "execute"
                                        ? "Enter command..."
                                        : "Enter script..."
                                }
                                rows={6}
                            />
                        </div>
                        <div className="form-row">
                            <label>Timeout (seconds)</label>
                            <input
                                type="number"
                                value={cmdTimeout}
                                onChange={(e) =>
                                    setCmdTimeout(parseInt(e.target.value) || 60)
                                }
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
        </>
    );
}
