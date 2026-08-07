import { useState, useEffect, useMemo, useCallback } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import SearchInput from "../../components/common/SearchInput";
import { agentsApi, AgentCommand } from "../../services/agents";
import { formatDateTime } from "../../utils/dateFormat";

type StatusFilter = "all" | "pending" | "running" | "completed" | "failed" | "cancelled";

function formatDuration(ms: number | null): string {
    if (ms == null) return "—";
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
}

export default function CommandCenterPage() {
    const [commands, setCommands] = useState<AgentCommand[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState("");
    const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
    const [expandedCmd, setExpandedCmd] = useState<number | null>(null);

    const load = useCallback(async () => {
        try {
            const data = await agentsApi.getAllCommands(200);
            setCommands(data.items);
        } catch {
            setCommands([]);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        load();
        const id = setInterval(load, 10000);
        return () => clearInterval(id);
    }, [load]);

    const filtered = useMemo(() => {
        let list = commands;
        if (statusFilter !== "all") {
            list = list.filter((c) => c.status === statusFilter);
        }
        if (search) {
            const q = search.toLowerCase();
            list = list.filter(
                (c) =>
                    c.command.toLowerCase().includes(q) ||
                    c.command_type.toLowerCase().includes(q) ||
                    String(c.agent_id).includes(q),
            );
        }
        return list;
    }, [commands, search, statusFilter]);

    const counts = useMemo(() => ({
        all: commands.length,
        pending: commands.filter((c) => c.status === "pending").length,
        running: commands.filter((c) => c.status === "running").length,
        completed: commands.filter((c) => c.status === "completed").length,
        failed: commands.filter((c) => c.status === "failed").length,
        cancelled: commands.filter((c) => c.status === "cancelled").length,
    }), [commands]);

    const handleRetry = async (cmd: AgentCommand) => {
        try {
            await agentsApi.execute(cmd.agent_id, {
                command_type: cmd.command_type,
                command: cmd.command,
                timeout: cmd.timeout,
                requested_by: "command-center-retry",
            });
            await load();
        } catch {
            // ignore
        }
    };

    return (
        <>
            <PageHeader
                title="Command Center"
                subtitle="Centralized command workspace"
            />

            <div className="fleet-toolbar">
                <SearchInput value={search} onChange={setSearch} placeholder="Search commands..." />
                <div className="command-center-filters">
                    {(["all", "pending", "running", "completed", "failed", "cancelled"] as StatusFilter[]).map((s) => (
                        <button
                            key={s}
                            className={`tab-btn ${statusFilter === s ? "active" : ""}`}
                            onClick={() => setStatusFilter(s)}
                        >
                            {s.charAt(0).toUpperCase() + s.slice(1)}
                            {counts[s] > 0 && ` (${counts[s]})`}
                        </button>
                    ))}
                </div>
            </div>

            {loading && commands.length === 0 ? (
                <div className="loading-bar" />
            ) : filtered.length === 0 ? (
                <div className="empty-state">
                    <p>No commands found</p>
                </div>
            ) : (
                <div className="data-table-wrapper">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Agent</th>
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
                            {filtered.map((cmd) => (
                                <>
                                    <tr key={cmd.id} className={expandedCmd === cmd.id ? "selected" : ""}>
                                        <td>{cmd.id}</td>
                                        <td>{cmd.agent_id}</td>
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
                                                {cmd.status === "failed" && (
                                                    <button
                                                        className="btn btn-sm btn-primary"
                                                        onClick={() => handleRetry(cmd)}
                                                    >
                                                        Retry
                                                    </button>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                    {expandedCmd === cmd.id && (
                                        <tr key={`${cmd.id}-output`}>
                                            <td colSpan={9}>
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
        </>
    );
}
