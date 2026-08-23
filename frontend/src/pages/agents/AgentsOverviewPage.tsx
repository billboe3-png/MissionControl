import { useState, useEffect, useMemo, useCallback } from "react";
import { Link } from "react-router-dom";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import SearchInput from "../../components/common/SearchInput";
import EmptyState from "../../components/common/EmptyState";
import { agentsApi, Agent, downloadAgentBundle } from "../../services/agents";

type SortKey = "name" | "hostname" | "status" | "os" | "version" | "cpu" | "memory" | "disk" | "heartbeat" | "health";
type SortDir = "asc" | "desc";

function formatUptime(dateStr: string | null): string {
    if (!dateStr) return "Never";
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "Just now";
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
}

function formatDateTimeUtc(iso: string | null | undefined): string {
    if (!iso) return "Never";
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso || "Never";
    const pad = (v: number) => `${v}`.padStart(2, "0");
    return `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())} ${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}:${pad(d.getUTCSeconds())} UTC`;
}

function sortAgents(agents: Agent[], key: SortKey, dir: SortDir): Agent[] {
    const sorted = [...agents].sort((a, b) => {
        let va: string | number = "";
        let vb: string | number = "";
        switch (key) {
            case "name": va = a.name; vb = b.name; break;
            case "hostname": va = a.hostname; vb = b.hostname; break;
            case "status": va = a.status; vb = b.status; break;
            case "os": va = a.operating_system ?? ""; vb = b.operating_system ?? ""; break;
            case "version": va = a.agent_version ?? ""; vb = b.agent_version ?? ""; break;
            case "cpu": va = a.cpu_percent ?? -1; vb = b.cpu_percent ?? -1; break;
            case "memory": va = a.memory_percent ?? -1; vb = b.memory_percent ?? -1; break;
            case "disk": va = a.disk_percent ?? -1; vb = b.disk_percent ?? -1; break;
            case "heartbeat": va = a.last_heartbeat ?? ""; vb = b.last_heartbeat ?? ""; break;
            case "health": va = a.health; vb = b.health; break;
        }
        if (typeof va === "string") return dir === "asc" ? va.localeCompare(vb as string) : (vb as string).localeCompare(va);
        return dir === "asc" ? (va as number) - (vb as number) : (vb as number) - (va as number);
    });
    return sorted;
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

export default function AgentsOverviewPage() {
    const [agents, setAgents] = useState<Agent[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [search, setSearch] = useState("");
    const [sortKey, setSortKey] = useState<SortKey>("name");
    const [sortDir, setSortDir] = useState<SortDir>("asc");
    const [statusFilter, setStatusFilter] = useState<string>("all");
    const [selected, setSelected] = useState<Set<number>>(new Set());
    const [downloadSelections, setDownloadSelections] = useState<Record<number, string>>({});
    const [globalDownload, setGlobalDownload] = useState<string>("");
    const [editingAgentId, setEditingAgentId] = useState<number | null>(null);
    const [editingAgentName, setEditingAgentName] = useState<string>("");
    const [updatingAgentId, setUpdatingAgentId] = useState<number | null>(null);
    const [revealedApiKey, setRevealedApiKey] = useState<Record<number, string>>({});
    const [revealingApiKey, setRevealingApiKey] = useState<Record<number, boolean>>({});

    const load = useCallback(async () => {
        try {
            const data = await agentsApi.list();
            setAgents(data.items);
        } catch (e) {
            setError(e instanceof Error ? e.message : "Failed to load");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        load();
        const id = setInterval(load, 15000);
        return () => clearInterval(id);
    }, [load]);

    const handleSort = (key: SortKey) => {
        if (sortKey === key) {
            setSortDir((d) => (d === "asc" ? "desc" : "asc"));
        } else {
            setSortKey(key);
            setSortDir("asc");
        }
    };

    const toggleSelect = (id: number) => {
        setSelected((prev) => {
            const next = new Set(prev);
            if (next.has(id)) next.delete(id);
            else next.add(id);
            return next;
        });
    };

    const toggleSelectAll = () => {
        if (selected.size === filtered.length) {
            setSelected(new Set());
        } else {
            setSelected(new Set(filtered.map((a) => a.id)));
        }
    };

    const handleDownload = async (agentId: number, platform: "linux" | "windows") => {
        setDownloadSelections((prev) => ({ ...prev, [agentId]: platform }));
        try {
            await downloadAgentBundle(agentId, platform);
        } catch (e) {
            alert(e instanceof Error ? e.message : "Download failed");
        } finally {
            setDownloadSelections((prev) => {
                const next = { ...prev };
                delete next[agentId];
                return next;
            });
        }
    };

    const startRename = (agent: Agent) => {
        setEditingAgentId(agent.id);
        setEditingAgentName(agent.name);
    };

    const cancelRename = () => {
        setEditingAgentId(null);
        setEditingAgentName("");
    };

    const saveRename = async (agent: Agent) => {
        const trimmed = editingAgentName.trim();
        if (!trimmed || trimmed === agent.name) {
            cancelRename();
            if (trimmed && trimmed !== agent.name) {
                await load();
            }
            return;
        }
        setUpdatingAgentId(agent.id);
        try {
            const updated = await agentsApi.update(agent.id, { name: trimmed });
            setAgents((prev) => prev.map((a) => (a.id === agent.id ? updated : a)));
        } catch (e) {
            alert(e instanceof Error ? e.message : "Rename failed");
        } finally {
            setUpdatingAgentId(null);
            setEditingAgentId(null);
            setEditingAgentName("");
        }
    };

    const handleRenameKeyDown = (agent: Agent, event: React.KeyboardEvent<HTMLInputElement>) => {
        if (event.key === "Enter") {
            saveRename(agent);
        } else if (event.key === "Escape") {
            cancelRename();
        }
    };

    const handleGlobalDownload = async (platform: "linux" | "windows") => {
        setGlobalDownload(platform);
        try {
            await downloadAgentBundle(0, platform);
        } catch (e) {
            alert(e instanceof Error ? e.message : "Download failed");
        } finally {
            setGlobalDownload("");
        }
    };

    const filtered = useMemo(() => {
        let list = agents;
        if (statusFilter !== "all") {
            list = list.filter((a) => a.status === statusFilter);
        }
        if (search) {
            const q = search.toLowerCase();
            list = list.filter(
                (a) =>
                    a.name.toLowerCase().includes(q) ||
                    a.hostname.toLowerCase().includes(q) ||
                    (a.operating_system ?? "").toLowerCase().includes(q) ||
                    (a.ip_address ?? "").toLowerCase().includes(q),
            );
        }
        return sortAgents(list, sortKey, sortDir);
    }, [agents, search, statusFilter, sortKey, sortDir]);

    const online = agents.filter((a) => a.status === "online").length;
    const offline = agents.filter((a) => a.status === "offline").length;
    const avgCpu = agents.length > 0 ? agents.reduce((s, a) => s + (a.cpu_percent ?? 0), 0) / agents.length : 0;
    const avgMem = agents.length > 0 ? agents.reduce((s, a) => s + (a.memory_percent ?? 0), 0) / agents.length : 0;

    const SortIcon = ({ col }: { col: SortKey }) => {
        if (sortKey !== col) return <span className="fleet-sort-icon">↕</span>;
        return <span className="fleet-sort-icon active">{sortDir === "asc" ? "↑" : "↓"}</span>;
    };

    if (loading && agents.length === 0) return <div className="loading-bar" />;

    return (
        <>
            <PageHeader
                title="Fleet Management"
                subtitle={`Manage ${agents.length} agents across your infrastructure`}
                actions={
                    selected.size > 0 && (
                        <div className="page-header-actions">
                            <span className="refresh-indicator">{selected.size} selected</span>
                        </div>
                    )
                }
            />

            {error && (
                <div className="error-banner">
                    {error}
                    <button className="btn btn-link" onClick={() => setError(null)}>Dismiss</button>
                </div>
            )}

            <div className="fleet-stats-bar">
                <div className="fleet-stat-chip">
                    <span className="fleet-stat-chip-value">{agents.length}</span>
                    <span className="fleet-stat-chip-label">Total</span>
                </div>
                <div className="fleet-stat-chip success">
                    <span className="fleet-stat-chip-value">{online}</span>
                    <span className="fleet-stat-chip-label">Online</span>
                </div>
                <div className="fleet-stat-chip danger">
                    <span className="fleet-stat-chip-value">{offline}</span>
                    <span className="fleet-stat-chip-label">Offline</span>
                </div>
                <div className="fleet-stat-chip">
                    <span className="fleet-stat-chip-value">{avgCpu.toFixed(1)}%</span>
                    <span className="fleet-stat-chip-label">Avg CPU</span>
                </div>
                <div className="fleet-stat-chip">
                    <span className="fleet-stat-chip-value">{avgMem.toFixed(1)}%</span>
                    <span className="fleet-stat-chip-label">Avg Memory</span>
                </div>
            </div>

            <div className="fleet-toolbar">
                <SearchInput value={search} onChange={setSearch} placeholder="Search agents..." />
                <select
                    className="form-input fleet-filter"
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                >
                    <option value="all">All Status</option>
                    <option value="online">Online</option>
                    <option value="offline">Offline</option>
                </select>
            </div>

            <div className="data-table-wrapper" style={{ marginBottom: 12 }}>
                <div style={{ display: "flex", gap: 10, alignItems: "center", justifyContent: "space-between" }}>
                    <div style={{ fontWeight: 600 }}>Agent Bundle Downloads</div>
                    <div style={{ display: "flex", gap: 10 }}>
                        <button className="btn btn-primary" onClick={() => handleGlobalDownload("linux")}>
                            Download Linux bundle
                        </button>
                        <button className="btn btn-primary" onClick={() => handleGlobalDownload("windows")}>
                            Download Windows bundle
                        </button>
                        <Link to="/agents/install" className="btn btn-secondary">
                            Install Agent
                        </Link>
                    </div>
                </div>
                {globalDownload && (
                    <div className="fleet-download-status" style={{ marginTop: 10 }}>
                        Downloading {globalDownload} bundle…
                    </div>
                )}
            </div>

            {filtered.length === 0 && !error ? (
                <EmptyState
                    icon="🤖"
                    title="No agents found"
                    description={search ? "Try adjusting your search or filters." : "Deploy the Mission Control Agent to your systems."}
                />
            ) : (
                <div className="data-table-wrapper">
                    <table className="data-table fleet-table">
                        <thead>
                            <tr>
                                <th className="fleet-th-check">
                                    <input
                                        type="checkbox"
                                        checked={selected.size === filtered.length && filtered.length > 0}
                                        onChange={toggleSelectAll}
                                    />
                                </th>
                                <th className="fleet-th-sortable" onClick={() => handleSort("name")}>
                                    Agent <SortIcon col="name" />
                                </th>
                                <th className="fleet-th-sortable" onClick={() => handleSort("hostname")}>
                                    Hostname <SortIcon col="hostname" />
                                </th>
                                <th className="fleet-th-sortable" onClick={() => handleSort("os")}>
                                    OS <SortIcon col="os" />
                                </th>
                                <th className="fleet-th-sortable" onClick={() => handleSort("version")}>
                                    Version <SortIcon col="version" />
                                </th>
                                <th className="fleet-th-sortable" onClick={() => handleSort("status")}>
                                    Status <SortIcon col="status" />
                                </th>
                                <th className="fleet-th-sortable" onClick={() => handleSort("health")}>
                                    Health <SortIcon col="health" />
                                </th>
                                <th className="fleet-th-sortable" onClick={() => handleSort("cpu")}>
                                    CPU <SortIcon col="cpu" />
                                </th>
                                <th className="fleet-th-sortable" onClick={() => handleSort("memory")}>
                                    Memory <SortIcon col="memory" />
                                </th>
                                <th className="fleet-th-sortable" onClick={() => handleSort("disk")}>
                                    Disk <SortIcon col="disk" />
                                </th>
                                <th className="fleet-th-sortable" onClick={() => handleSort("heartbeat")}>
                                    Last Heartbeat <SortIcon col="heartbeat" />
                                </th>
                                <th>Plugins</th>
                                <th>API Key</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filtered.map((agent) => (
                                <tr
                                    key={agent.id}
                                    className={`fleet-row ${selected.has(agent.id) ? "selected" : ""}`}
                                >
                                    <td>
                                        <input
                                            type="checkbox"
                                            checked={selected.has(agent.id)}
                                            onChange={() => toggleSelect(agent.id)}
                                        />
                                    </td>
                                    <td>
                                        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                            <Link to={`/agents/${agent.id}`} className="fleet-agent-link" style={{ flex: 1, minWidth: 0 }}>
                                                <StatusBadge
                                                    status={agent.status === "online" ? "healthy" : "error"}
                                                    label={agent.status}
                                                />
                                                {editingAgentId === agent.id ? (
                                                    <input
                                                        className="form-input"
                                                        style={{ marginLeft: 8, width: 220 }}
                                                        value={editingAgentName}
                                                        onChange={(e) => setEditingAgentName(e.target.value)}
                                                        onBlur={() => saveRename(agent)}
                                                        onKeyDown={(e) => handleRenameKeyDown(agent, e)}
                                                        autoFocus
                                                        disabled={updatingAgentId === agent.id}
                                                    />
                                                ) : (
                                                    <span className="fleet-agent-name">{agent.name}</span>
                                                )}
                                            </Link>
                                            {editingAgentId !== agent.id && (
                                                <button
                                                    className="btn btn-link"
                                                    style={{ padding: "2px 8px" }}
                                                    onClick={() => startRename(agent)}
                                                    title="Rename agent"
                                                >
                                                    Rename
                                                </button>
                                            )}
                                        </div>
                                    </td>
                                    <td className="mono">{agent.hostname}</td>
                                    <td>{agent.operating_system ?? "—"}</td>
                                    <td className="mono">{agent.agent_version ?? "—"}</td>
                                    <td>
                                        <StatusBadge
                                            status={
                                                agent.status === "online"
                                                    ? "healthy"
                                                    : "error"
                                            }
                                            label={agent.status}
                                        />
                                    </td>
                                    <td>
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
                                    </td>
                                    <td>
                                        {agent.status === "online" ? (
                                            <HealthBar label="" value={agent.cpu_percent} />
                                        ) : "—"}
                                    </td>
                                    <td>
                                        {agent.status === "online" ? (
                                            <HealthBar label="" value={agent.memory_percent} />
                                        ) : "—"}
                                    </td>
                                    <td>
                                        {agent.status === "online" ? (
                                            <HealthBar label="" value={agent.disk_percent} />
                                        ) : "—"}
                                    </td>
                                    <td className="fleet-heartbeat">
                                        {formatUptime(agent.last_heartbeat)}
                                    </td>
                                    <td>{agent.active_plugins ?? "—"}</td>
                                    <td>
                                        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                                            <code className="mono">
                                                {revealedApiKey[agent.id] || agent.api_key_masked || "mc_agent_…"}
                                            </code>
                                            {!revealedApiKey[agent.id] && (
                                                <button
                                                    className="btn btn-link"
                                                    onClick={async () => {
                                                        setRevealingApiKey((prev) => ({ ...prev, [agent.id]: true }));
                                                        try {
                                                            const res = await agentsApi.revealApiKey(agent.id);
                                                            setRevealedApiKey((prev) => ({ ...prev, [agent.id]: res.api_key }));
                                                        } catch (e) {
                                                            alert(e instanceof Error ? e.message : "Failed to load API key");
                                                        } finally {
                                                            setRevealingApiKey((prev) => ({ ...prev, [agent.id]: false }));
                                                        }
                                                    }}
                                                    disabled={revealingApiKey[agent.id]}
                                                >
                                                    {revealingApiKey[agent.id] ? "Loading…" : "Show"}
                                                </button>
                                            )}
                                        </div>
                                    </td>
                                    <td>
                                        <select
                                            className="form-input"
                                            value={downloadSelections[agent.id] ?? ""}
                                            onChange={(e) => {
                                                const value = e.target.value;
                                                if (value === "linux" || value === "windows") {
                                                    handleDownload(agent.id, value);
                                                }
                                            }}
                                        >
                                            <option value="">Download agent…</option>
                                            <option value="linux">Linux bundle</option>
                                            <option value="windows">Windows bundle</option>
                                        </select>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </>
    );
}
