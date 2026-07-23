import { useEffect, useState } from "react";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import { veeamApi, VeeamSession, VeeamSessionStat } from "../../services/veeam";
import { formatBytes } from "../../services/veeam";

const SKIP_TYPES = new Set(["ConfigurationResynchronize", "MalwareDetection"]);

function sessionStatus(s: VeeamSession): { status: "healthy" | "warning" | "error" | "info"; label: string } {
    if (s.state === "Running" || s.state === "Working") return { status: "info", label: "Running" };
    const r = s.result?.result;
    if (r === "Success") return { status: "healthy", label: "Success" };
    if (r === "Failed") return { status: "error", label: "Failed" };
    if (r === "Warning") return { status: "warning", label: "Warning" };
    return { status: "warning", label: s.state || "Unknown" };
}

function formatDuration(start: string | null, end: string | null): string {
    if (!start) return "-";
    const s = new Date(start).getTime();
    const e = end ? new Date(end).getTime() : Date.now();
    const secs = Math.floor((e - s) / 1000);
    if (secs < 60) return `${secs}s`;
    const mins = Math.floor(secs / 60);
    const rem = secs % 60;
    if (mins < 60) return `${mins}m ${rem}s`;
    const hrs = Math.floor(mins / 60);
    return `${hrs}h ${mins % 60}m`;
}

