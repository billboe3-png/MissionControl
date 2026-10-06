import { useCallback, useEffect, useState } from "react";
import { useVeeamServer } from "../../contexts/VeeamServerContext";
import VeeamPageShell from "../../components/veeam/VeeamPageShell";
import { formatBytes } from "../../services/veeam";
import {
    veeamApi,
    VeeamJobDailyRow,
} from "../../services/veeam";

const DAY_PRESETS = [8, 14, 90] as const;
type DayPreset = (typeof DAY_PRESETS)[number];

function dateHeader(d: string): string {
    const [y, m, day] = d.split("-");
    const date = new Date(Date.UTC(Number(y), Number(m) - 1, Number(day)));
    const dow = date.toLocaleDateString("en-US", { weekday: "short" });
    return `${day}/${m} (${dow})`;
}

export default function VeeamJobsPage() {
    const [jobs, setJobs] = useState<VeeamJobDailyRow[]>([]);
    const [days, setDays] = useState<DayPreset>(8);
    const [showSystem, setShowSystem] = useState(false);
    const [dates, setDates] = useState<string[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const { selectedServerId } = useVeeamServer();

    const load = useCallback((refresh: boolean = false) => {
        setLoading(true);
        setError(null);
        veeamApi
            .getJobStatsDaily(days, selectedServerId, showSystem, refresh)
            .then((r) => {
                if (!r.success) {
                    setError(r.error ?? "Failed to load job stats");
                    return;
                }
                setJobs(r.jobs ?? []);
                setDates(r.dates ?? []);
            })
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, [days, showSystem, selectedServerId]);

    useEffect(() => {
        load(false);
    }, [load]);

    return (
        <VeeamPageShell
            title="Veeam Jobs"
            onRefresh={() => load(true)}
            refreshing={loading}
        >
            <div className="jobs-toolbar">
                <label className="jobs-days-label" htmlFor="veeam-job-days">
                    Days
                </label>
                <select
                    id="veeam-job-days"
                    className="jobs-days-select"
                    value={days}
                    onChange={(e) => setDays(Number(e.target.value) as DayPreset)}
                >
                    {DAY_PRESETS.map((d) => (
                        <option key={d} value={d}>
                            {d} days
                        </option>
                    ))}
                </select>
                <label className="jobs-system-label">
                    <input
                        type="checkbox"
                        className="jobs-system-toggle"
                        checked={showSystem}
                        onChange={(e) => setShowSystem(e.target.checked)}
                    />
                    Show system jobs
                </label>
            </div>
            {error && <div className="error-banner">{error}</div>}
            {loading && <div className="loading-bar" />}
            {!error && jobs.length === 0 && !loading && (
                <div className="data-table-empty">No job data available.</div>
            )}
            {!error && jobs.length > 0 && (
                <div className="jobs-matrix-wrapper">
                    <table className="jobs-matrix">
                        <thead>
                            <tr>
                                <th className="jobs-matrix-name">VEEAM TASK</th>
                                <th>Run Time</th>
                                {dates.map((d) => (
                                    <th key={d}>{dateHeader(d)}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {jobs.map((job) => (
                                <tr key={job.job_name}>
                                    <td className="jobs-matrix-name">{job.job_name}</td>
                                    <td></td>
                                    {dates.map((d) => {
                                        const cell = (job.daily || {})[d];
                                        if (!cell) return <td key={d} className="cell-no-data" />;
                                        const runs = cell.runs?.length ? cell.runs : null;
                                        if (runs) {
                                            return (
                                                <td key={d} className="jobs-matrix-cell">
                                                    <div className="jobs-matrix-runs">
                                                        {runs.map((run, i) => {
                                                            let runCls = "cell-run-success";
                                                            if (run.result === "Failed") {
                                                                runCls = "cell-run-failed";
                                                            } else if (run.result === "Warning") {
                                                                runCls = "cell-run-warning";
                                                            }
                                                            const bytes =
                                                                run.transferred_bytes ??
                                                                run.stored_bytes ??
                                                                run.processed_bytes ??
                                                                0;
                                                            return (
                                                                <span key={i} className={`cell-run ${runCls}`}>
                                                                    {formatBytes(bytes)}
                                                                </span>
                                                            );
                                                        })}
                                                    </div>
                                                </td>
                                            );
                                        }
                                        let cls = "cell-success";
                                        let content = formatBytes(
                                            cell.transferred_bytes ?? cell.stored_bytes ?? cell.processed_bytes ?? 0,
                                        );
                                        if (cell.failed_count > 0) {
                                            cls = "cell-failed";
                                            content = "X";
                                        } else if (cell.warning_count > 0) {
                                            cls = "cell-warning";
                                        }
                                        return (
                                            <td key={d} className={`jobs-matrix-cell ${cls}`}>
                                                {content}
                                            </td>
                                        );
                                    })}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </VeeamPageShell>
    );
}
