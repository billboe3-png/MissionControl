import { useEffect, useState } from "react";
import { useVeeamServer } from "../../contexts/VeeamServerContext";
import { ServerSelector } from "../../components/veeam/ServerSelector";
import PageHeader from "../../components/common/PageHeader";
import StatusBadge from "../../components/common/StatusBadge";
import {
    veeamApi,
    VeeamSummary,
    VeeamHealth,
    VeeamJob,
    VeeamRepository,
    formatBytes,
} from "../../services/veeam";

function jobState(s: string): { status: "healthy" | "warning" | "error" | "info"; label: string } {
    if (s === "Stopped") return { status: "healthy", label: "Idle" };
    if (s === "Running") return { status: "info", label: "Running" };
    if (s === "Failed") return { status: "error", label: "Failed" };
    return { status: "warning", label: s };
}

function repoStatus(repo: VeeamRepository): string {
    if (repo.status) return repo.status;
    return "Available";
}

export default function VeeamOverviewPage() {
    const [summary, setSummary] = useState<VeeamSummary | null>(null);
    const [health, setHealth] = useState<VeeamHealth | null>(null);
    const [jobs, setJobs] = useState<VeeamJob[]>([]);
    const [repos, setRepos] = useState<VeeamRepository[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const { servers, selectedServerId } = useVeeamServer();

    useEffect(() => {
        // Servers fetched by VeeamServerProvider
    }, [selectedServerId]);

    useEffect(() => {
        if (loading) return;
        Promise.all([
            veeamApi.getSummary(selectedServerId),
            veeamApi.getHealth(selectedServerId),
            veeamApi.listJobs(selectedServerId),
            veeamApi.listRepositories(selectedServerId),
        ])
            .then(([s, h, j, r]) => {
                setSummary(s);
                setHealth(h);
                setJobs(j.jobs);
                setRepos(r);
            })
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, [selectedServerId, loading]);

    const selectedServerName = servers.length > 0 ? servers.find(s => s.id === selectedServerId)?.name : "Veeam Server";

    if (loading) return <div className="loading-bar" />;
    if (error) return <div className="error-banner">{error}</div>;
    if (!summary) return null;

    const storagePercent =
        summary.total_space_bytes > 0
            ? Math.round((summary.used_space_bytes / summary.total_space_bytes) * 100)
            : 0;

    return (
        <>
            <PageHeader
                title="Veeam Backup &amp; Replication"
                subtitle={`${selectedServerName ?? "Veeam Server"} v${summary.version ?? "?"}`}
            />
            {!summary.success && (
                <div className="error-banner">
                    Veeam server not connected: {summary.error ?? "Unknown error"}
                </div>
            )}
            {health && (
                <div className="veeam-connection-status">
                    <StatusBadge
                        status={health.healthy ? "healthy" : "error"}
                        label={health.healthy ? "Connected" : "Error"}
                    />
                    <span>{health.healthy ? "Server reachable" : health.error}</span>
                </div>
            )}
            <div className="dashboard-row">
                <div className="dashboard-card">
                    <div className="dashboard-card-header">Jobs</div>
                    <div className="dashboard-card-value">{summary.total_jobs}</div>
                    <div className="dashboard-card-subtitle">
                        {summary.running_jobs} running
                    </div>
                </div>
                <div className="dashboard-card">
                    <div className="dashboard-card-header">Repositories</div>
                    <div className="dashboard-card-value">{summary.total_repositories}</div>
                    <div className="dashboard-card-subtitle">
                        {formatBytes(summary.used_space_bytes)} / {formatBytes(summary.total_space_bytes)}
                    </div>
                </div>
                <div className="dashboard-card">
                    <div className="dashboard-card-header">Recent Sessions</div>
                    <div className="dashboard-card-value">{summary.recent_sessions}</div>
                    <div className="dashboard-card-subtitle">
                        {summary.sessions_success} success / {summary.sessions_failed} failed
                    </div>
                </div>
            </div>

            {summary.success && (
                <div className="dashboard-section">
                    <h3>Storage Usage</h3>
                    <div className="progress-bar">
                        <div
                            className={`progress-fill ${storagePercent > 90 ? "danger" : storagePercent > 75 ? "warning" : ""}`}
                            style={{ width: `${storagePercent}%` }}
                        />
                        <div className="progress-label">
                            {storagePercent}% — {formatBytes(summary.used_space_bytes)} used of{" "}
                            {formatBytes(summary.total_space_bytes)}
                        </div>
                    </div>
                </div>
            )}

            {jobs.length > 0 && (
                <div className="dashboard-section">
                    <h3>Backup Jobs</h3>
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Type</th>
                                <th>Status</th>
                                <th>Schedule</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {jobs.map((job) => {
                                const st = jobState(job.state);
                                return (
                                    <tr key={job.id}>
                                        <td>{job.name}</td>
                                        <td>{job.type}</td>
                                        <td><StatusBadge status={st.status} label={st.label} /></td>
                                        <td>{job.schedule?.kind ?? "Manual"}</td>
                                        <td>
                                            {job.state !== "Running" && (
                                                <button
                                                    className="btn btn-sm btn-success"
                                                    onClick={() =>
                                                        veeamApi.startJob(job.id, selectedServerId).catch(() => {})
                                                    }
                                                >
                                                    Start
                                                </button>
                                            )}
                                            {job.state === "Running" && (
                                                <button
                                                    className="btn btn-sm btn-danger"
                                                    onClick={() =>
                                                        veeamApi.stopJob(job.id, selectedServerId).catch(() => {})
                                                    }
                                                >
                                                    Stop
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            )}

            {repos.length > 0 && (
                <div className="dashboard-section">
                    <h3>Repositories</h3>
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Type</th>
                                <th>Path</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {repos.map((repo) => {
                                return (
                                    <tr key={repo.id}>
                                        <td>{repo.name}</td>
                                        <td>{repo.type}</td>
                                        <td>{repo.repository?.path ?? "-"}</td>
                                        <td>
                                            <StatusBadge
                                                status={repoStatus(repo) === "Available" ? "healthy" : "warning"}
                                                label={repoStatus(repo)}
                                            />
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            )}
            {servers.length > 1 && <ServerSelector />}
        </>
    );
}
