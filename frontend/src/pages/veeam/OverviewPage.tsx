import { useCallback, useEffect, useState } from "react";
import { useVeeamServer } from "../../contexts/VeeamServerContext";
import VeeamPageShell from "../../components/veeam/VeeamPageShell";
import StatusBadge from "../../components/common/StatusBadge";
import {
    veeamApi,
    VeeamSummary,
    VeeamHealth,
    VeeamJob,
    VeeamRepository,
    VeeamHostBackup,
    VeeamHostBackupStatus,
    formatBytes,
} from "../../services/veeam";

const HOST_WINDOW_DAYS = 3;

function hostBadge(status: VeeamHostBackupStatus): {
    status: "healthy" | "error" | "warning" | "neutral";
    label: string;
} {
    if (status === "passed") return { status: "healthy", label: "Passed" };
    if (status === "failed") return { status: "error", label: "Failed" };
    if (status === "warning") return { status: "warning", label: "Warning" };
    if (status === "error") return { status: "error", label: "Error" };
    return { status: "neutral", label: "No data" };
}

function hostSummaryText(host: VeeamHostBackup): string {
    if (host.error) return host.error;
    if (host.status === "no_data") {
        return `No backups in the last ${host.days} days`;
    }
    if (host.jobs_failed > 0) {
        return `${host.jobs_failed} of ${host.jobs_total} jobs failed (last ${host.days} days)`;
    }
    if (host.jobs_warning > 0) {
        return `${host.jobs_warning} of ${host.jobs_total} jobs warned (last ${host.days} days)`;
    }
    return `All ${host.jobs_total} jobs passed (last ${host.days} days)`;
}

function VeeamHostCard({
    host,
    selected,
    onSelect,
}: {
    host: VeeamHostBackup;
    selected: boolean;
    onSelect: () => void;
}) {
    const badge = hostBadge(host.status);
    return (
        <button
            type="button"
            className={`veeam-host-card status-${host.status}${selected ? " is-selected" : ""}`}
            onClick={onSelect}
            title={host.name}
        >
            <div className="veeam-host-card-header">
                <span className="veeam-host-name">{host.name}</span>
                <StatusBadge status={badge.status} label={badge.label} />
            </div>
            <div className="veeam-host-meta">{hostSummaryText(host)}</div>
            {host.failures.length > 0 && (
                <ul className="veeam-host-reasons">
                    {host.failures.slice(0, 3).map((failure, i) => (
                        <li key={i} className="veeam-host-reason">
                            <span className="veeam-host-reason-job">{failure.job_name}</span>
                            {failure.reason && (
                                <span className="veeam-host-reason-text">{failure.reason}</span>
                            )}
                        </li>
                    ))}
                    {host.failures.length > 3 && (
                        <li className="veeam-host-reason-more">
                            +{host.failures.length - 3} more
                        </li>
                    )}
                </ul>
            )}
        </button>
    );
}

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
    const [hosts, setHosts] = useState<VeeamHostBackup[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [refreshing, setRefreshing] = useState(false);
    const [hostsLoading, setHostsLoading] = useState(false);
    const { selectedServerId, setSelectedServerId } = useVeeamServer();

    const load = useCallback((refresh: boolean = false) => {
        if (refresh) {
            setRefreshing(true);
        } else {
            setLoading(true);
        }
        setError(null);
        Promise.all([
            veeamApi.getSummary(selectedServerId, refresh),
            veeamApi.getHealth(selectedServerId),
            veeamApi.listJobs(selectedServerId, refresh),
            veeamApi.listRepositories(selectedServerId, refresh),
        ])
            .then(([s, h, j, r]) => {
                setSummary(s);
                setHealth(h);
                setJobs(j.jobs);
                setRepos(r);
            })
            .catch((e) => setError(e.message))
            .finally(() => {
                setLoading(false);
                setRefreshing(false);
            });
    }, [selectedServerId]);

    const loadHosts = useCallback((refresh: boolean = false) => {
        setHostsLoading(true);
        veeamApi
            .getHostsStatus(HOST_WINDOW_DAYS, refresh)
            .then((res) => setHosts(res.hosts ?? []))
            .catch(() => setHosts([]))
            .finally(() => setHostsLoading(false));
    }, []);

    useEffect(() => {
        load(false);
    }, [load]);

    useEffect(() => {
        loadHosts(false);
    }, [loadHosts]);

    const storagePercent =
        summary && summary.total_space_bytes > 0
            ? Math.round((summary.used_space_bytes / summary.total_space_bytes) * 100)
            : 0;

    return (
        <VeeamPageShell
            title="Veeam Backup &amp; Replication"
            version={summary?.version ?? "?"}
            onRefresh={() => {
                load(true);
                loadHosts(true);
            }}
            refreshing={loading || refreshing || hostsLoading}
        >
            {error && <div className="error-banner">{error}</div>}
            {loading && <div className="loading-bar" />}
            {summary && !summary.success && (
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
            {(hosts.length > 0 || hostsLoading) && (
                <div className="veeam-hosts-section">
                    <div className="veeam-hosts-heading">
                        <h3>Backup Health (Last {HOST_WINDOW_DAYS} Days)</h3>
                        {hostsLoading && (
                            <span className="refresh-indicator">Loading hosts…</span>
                        )}
                    </div>
                    <div className="veeam-hosts-grid">
                        {hosts.map((host) => (
                            <VeeamHostCard
                                key={host.server_id}
                                host={host}
                                selected={host.server_id === selectedServerId}
                                onSelect={() => setSelectedServerId(host.server_id)}
                            />
                        ))}
                    </div>
                </div>
            )}
            {summary && (
                <>
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
                </>
            )}
        </VeeamPageShell>
    );
}