export default function VeeamSessionsPage() {
    const [allSessions, setAllSessions] = useState<VeeamSession[]>([]);
    const [stats, setStats] = useState<VeeamSessionStat[]>([]);
    const [serverNames, setServerNames] = useState<string[]>([]);
    const [sshAvailable, setSshAvailable] = useState(false);
    const [loading, setLoading] = useState(true);
    const [longLoad, setLongLoad] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [showAll, setShowAll] = useState(false);
    const [selectedServer, setSelectedServer] = useState<string | null>(null);

    useEffect(() => {
        setLoading(true);
        setLongLoad(false);
        const timer = setTimeout(() => setLongLoad(true), 15000);
        Promise.all([
            veeamApi.listSessions(),
            veeamApi.getSessionStats().catch(() => ({ success: false, stats: [], server_names: [] as string[], ssh_available: false, count: 0, message: null, error: null })),
        ])
            .then(([sessions, statsResp]) => {
                setAllSessions(sessions);
                setStats(statsResp.stats ?? []);
                setServerNames(statsResp.server_names ?? []);
                setSshAvailable(statsResp.ssh_available ?? false);
            })
            .catch((e) => setError(e.message))
            .finally(() => { clearTimeout(timer); setLongLoad(false); setLoading(false); });
    }, []);

    const statsMap = new Map(stats.map((s) => [s.session_id, s]));

    if (loading) return (
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "4rem 2rem" }}>
            <div className="loading-bar" style={{ width: "200px", marginBottom: longLoad ? "1.5rem" : 0 }} />
            {longLoad && (
                <div style={{ textAlign: "center", color: "#8b949e", fontSize: "0.85rem", lineHeight: 1.6 }}>
                    <div style={{ marginBottom: "0.5rem" }}>Connecting to Veeam servers for the first time...</div>
                    <div style={{ color: "#6e7681" }}>This takes about 2 minutes while we detect each server&apos;s database engine. Subsequent loads will be fast.</div>
                </div>
            )}
        </div>
    );
    if (error) return <div className="error-banner">{error}</div>;

    const backupSessions = allSessions.filter((s) => !SKIP_TYPES.has(s.sessionType));
    const baseSessions = showAll ? allSessions : backupSessions;

    const uniqueServers = serverNames.length > 0 ? serverNames : [...new Set(baseSessions.map((s) => (s as any).server_name ?? "").filter(Boolean))];
    const hasMultiServer = uniqueServers.length > 1;

    const display = selectedServer
        ? baseSessions.filter((s) => (s as any).server_name === selectedServer)
        : baseSessions;

    return (
        <>
            <PageHeader
                title="Backup Sessions"
                subtitle={`${display.length} sessions across ${hasMultiServer ? uniqueServers.length + " servers" : "1 server"}`}
            />
            {hasMultiServer && (
                <div style={{ marginBottom: "0.75rem", display: "flex", gap: "0.5rem", flexWrap: "wrap", alignItems: "center" }}>
                    <span style={{ fontSize: "0.75rem", color: "#8b949e", marginRight: "0.25rem" }}>Servers:</span>
                    <button
                        onClick={() => setSelectedServer(null)}
                        style={{
                            fontSize: "0.75rem", padding: "0.3rem 0.7rem", borderRadius: "4px", cursor: "pointer", border: "1px solid",
                            borderColor: !selectedServer ? "#58a6ff" : "#30363d",
                            background: !selectedServer ? "#1a3a5c" : "#161b22",
                            color: !selectedServer ? "#b8d4f0" : "#8b949e",
                            fontWeight: !selectedServer ? 600 : 400,
                        }}
                    >
                        All ({baseSessions.length})
                    </button>
                    {uniqueServers.map((srv) => {
                        const count = baseSessions.filter((s) => (s as any).server_name === srv).length;
                        const active = selectedServer === srv;
                        return (
                            <button
                                key={srv}
                                onClick={() => setSelectedServer(active ? null : srv)}
                                style={{
                                    fontSize: "0.75rem", padding: "0.3rem 0.7rem", borderRadius: "4px", cursor: "pointer", border: "1px solid",
                                    borderColor: active ? "#58a6ff" : "#30363d",
                                    background: active ? "#1a3a5c" : "#161b22",
                                    color: active ? "#b8d4f0" : "#8b949e",
                                    fontWeight: active ? 600 : 400,
                                }}
                            >
                                {srv} ({count})
                            </button>
                        );
                    })}
                </div>
            )}
            <div className="veeam-sessions-controls">
                <label className="veeam-sessions-checkbox">
                    <input
                        type="checkbox"
                        checked={showAll}
                        onChange={(e) => setShowAll(e.target.checked)}
                    />
                    Show all session types (including system config sync)
                </label>
                {sshAvailable && (
                    <span className="veeam-ssh-badge">SSH bridge active - transfer data available</span>
                )}
                {!sshAvailable && stats.length === 0 && (
                    <span className="veeam-ssh-badge veeam-ssh-badge-off">SSH bridge not configured - transfer data unavailable</span>
                )}
            </div>
            <table className="data-table">
                <thead>
                    <tr>
                        {hasMultiServer && <th>Server</th>}
                        <th>Name</th>
                        <th>Platform</th>
                        <th>Result</th>
                        <th>Start</th>
                        <th>End</th>
                        <th>Duration</th>
                        {sshAvailable && <th>Processed</th>}
                        {sshAvailable && <th>Read</th>}
                        {sshAvailable && <th>Transferred</th>}
                    </tr>
                </thead>
                <tbody>
                    {display.map((s) => {
                        const st = sessionStatus(s);
                        const ss = statsMap.get(s.id);
                        const srvName = (s as any).server_name;
                        return (
                            <tr key={`${srvName ?? ""}-${s.id}`}>
                                {hasMultiServer && (
                                    <td style={{ fontSize: "0.75rem", color: "#8b949e", maxWidth: 140, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                                        {srvName ?? ""}
                                    </td>
                                )}
                                <td>{s.name}</td>
                                <td>{s.platformName ?? s.sessionType}</td>
                                <td><StatusBadge status={st.status} label={st.label} /></td>
                                <td>{s.creationTime ? new Date(s.creationTime).toLocaleString() : "-"}</td>
                                <td>{s.endTime ? new Date(s.endTime).toLocaleString() : "-"}</td>
                                <td>{formatDuration(s.creationTime, s.endTime)}</td>
                                {sshAvailable && (
                                    <td>{ss ? formatBytes(ss.processed_bytes) : "-"}</td>
                                )}
                                {sshAvailable && (
                                    <td>{ss ? formatBytes(ss.read_bytes) : "-"}</td>
                                )}
                                {sshAvailable && (
                                    <td>{ss ? formatBytes(ss.transferred_bytes) : "-"}</td>
                                )}
                            </tr>
                        );
                    })}
                    {display.length === 0 && (
                        <tr><td colSpan={(hasMultiServer ? 1 : 0) + (sshAvailable ? 9 : 6)} className="empty-state">No sessions found</td></tr>
                    )}
                </tbody>
            </table>
        </>
    );
}
