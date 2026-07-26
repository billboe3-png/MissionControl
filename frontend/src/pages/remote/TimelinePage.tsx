import { useState, useEffect, useMemo } from "react";
import PageHeader from "../../components/common/PageHeader";
import SearchInput from "../../components/common/SearchInput";
import StatusBadge from "../../components/common/StatusBadge";
import { apiClient } from "../../utils/apiClient";

interface TimelineEvent {
    id: string;
    type: string;
    message: string;
    timestamp: string;
    severity: string;
    source?: string;
}

const EVENT_TYPE_COLORS: Record<string, string> = {
    registration: "green",
    heartbeat: "green",
    command: "blue",
    automation: "blue",
    plugin: "amber",
    auth: "amber",
    error: "red",
    warning: "amber",
    update: "blue",
};

export default function TimelinePage() {
    const [events, setEvents] = useState<TimelineEvent[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState("");
    const [typeFilter, setTypeFilter] = useState("all");
    const [timeRange, setTimeRange] = useState("24h");

    useEffect(() => {
        const load = async () => {
            try {
                const cmds = await apiClient<{ items: Array<{ id: number; command_type: string; command: string; status: string; created_at: string | null; agent_id: number; success: boolean | null }> }>("/api/v1/agents/commands/all?limit=200");
                const mapped: TimelineEvent[] = (cmds.items ?? []).map((c) => ({
                    id: `cmd-${c.id}`,
                    type: "command",
                    message: `${c.command_type}: ${c.command.length > 80 ? c.command.slice(0, 80) + "..." : c.command}`,
                    timestamp: c.created_at ?? "",
                    severity: c.status === "completed"
                        ? c.success ? "info" : "error"
                        : c.status === "failed" ? "error" : "warning",
                    source: `Agent ${c.agent_id}`,
                }));
                setEvents(mapped.sort((a, b) =>
                    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
                ));
            } catch {
                setEvents([]);
            } finally {
                setLoading(false);
            }
        };
        load();
        const id = setInterval(load, 30000);
        return () => clearInterval(id);
    }, []);

    const filtered = useMemo(() => {
        let list = events;
        if (typeFilter !== "all") {
            list = list.filter((e) => e.type === typeFilter);
        }
        if (search) {
            const q = search.toLowerCase();
            list = list.filter(
                (e) =>
                    e.message.toLowerCase().includes(q) ||
                    (e.source ?? "").toLowerCase().includes(q),
            );
        }
        if (timeRange !== "all") {
            const hours = timeRange === "1h" ? 1 : timeRange === "6h" ? 6 : timeRange === "24h" ? 24 : 168;
            const cutoff = new Date(Date.now() - hours * 3600000);
            list = list.filter((e) => new Date(e.timestamp) >= cutoff);
        }
        return list;
    }, [events, search, typeFilter, timeRange]);

    const types = useMemo(() => {
        const s = new Set(events.map((e) => e.type));
        return Array.from(s).sort();
    }, [events]);

    const handleExport = () => {
        const csv = ["Timestamp,Type,Severity,Source,Message"]
            .concat(
                filtered.map(
                    (e) =>
                        `"${e.timestamp}","${e.type}","${e.severity}","${e.source ?? ""}","${e.message.replace(/"/g, '""')}"`,
                ),
            )
            .join("\n");
        const blob = new Blob([csv], { type: "text/csv" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `timeline-export-${new Date().toISOString().slice(0, 10)}.csv`;
        a.click();
        URL.revokeObjectURL(url);
    };

    return (
        <>
            <PageHeader
                title="Operations Timeline"
                subtitle="Live event stream across all infrastructure"
                actions={
                    <div className="page-header-actions">
                        <button className="btn btn-sm btn-secondary" onClick={handleExport}>
                            Export CSV
                        </button>
                    </div>
                }
            />

            <div className="fleet-toolbar">
                <SearchInput value={search} onChange={setSearch} placeholder="Search events..." />
                <select
                    className="form-input fleet-filter"
                    value={typeFilter}
                    onChange={(e) => setTypeFilter(e.target.value)}
                >
                    <option value="all">All Types</option>
                    {types.map((t) => (
                        <option key={t} value={t}>{t}</option>
                    ))}
                </select>
                <select
                    className="form-input fleet-filter"
                    value={timeRange}
                    onChange={(e) => setTimeRange(e.target.value)}
                >
                    <option value="1h">Last 1 hour</option>
                    <option value="6h">Last 6 hours</option>
                    <option value="24h">Last 24 hours</option>
                    <option value="7d">Last 7 days</option>
                    <option value="all">All time</option>
                </select>
            </div>

            {loading && events.length === 0 ? (
                <div className="loading-bar" />
            ) : filtered.length === 0 ? (
                <div className="empty-state">
                    <p>No events found</p>
                </div>
            ) : (
                <div className="timeline-list">
                    {filtered.map((event) => (
                        <div key={event.id} className="timeline-item">
                            <div
                                className={`timeline-dot ${EVENT_TYPE_COLORS[event.type] ?? "gray"}`}
                            />
                            <div className="timeline-content">
                                <div className="timeline-message">{event.message}</div>
                                <div className="timeline-meta">
                                    <StatusBadge
                                        status={
                                            event.severity === "error" ? "error"
                                            : event.severity === "warning" ? "warning"
                                            : "info"
                                        }
                                        label={event.type}
                                    />
                                    {event.source && <span>{event.source}</span>}
                                </div>
                            </div>
                            <span className="timeline-time">
                                {event.timestamp
                                    ? new Date(event.timestamp).toLocaleString()
                                    : "—"}
                            </span>
                        </div>
                    ))}
                </div>
            )}
        </>
    );
}
